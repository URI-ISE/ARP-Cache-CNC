#!/usr/bin/env python3
"""
Cyber-Physical System Defense Mechanisms
Prevention and Detection Modules for G-Code Security
ONR Research - Industrial Control System Protection
"""

import hashlib
import hmac
import json
import time
import numpy as np
from datetime import datetime, timedelta
from collections import deque
from typing import Dict, List, Tuple, Optional
import threading
import re
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2
import os


class DefenseSystem:
    """Comprehensive defense system against G-code attacks"""
    
    def __init__(self):
        self.defense_modules = {
            'authentication': AuthenticationModule(),
            'encryption': EncryptionModule(),
            'anomaly_detection': AnomalyDetectionModule(),
            'integrity': IntegrityVerificationModule(),
            'rate_limiting': RateLimitingModule(),
            'isolation': NetworkIsolationModule(),
            'audit': AuditLoggingModule(),
            'rollback': CommandRollbackModule()
        }
        
        self.active_defenses = set()
        self.defense_stats = {}
        
    def enable_defense(self, defense_type):
        """Enable a specific defense mechanism"""
        if defense_type in self.defense_modules:
            self.active_defenses.add(defense_type)
            return True
        return False
        
    def process_command(self, command, context=None):
        """Process command through active defense layers"""
        defense_results = {}
        
        for defense_name in self.active_defenses:
            module = self.defense_modules[defense_name]
            result = module.process(command, context)
            defense_results[defense_name] = result
            
            # If any defense blocks the command, stop processing
            if not result['allowed']:
                return {
                    'allowed': False,
                    'blocked_by': defense_name,
                    'reason': result.get('reason', 'Security policy violation'),
                    'details': defense_results
                }
                
        return {
            'allowed': True,
            'command': command,
            'defense_results': defense_results
        }


class AuthenticationModule:
    """Command authentication using HMAC"""
    
    def __init__(self):
        self.shared_secret = os.urandom(32)  # In production, use secure key exchange
        self.nonce_cache = deque(maxlen=1000)  # Prevent replay attacks
        self.time_window = 30  # seconds
        
    def generate_authenticated_command(self, command):
        """Generate authenticated G-code command"""
        timestamp = int(time.time())
        nonce = os.urandom(16).hex()
        
        # Create message to sign
        message = f"{command}|{timestamp}|{nonce}".encode()
        
        # Generate HMAC
        h = hmac.new(self.shared_secret, message, hashlib.sha256)
        signature = h.hexdigest()
        
        return {
            'command': command,
            'timestamp': timestamp,
            'nonce': nonce,
            'signature': signature
        }
        
    def verify_command(self, auth_command):
        """Verify authenticated command"""
        try:
            command = auth_command['command']
            timestamp = auth_command['timestamp']
            nonce = auth_command['nonce']
            signature = auth_command['signature']
            
            # Check timestamp freshness
            current_time = int(time.time())
            if abs(current_time - timestamp) > self.time_window:
                return {'allowed': False, 'reason': 'Command expired'}
                
            # Check nonce for replay attack
            if nonce in self.nonce_cache:
                return {'allowed': False, 'reason': 'Replay attack detected'}
                
            # Verify HMAC
            message = f"{command}|{timestamp}|{nonce}".encode()
            h = hmac.new(self.shared_secret, message, hashlib.sha256)
            expected_signature = h.hexdigest()
            
            if not hmac.compare_digest(signature, expected_signature):
                return {'allowed': False, 'reason': 'Invalid signature'}
                
            # Add nonce to cache
            self.nonce_cache.append(nonce)
            
            return {'allowed': True, 'verified': True}
            
        except Exception as e:
            return {'allowed': False, 'reason': f'Verification failed: {e}'}
            
    def process(self, command, context=None):
        """Process command for authentication"""
        # In real implementation, command would come with auth metadata
        if context and 'auth_data' in context:
            return self.verify_command(context['auth_data'])
        
        # For demonstration, generate and verify
        auth_cmd = self.generate_authenticated_command(command)
        return self.verify_command(auth_cmd)


