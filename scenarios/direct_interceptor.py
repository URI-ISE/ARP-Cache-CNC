#!/usr/bin/env python3
"""
Direct G-Code Interceptor - Monitors and modifies G-code traffic
Without needing to be in the middle
Save as: direct_interceptor.py
Run as: sudo python3 direct_interceptor.py
"""

import socket
import threading
import time
import sys
import os
from datetime import datetime
from scapy.all import *

class DirectGCodeMonitor:
    """Monitor G-code traffic directly on the network"""
    
    def __init__(self, cnc_ip="192.168.0.170", cnc_port=8080):
        self.cnc_ip = cnc_ip
        self.cnc_port = cnc_port
        self.controller_ip = "192.168.0.221"
        self.running = False
        self.packet_count = 0
        self.gcode_commands = []
        
    def start_passive_monitoring(self):
        """Just watch the traffic between controller and CNC"""
        print(f"[+] Starting passive monitoring")
        print(f"[+] Watching: {self.controller_ip} <-> {self.cnc_ip}:{self.cnc_port}")
        print("[*] This will show all G-code traffic")
        print("-" * 60)
        
        def packet_callback(packet):
            # Check if it's between our devices
            if IP in packet:
                # Traffic TO the CNC
                if packet[IP].dst == self.cnc_ip and TCP in packet:
                    if packet[TCP].dport == self.cnc_port:
                        if packet[TCP].payload:
                            try:
                                data = bytes(packet[TCP].payload).decode('utf-8', errors='ignore')
                                if data.strip():
                                    timestamp = datetime.now().strftime("%H:%M:%S")
                                    print(f"[{timestamp}] CONTROLLER->CNC: {data.strip()[:100]}")
                                    self.gcode_commands.append(data.strip())
                                    self.packet_count += 1
                            except:
                                pass
                
                # Traffic FROM the CNC
                elif packet[IP].src == self.cnc_ip and TCP in packet:
                    if packet[TCP].sport == self.cnc_port:
                        if packet[TCP].payload:
                            try:
                                data = bytes(packet[TCP].payload).decode('utf-8', errors='ignore')
                                if data.strip() and data.strip() != 'ok':
                                    timestamp = datetime.now().strftime("%H:%M:%S")
                                    print(f"[{timestamp}] CNC->CONTROLLER: {data.strip()[:100]}")
                            except:
                                pass
        
        # Start sniffing
        print("[*] Sniffing packets... (Ctrl+C to stop)")
        print("[*] Send some G-code commands from your controller to see them here")
        try:
            sniff(filter=f"host {self.cnc_ip}", prn=packet_callback, store=0)
        except KeyboardInterrupt:
            print(f"\n[*] Stopped. Captured {self.packet_count} G-code packets")
            if self.gcode_commands:
                print("\n[*] Recent G-code commands:")
                for cmd in self.gcode_commands[-10:]:
                    print(f"    {cmd}")
    
    def test_direct_connection(self):
        """Test sending commands directly to CNC"""
        print(f"\n[+] Testing direct connection to CNC at {self.cnc_ip}:{self.cnc_port}")
        
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(5)
            sock.connect((self.cnc_ip, self.cnc_port))
            
            # Send status query
            sock.send(b"?\n")
            response = sock.recv(1024).decode('utf-8', errors='ignore')
            print(f"[+] CNC Status: {response.strip()}")
            
            # Interactive mode
            print("\n[*] Interactive mode - type G-code commands (or 'quit' to exit):")
            print("    Example: G1 X10 Y10 F1000")
            
            while True:
                cmd = input("gcode> ").strip()
                if cmd.lower() == 'quit':
                    break
                    
                if cmd:
                    sock.send((cmd + "\n").encode())
                    response = sock.recv(1024).decode('utf-8', errors='ignore')
                    print(f"Response: {response.strip()}")
            
            sock.close()
            
        except Exception as e:
            print(f"[!] Connection error: {e}")

def main():
    print("="*60)
    print("Direct G-Code Monitor - No Proxy Required")
    print("="*60)
    
    # Check root
    if os.geteuid() != 0:
        print("[!] ERROR: Must run as root for packet capture")
        print("    Run: sudo python3 direct_interceptor.py")
        sys.exit(1)
    
    monitor = DirectGCodeMonitor(cnc_ip="192.168.0.170", cnc_port=8080)
    
    print("\nOptions:")
    print("1. Passive monitoring (watch traffic)")
    print("2. Test direct connection (send commands)")
    print("3. Both")
    
    choice = input("\nSelect option [1]: ").strip() or "1"
    
    if choice == "1":
        monitor.start_passive_monitoring()
    elif choice == "2":
        monitor.test_direct_connection()
    elif choice == "3":
        # Test connection first
        monitor.test_direct_connection()
        # Then monitor
        monitor.start_passive_monitoring()

if __name__ == "__main__":
    main()