class EncryptionModule:
    """End-to-end encryption for G-code transmission"""
    
    def __init__(self):
        self.key = os.urandom(32)  # AES-256 key
        self.cipher_suite = None
        self.setup_encryption()
        
    def setup_encryption(self):
        """Initialize encryption suite"""
        self.backend = default_backend()
        
    def encrypt_command(self, command):
        """Encrypt G-code command"""
        # Generate IV for this message
        iv = os.urandom(16)
        
        # Create cipher
        cipher = Cipher(
            algorithms.AES(self.key),
            modes.CBC(iv),
            backend=self.backend
        )
        encryptor = cipher.encryptor()
        
        # Pad command to AES block size
        block_size = 16
        padding_length = block_size - (len(command) % block_size)
        padded_command = command.encode() + bytes([padding_length] * padding_length)
        
        # Encrypt
        ciphertext = encryptor.update(padded_command) + encryptor.finalize()
        
        return {
            'iv': iv.hex(),
            'ciphertext': ciphertext.hex()
        }
        
    def decrypt_command(self, encrypted_data):
        """Decrypt G-code command"""
        try:
            iv = bytes.fromhex(encrypted_data['iv'])
            ciphertext = bytes.fromhex(encrypted_data['ciphertext'])
            
            # Create cipher
            cipher = Cipher(
                algorithms.AES(self.key),
                modes.CBC(iv),
                backend=self.backend
            )
            decryptor = cipher.decryptor()
            
            # Decrypt
            padded_plaintext = decryptor.update(ciphertext) + decryptor.finalize()
            
            # Remove padding
            padding_length = padded_plaintext[-1]
            command = padded_plaintext[:-padding_length].decode()
            
            return {'allowed': True, 'command': command}
            
        except Exception as e:
            return {'allowed': False, 'reason': f'Decryption failed: {e}'}
            
    def process(self, command, context=None):
        """Process command encryption/decryption"""
        # Demonstrate encryption and decryption
        encrypted = self.encrypt_command(command)
        decrypted = self.decrypt_command(encrypted)
        
        return {
            'allowed': decrypted['allowed'],
            'encrypted_size': len(encrypted['ciphertext']),
            'encryption_overhead': len(encrypted['ciphertext']) - len(command)
        }


class AnomalyDetectionModule:
    """Machine learning-based anomaly detection"""
    
    def __init__(self):
        self.command_history = deque(maxlen=100)
        self.position_history = deque(maxlen=100)
        self.baseline_stats = {
            'avg_feed_rate': 1500,
            'std_feed_rate': 200,
            'avg_power': 500,
            'std_power': 100,
            'max_acceleration': 100,
            'typical_patterns': []
        }
        
        self.anomaly_threshold = 3.0  # Standard deviations
        self.ml_model = self._initialize_ml_model()
        
    def _initialize_ml_model(self):
        """Initialize simple anomaly detection model"""
        # In production, use proper ML model (isolation forest, LSTM, etc.)
        return {
            'position_predictor': None,  # Would be trained LSTM
            'command_classifier': None,  # Would be trained classifier
            'threshold': 0.8
        }
        
    def extract_features(self, command):
        """Extract features from G-code command"""
        features = {
            'has_g0': 'G0' in command,
            'has_g1': 'G1' in command,
            'has_m3': 'M3' in command,
            'has_m5': 'M5' in command,
            'feed_rate': None,
            'power': None,
            'x_coord': None,
            'y_coord': None,
            'z_coord': None
        }
        
        # Extract numerical values
        feed_match = re.search(r'F(\d+)', command)
        if feed_match:
            features['feed_rate'] = int(feed_match.group(1))
            
        power_match = re.search(r'S(\d+)', command)
        if power_match:
            features['power'] = int(power_match.group(1))
            
        for axis in ['X', 'Y', 'Z']:
            coord_match = re.search(f'{axis}([\\-\\d.]+)', command)
            if coord_match:
                features[f'{axis.lower()}_coord'] = float(coord_match.group(1))
                
        return features
        
    def detect_anomalies(self, command):
        """Detect anomalies in command"""
        features = self.extract_features(command)
        anomalies = []
        
        # Statistical anomaly detection
        if features['feed_rate']:
            z_score = abs((features['feed_rate'] - self.baseline_stats['avg_feed_rate']) / 
                         self.baseline_stats['std_feed_rate'])
            if z_score > self.anomaly_threshold:
                anomalies.append({
                    'type': 'feed_rate_anomaly',
                    'value': features['feed_rate'],
                    'z_score': z_score
                })
                
        if features['power']:
            z_score = abs((features['power'] - self.baseline_stats['avg_power']) / 
                         self.baseline_stats['std_power'])
            if z_score > self.anomaly_threshold:
                anomalies.append({
                    'type': 'power_anomaly',
                    'value': features['power'],
                    'z_score': z_score
                })
                
        # Position prediction anomaly
        if len(self.position_history) > 10:
            last_positions = list(self.position_history)[-10:]
            
            # Simple velocity check (in production, use LSTM prediction)
            if features['x_coord'] is not None:
                velocities = [abs(last_positions[i+1].get('x', 0) - last_positions[i].get('x', 0))
                             for i in range(len(last_positions)-1)]
                avg_velocity = np.mean(velocities) if velocities else 0
                current_velocity = abs(features['x_coord'] - last_positions[-1].get('x', 0))
                
                if avg_velocity > 0 and current_velocity > avg_velocity * 3:
                    anomalies.append({
                        'type': 'position_jump',
                        'axis': 'X',
                        'expected_velocity': avg_velocity,
                        'actual_velocity': current_velocity
                    })
                    
        # Command sequence anomaly
        if len(self.command_history) > 5:
            # Check for unusual command sequences
            recent_commands = list(self.command_history)[-5:]
            
            # Example: M3 (laser on) without G1 (movement) is suspicious
            if features['has_m3'] and not any('G1' in cmd for cmd in recent_commands):
                anomalies.append({
                    'type': 'sequence_anomaly',
                    'description': 'Laser activation without movement'
                })
                
        return anomalies
        
    def update_baseline(self, command):
        """Update baseline statistics with legitimate commands"""
        features = self.extract_features(command)
        
        # Update rolling statistics (simplified)
        if features['feed_rate']:
            # In production, use proper online statistics update
            self.baseline_stats['avg_feed_rate'] = (
                0.95 * self.baseline_stats['avg_feed_rate'] +
                0.05 * features['feed_rate']
            )
            
    def process(self, command, context=None):
        """Process command for anomaly detection"""
        anomalies = self.detect_anomalies(command)
        
        # Add to history
        self.command_history.append(command)
        features = self.extract_features(command)
        self.position_history.append({
            'x': features.get('x_coord'),
            'y': features.get('y_coord'),
            'z': features.get('z_coord')
        })
        
        if anomalies:
            return {
                'allowed': False,
                'reason': 'Anomalies detected',
                'anomalies': anomalies,
                'risk_score': len(anomalies) / 10.0  # Simple risk scoring
            }
            
        # Update baseline if no anomalies
        self.update_baseline(command)
        
        return {
            'allowed': True,
            'anomalies': [],
            'risk_score': 0.0
        }


class IntegrityVerificationModule:
    """Verify command integrity using checksums and digital signatures"""
    
    def __init__(self):
        self.checksum_algorithm = 'sha256'
        self.command_hashes = deque(maxlen=1000)
        
    def calculate_checksum(self, command):
        """Calculate command checksum"""
        h = hashlib.sha256(command.encode())
        return h.hexdigest()
        
    def verify_checksum(self, command, provided_checksum):
        """Verify command checksum"""
        calculated = self.calculate_checksum(command)
        return calculated == provided_checksum
        
    def generate_merkle_tree(self, commands):
        """Generate Merkle tree for batch verification"""
        if not commands:
            return None
            
        # Leaf nodes
        hashes = [self.calculate_checksum(cmd) for cmd in commands]
        
        # Build tree
        while len(hashes) > 1:
            next_level = []
            for i in range(0, len(hashes), 2):
                if i + 1 < len(hashes):
                    combined = hashes[i] + hashes[i + 1]
                else:
                    combined = hashes[i] + hashes[i]
                    
                h = hashlib.sha256(combined.encode())
                next_level.append(h.hexdigest())
                
            hashes = next_level
            
        return hashes[0]  # Root hash
        
    def process(self, command, context=None):
        """Process command for integrity verification"""
        checksum = self.calculate_checksum(command)
        
        # Check for duplicate commands (replay attack)
        if checksum in self.command_hashes:
            return {
                'allowed': False,
                'reason': 'Duplicate command detected (possible replay)',
                'checksum': checksum
            }
            
        self.command_hashes.append(checksum)
        
        # Verify provided checksum if available
        if context and 'checksum' in context:
            if not self.verify_checksum(command, context['checksum']):
                return {
                    'allowed': False,
                    'reason': 'Checksum verification failed',
                    'expected': context['checksum'],
                    'calculated': checksum
                }
                
        return {
            'allowed': True,
            'checksum': checksum,
            'verified': True
        }


class RateLimitingModule:
    """Rate limiting and DDoS protection"""
    
    def __init__(self):
        self.command_buckets = {}  # Per-IP rate limiting
        self.global_rate_limit = 100  # Commands per second
        self.per_ip_rate_limit = 50  # Commands per IP per second
        self.burst_size = 200  # Allow burst traffic
        self.last_reset = time.time()
        
    def check_rate_limit(self, source_ip):
        """Check if request exceeds rate limit"""
        current_time = time.time()
        
        # Reset buckets every second
        if current_time - self.last_reset > 1.0:
            self.command_buckets = {}
            self.last_reset = current_time
            
        # Check per-IP limit
        if source_ip not in self.command_buckets:
            self.command_buckets[source_ip] = 0
            
        self.command_buckets[source_ip] += 1
        
        if self.command_buckets[source_ip] > self.per_ip_rate_limit:
            return False, 'Per-IP rate limit exceeded'
            
        # Check global limit
        total_commands = sum(self.command_buckets.values())
        if total_commands > self.global_rate_limit:
            return False, 'Global rate limit exceeded'
            
        return True, None
        
    def adaptive_rate_limiting(self, metrics):
        """Adjust rate limits based on attack detection"""
        # Increase limits during normal operation
        if metrics.get('attack_detected', False):
            self.per_ip_rate_limit = max(10, self.per_ip_rate_limit // 2)
            self.global_rate_limit = max(20, self.global_rate_limit // 2)
        else:
            self.per_ip_rate_limit = min(100, self.per_ip_rate_limit + 1)
            self.global_rate_limit = min(200, self.global_rate_limit + 2)
            
    def process(self, command, context=None):
        """Process command for rate limiting"""
        source_ip = context.get('source_ip', '0.0.0.0') if context else '0.0.0.0'
        
        allowed, reason = self.check_rate_limit(source_ip)
        
        return {
            'allowed': allowed,
            'reason': reason if not allowed else None,
            'current_rate': self.command_buckets.get(source_ip, 0),
            'limit': self.per_ip_rate_limit
        }


class NetworkIsolationModule:
    """Network segmentation and isolation"""
    
    def __init__(self):
        self.trusted_networks = ['192.168.100.0/24', '10.0.0.0/8']
        self.vlan_config = {
            'control': 100,
            'management': 200,
            'production': 300
        }
        self.firewall_rules = []
        self._initialize_firewall_rules()
        
    def _initialize_firewall_rules(self):
        """Initialize firewall rules"""
        self.firewall_rules = [
            {
                'name': 'Block external G-code',
                'source': '0.0.0.0/0',
                'destination': 'cnc_devices',
                'protocol': 'tcp',
                'port': 80,
                'action': 'deny'
            },
            {
                'name': 'Allow control VLAN',
                'source': 'vlan_100',
                'destination': 'cnc_devices',
                'protocol': 'tcp',
                'port': 80,
                'action': 'allow'
            },
            {
                'name': 'Log all G-code traffic',
                'source': 'any',
                'destination': 'cnc_devices',
                'protocol': 'tcp',
                'port': 80,
                'action': 'log'
            }
        ]
        
    def check_network_access(self, source_ip, destination_ip):
        """Check if network access is allowed"""
        # Simplified check - in production, use proper CIDR matching
        for network in self.trusted_networks:
            if source_ip.startswith(network.split('/')[0].rsplit('.', 1)[0]):
                return True
                
        return False
        
    def get_vlan_from_ip(self, ip_address):
        """Determine VLAN from IP address"""
        # Simplified - in production, query switch/router
        if ip_address.startswith('192.168.100'):
            return self.vlan_config['control']
        elif ip_address.startswith('192.168.200'):
            return self.vlan_config['management']
        else:
            return self.vlan_config['production']
            
    def process(self, command, context=None):
        """Process command for network isolation checks"""
        if not context:
            return {'allowed': True, 'reason': 'No network context'}
            
        source_ip = context.get('source_ip', '')
        destination_ip = context.get('destination_ip', '')
        
        # Check if source is from trusted network
        if not self.check_network_access(source_ip, destination_ip):
            return {
                'allowed': False,
                'reason': 'Source network not trusted',
                'source_ip': source_ip
            }
            
        # Check VLAN isolation
        source_vlan = self.get_vlan_from_ip(source_ip)
        if source_vlan != self.vlan_config['control']:
            return {
                'allowed': False,
                'reason': 'Wrong VLAN for control traffic',
                'source_vlan': source_vlan,
                'required_vlan': self.vlan_config['control']
            }
            
        return {
            'allowed': True,
            'source_vlan': source_vlan,
            'network_trusted': True
        }


class AuditLoggingModule:
    """Comprehensive audit logging for compliance"""
    
    def __init__(self):
        self.audit_log = []
        self.log_retention_days = 90
        self.compliance_standards = ['ISO27001', 'NIST', 'IEC62443']
        
    def log_event(self, event_type, details, severity='INFO'):
        """Log security event"""
        event = {
            'timestamp': datetime.now().isoformat(),
            'event_type': event_type,
            'severity': severity,
            'details': details,
            'compliance_tags': self._get_compliance_tags(event_type)
        }
        
        self.audit_log.append(event)
        
        # In production, write to secure log storage
        return event
        
    def _get_compliance_tags(self, event_type):
        """Get relevant compliance tags for event"""
        tags = []
        
        if 'attack' in event_type.lower():
            tags.extend(['ISO27001-A.12.1', 'NIST-DE.AE-1'])
        if 'auth' in event_type.lower():
            tags.extend(['ISO27001-A.9.2', 'NIST-PR.AC-1'])
        if 'anomaly' in event_type.lower():
            tags.extend(['IEC62443-3-3-SR2.11'])
            
        return tags
        
    def generate_compliance_report(self, standard='ISO27001'):
        """Generate compliance report"""
        relevant_events = [
            event for event in self.audit_log
            if any(standard in tag for tag in event.get('compliance_tags', []))
        ]
        
        return {
            'standard': standard,
            'period': f"Last {self.log_retention_days} days",
            'total_events': len(relevant_events),
            'severity_breakdown': self._count_by_severity(relevant_events),
            'event_types': self._count_by_type(relevant_events)
        }
        
    def _count_by_severity(self, events):
        """Count events by severity"""
        counts = {'CRITICAL': 0, 'HIGH': 0, 'MEDIUM': 0, 'LOW': 0, 'INFO': 0}
        for event in events:
            severity = event.get('severity', 'INFO')
            counts[severity] = counts.get(severity, 0) + 1
        return counts
        
    def _count_by_type(self, events):
        """Count events by type"""
        counts = {}
        for event in events:
            event_type = event.get('event_type', 'unknown')
            counts[event_type] = counts.get(event_type, 0) + 1
        return counts
        
    def process(self, command, context=None):
        """Process command for audit logging"""
        self.log_event(
            event_type='command_processed',
            details={
                'command': command,
                'context': context
            },
            severity='INFO'
        )
        
        return {
            'allowed': True,
            'logged': True,
            'log_size': len(self.audit_log)
        }


class CommandRollbackModule:
    """Emergency rollback and recovery"""
    
    def __init__(self):
        self.command_history = deque(maxlen=1000)
        self.checkpoint_states = {}
        self.rollback_in_progress = False
        
    def save_checkpoint(self, checkpoint_id, state):
        """Save system state checkpoint"""
        self.checkpoint_states[checkpoint_id] = {
            'timestamp': datetime.now(),
            'state': state.copy(),
            'command_count': len(self.command_history)
        }
        
    def rollback_to_checkpoint(self, checkpoint_id):
        """Rollback to saved checkpoint"""
        if checkpoint_id not in self.checkpoint_states:
            return False, 'Checkpoint not found'
            
        checkpoint = self.checkpoint_states[checkpoint_id]
        rollback_commands = []
        
        # Generate inverse commands
        commands_to_reverse = list(self.command_history)[checkpoint['command_count']:]
        
        for cmd in reversed(commands_to_reverse):
            inverse = self._generate_inverse_command(cmd)
            if inverse:
                rollback_commands.append(inverse)
                
        return True, rollback_commands
        
    def _generate_inverse_command(self, command):
        """Generate inverse of G-code command"""
        # Simplified inverse generation
        if 'M3' in command:  # Laser on
            return 'M5'  # Laser off
        elif 'G1' in command or 'G0' in command:
            # Extract coordinates and reverse
            # In production, track actual position
            return command  # Would return move to previous position
        elif 'S' in command:  # Power setting
            return 'S0'  # Set power to 0
            
        return None
        
    def emergency_stop(self):
        """Execute emergency stop sequence"""
        stop_sequence = [
            'M5',      # Laser/spindle off
            'G0 Z10',  # Raise Z to safe height
            'M0',      # Program stop
            'M112'     # Emergency stop
        ]
        
        return stop_sequence
        
    def process(self, command, context=None):
        """Process command for rollback tracking"""
        self.command_history.append(command)
        
        # Check if emergency stop needed
        if context and context.get('emergency_stop', False):
            return {
                'allowed': False,
                'reason': 'Emergency stop triggered',
                'recovery_commands': self.emergency_stop()
            }
            
        return {
            'allowed': True,
            'tracked': True,
            'history_size': len(self.command_history)
        }


def demonstrate_defense_effectiveness():
    """Demonstrate effectiveness of defense mechanisms"""
    
    defense_system = DefenseSystem()
    results = {
        'attacks_blocked': 0,
        'attacks_detected': 0,
        'false_positives': 0,
        'performance_impact': {}
    }
    
    # Test against various attacks
    test_commands = [
        # Normal commands
        ('G1 X10 Y10 F1500', 'normal'),
        ('G1 X20 Y10', 'normal'),
        
        # Attack commands
        ('G1 X1000 Y1000 F9999', 'anomaly'),  # Extreme values
        ('M3 S9999', 'anomaly'),  # Extreme power
        ('G1 X10.1 Y10.1', 'drift'),  # Subtle drift
        ('G1 X10 Y10; rm -rf /', 'injection'),  # Command injection
    ]
    
    # Enable all defenses
    for defense in defense_system.defense_modules.keys():
        defense_system.enable_defense(defense)
    
    print("=" * 60)
    print("Defense System Demonstration")
    print("=" * 60)
    
    for command, attack_type in test_commands:
        start_time = time.time()
        
        result = defense_system.process_command(command)
        
        processing_time = time.time() - start_time
        
        print(f"\nCommand: {command}")
        print(f"Type: {attack_type}")
        print(f"Allowed: {result['allowed']}")
        
        if not result['allowed']:
            print(f"Blocked by: {result.get('blocked_by')}")
            print(f"Reason: {result.get('reason')}")
            
            if attack_type != 'normal':
                results['attacks_blocked'] += 1
            else:
                results['false_positives'] += 1
                
        print(f"Processing time: {processing_time*1000:.2f}ms")
        
    print("\n" + "=" * 60)
    print("Defense Statistics")
    print("=" * 60)
    print(f"Attacks blocked: {results['attacks_blocked']}")
    print(f"False positives: {results['false_positives']}")
    
    return results


if __name__ == "__main__":
    # Run demonstration
    demonstrate_defense_effectiveness()
    
    print("\n" + "=" * 60)
    print("Testing Individual Defense Modules")
    print("=" * 60)
    
    # Test encryption
    print("\n--- Encryption Module Test ---")
    enc_module = EncryptionModule()
    test_cmd = "G1 X50 Y50 F2000"
    encrypted = enc_module.encrypt_command(test_cmd)
    decrypted = enc_module.decrypt_command(encrypted)
    print(f"Original: {test_cmd}")
    print(f"Encrypted size: {len(encrypted['ciphertext'])} bytes")
    print(f"Decrypted: {decrypted.get('command')}")
    
    # Test anomaly detection
    print("\n--- Anomaly Detection Test ---")
    anomaly_module = AnomalyDetectionModule()
    normal_cmd = "G1 X10 Y10 F1500"
    anomaly_cmd = "G1 X10 Y10 F9999"  # Abnormal feed rate
    
    print(f"Normal command: {anomaly_module.process(normal_cmd)['allowed']}")
    print(f"Anomaly command: {anomaly_module.process(anomaly_cmd)['allowed']}")
    
    # Test authentication
    print("\n--- Authentication Module Test ---")
    auth_module = AuthenticationModule()
    auth_data = auth_module.generate_authenticated_command(test_cmd)
    print(f"Command authenticated: {auth_module.verify_command(auth_data)['allowed']}")
    
    # Tamper with signature
    auth_data['signature'] = 'tampered'
    print(f"Tampered command: {auth_module.verify_command(auth_data)['allowed']}")
