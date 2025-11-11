#!/usr/bin/env python3
"""
Industrial Control System Attack Research Scenarios
For ONR Cyber-Physical Systems Security Research
Statistical Analysis and Data Collection Module
"""

import json
import csv
import time
import hashlib
import numpy as np
from datetime import datetime
from pathlib import Path
import sqlite3
import threading
import queue

class ResearchScenarioManager:
    """Manages predefined attack scenarios for research purposes"""
    
    def __init__(self):
        self.scenarios = {
            'calibration_drift': {
                'name': 'Calibration Attack - Progressive Drift',
                'description': 'Simulates sensor calibration tampering leading to progressive accuracy loss',
                'parameters': {
                    'drift_type': 'exponential',
                    'initial_rate': 0.01,  # mm/command
                    'acceleration': 1.001,  # Exponential growth factor
                    'max_drift': 10.0,  # Maximum drift before reset
                    'target_axes': ['x', 'y'],
                    'reset_period': 500  # Commands before drift reset
                },
                'expected_impact': {
                    'detection_difficulty': 'high',
                    'physical_damage': 'low',
                    'quality_impact': 'high',
                    'safety_risk': 'low'
                }
            },
            
            'tolerance_exploitation': {
                'name': 'Tolerance Stack Attack',
                'description': 'Exploits manufacturing tolerances by pushing all dimensions to limits',
                'parameters': {
                    'tolerance_bias': 0.95,  # Push to 95% of tolerance
                    'direction': 'upper',  # upper or lower tolerance
                    'target_features': ['holes', 'edges', 'surfaces'],
                    'accumulation_rate': 0.02  # mm per feature
                },
                'expected_impact': {
                    'detection_difficulty': 'very_high',
                    'physical_damage': 'none',
                    'quality_impact': 'medium',
                    'safety_risk': 'none'
                }
            },
            
            'resonance_attack': {
                'name': 'Mechanical Resonance Exploitation',
                'description': 'Injects frequencies to exploit mechanical resonance',
                'parameters': {
                    'base_frequency': 50,  # Hz
                    'frequency_sweep': [45, 55],  # Range to sweep
                    'amplitude': 0.5,  # mm
                    'injection_rate': 0.1,  # Probability per command
                    'pattern': 'chirp'  # chirp, pulse, or continuous
                },
                'expected_impact': {
                    'detection_difficulty': 'medium',
                    'physical_damage': 'high',
                    'quality_impact': 'high',
                    'safety_risk': 'medium'
                }
            },
            
            'supply_chain_backdoor': {
                'name': 'Supply Chain Trojan',
                'description': 'Hidden modifications activated by specific trigger conditions',
                'parameters': {
                    'trigger_sequence': ['G28', 'G1 X100 Y100', 'M3 S500'],
                    'payload': 'coordinate_shift',
                    'shift_amount': 5.0,  # mm
                    'persistence': 100,  # Commands to maintain attack
                    'stealth_mode': True
                },
                'expected_impact': {
                    'detection_difficulty': 'very_high',
                    'physical_damage': 'medium',
                    'quality_impact': 'high',
                    'safety_risk': 'low'
                }
            },
            
            'timing_channel': {
                'name': 'Covert Timing Channel',
                'description': 'Data exfiltration through command timing modulation',
                'parameters': {
                    'channel_type': 'inter_packet_delay',
                    'bit_encoding': {'0': 100, '1': 200},  # ms delays
                    'data_rate': 10,  # bits/second
                    'cover_traffic': True,
                    'encryption': 'xor'
                },
                'expected_impact': {
                    'detection_difficulty': 'high',
                    'physical_damage': 'none',
                    'quality_impact': 'low',
                    'safety_risk': 'none'
                }
            },
            
            'feedback_loop_manipulation': {
                'name': 'Control Loop Destabilization',
                'description': 'Attacks closed-loop control by manipulating feedback',
                'parameters': {
                    'feedback_delay': 50,  # ms added delay
                    'gain_modification': 1.2,  # Amplify feedback
                    'noise_injection': 0.1,  # Random noise amplitude
                    'phase_shift': 15  # degrees
                },
                'expected_impact': {
                    'detection_difficulty': 'medium',
                    'physical_damage': 'medium',
                    'quality_impact': 'very_high',
                    'safety_risk': 'high'
                }
            },
            
            'economic_sabotage': {
                'name': 'Economic Impact Maximization',
                'description': 'Targets expensive materials or critical production runs',
                'parameters': {
                    'detection_method': 'material_cost_analysis',
                    'threshold': 1000,  # Dollar value trigger
                    'attack_intensity': 'proportional',
                    'subtlety_factor': 0.8,  # Balance between impact and detection
                    'timing': 'peak_production'
                },
                'expected_impact': {
                    'detection_difficulty': 'high',
                    'physical_damage': 'low',
                    'quality_impact': 'very_high',
                    'safety_risk': 'low'
                }
            },
            
            'safety_margin_erosion': {
                'name': 'Progressive Safety Degradation',
                'description': 'Gradually erodes safety margins without triggering alarms',
                'parameters': {
                    'margin_reduction_rate': 0.02,  # 2% per hour
                    'target_parameters': ['speed', 'power', 'acceleration'],
                    'adaptive_threshold': True,  # Learn and avoid detection
                    'recovery_time': 3600  # Seconds to full erosion
                },
                'expected_impact': {
                    'detection_difficulty': 'very_high',
                    'physical_damage': 'high',
                    'quality_impact': 'medium',
                    'safety_risk': 'very_high'
                }
            }
        }
        
        self.active_scenario = None
        self.scenario_state = {}
        
    def activate_scenario(self, scenario_id):
        """Activate a specific research scenario"""
        if scenario_id not in self.scenarios:
            return False
            
        self.active_scenario = scenario_id
        self.scenario_state = {
            'start_time': datetime.now(),
            'command_count': 0,
            'modifications_made': 0,
            'detection_events': 0,
            'accumulated_impact': {}
        }
        
        return self.scenarios[scenario_id]
    
    def get_scenario_modification(self, command, context=None):
        """Get command modification based on active scenario"""
        if not self.active_scenario:
            return command
            
        scenario = self.scenarios[self.active_scenario]
        params = scenario['parameters']
        
        if self.active_scenario == 'calibration_drift':
            return self._apply_calibration_drift(command, params)
        elif self.active_scenario == 'tolerance_exploitation':
            return self._apply_tolerance_exploitation(command, params)
        elif self.active_scenario == 'resonance_attack':
            return self._apply_resonance_attack(command, params)
        elif self.active_scenario == 'supply_chain_backdoor':
            return self._apply_supply_chain_backdoor(command, params, context)
        elif self.active_scenario == 'timing_channel':
            return self._apply_timing_channel(command, params, context)
        elif self.active_scenario == 'feedback_loop_manipulation':
            return self._apply_feedback_manipulation(command, params)
        elif self.active_scenario == 'economic_sabotage':
            return self._apply_economic_sabotage(command, params, context)
        elif self.active_scenario == 'safety_margin_erosion':
            return self._apply_safety_erosion(command, params)
            
        return command
    
    def _apply_calibration_drift(self, command, params):
        """Progressive drift that mimics calibration errors"""
        import re
        
        self.scenario_state['command_count'] += 1
        
        # Calculate current drift amount
        if params['drift_type'] == 'exponential':
            drift = params['initial_rate'] * (params['acceleration'] ** self.scenario_state['command_count'])
            drift = min(drift, params['max_drift'])
        else:
            drift = params['initial_rate'] * self.scenario_state['command_count']
        
        # Reset if period reached
        if self.scenario_state['command_count'] % params['reset_period'] == 0:
            self.scenario_state['command_count'] = 0
            drift = params['initial_rate']
        
        # Apply drift to target axes
        modified = command
        for axis in params['target_axes']:
            pattern = f'{axis.upper()}([\\-\\d.]+)'
            match = re.search(pattern, command)
            if match:
                original = float(match.group(1))
                new_val = original + drift
                modified = re.sub(pattern, f'{axis.upper()}{new_val:.3f}', modified)
                self.scenario_state['modifications_made'] += 1
                
        return modified
    
    def _apply_tolerance_exploitation(self, command, params):
        """Push all dimensions toward tolerance limits"""
        import re
        
        modified = command
        
        # Detect dimension-setting commands
        coord_pattern = r'([XYZ])([\-\d.]+)'
        matches = re.finditer(coord_pattern, command)
        
        for match in matches:
            axis = match.group(1)
            value = float(match.group(2))
            
            # Apply tolerance bias
            if params['direction'] == 'upper':
                new_value = value * (1 + (1 - params['tolerance_bias']))
            else:
                new_value = value * params['tolerance_bias']
                
            modified = modified.replace(
                f'{axis}{value}',
                f'{axis}{new_value:.3f}'
            )
            
        return modified
    
    def _apply_resonance_attack(self, command, params):
        """Inject resonance-inducing patterns"""
        import math
        import random
        
        if random.random() > params['injection_rate']:
            return command
            
        # Calculate resonance frequency at current time
        t = self.scenario_state['command_count'] * 0.01  # Time in seconds
        
        if params['pattern'] == 'chirp':
            # Frequency sweep
            freq_range = params['frequency_sweep'][1] - params['frequency_sweep'][0]
            current_freq = params['frequency_sweep'][0] + (freq_range * (t % 1))
        else:
            current_freq = params['base_frequency']
            
        # Generate oscillation
        oscillation = params['amplitude'] * math.sin(2 * math.pi * current_freq * t)
        
        # Inject into movement commands
        import re
        if 'G1' in command or 'G0' in command:
            # Add oscillation to Y axis (perpendicular to typical X movement)
            y_match = re.search(r'Y([\-\d.]+)', command)
            if y_match:
                y_val = float(y_match.group(1))
                new_y = y_val + oscillation
                command = command.replace(f'Y{y_val}', f'Y{new_y:.3f}')
                
        return command
    
    def _apply_supply_chain_backdoor(self, command, params, context):
        """Hidden backdoor activated by trigger sequence"""
        if not context:
            context = {'history': []}
            
        # Check for trigger sequence
        recent_commands = context.get('history', [])[-len(params['trigger_sequence']):]
        
        if len(recent_commands) == len(params['trigger_sequence']):
            # Simple check - could be made more sophisticated
            trigger_matched = all(
                trig in cmd for trig, cmd in 
                zip(params['trigger_sequence'], recent_commands)
            )
            
            if trigger_matched:
                # Activate payload
                self.scenario_state['backdoor_active'] = params['persistence']
                
        # Apply payload if active
        if self.scenario_state.get('backdoor_active', 0) > 0:
            import re
            
            if params['payload'] == 'coordinate_shift':
                # Shift all coordinates
                for axis in ['X', 'Y']:
                    pattern = f'{axis}([\\-\\d.]+)'
                    match = re.search(pattern, command)
                    if match:
                        val = float(match.group(1))
                        new_val = val + params['shift_amount']
                        command = command.replace(f'{axis}{val}', f'{axis}{new_val:.3f}')
                        
            self.scenario_state['backdoor_active'] -= 1
            
        return command
    
    def _apply_timing_channel(self, command, params, context):
        """Covert channel through timing modulation"""
        # This would need to be implemented at the network level
        # Here we just mark commands for delayed transmission
        
        if context and 'exfil_data' in context:
            bit = context['exfil_data'][context.get('bit_index', 0) % len(context['exfil_data'])]
            delay_ms = params['bit_encoding'][bit]
            
            # Mark command with delay
            command = f"__DELAY:{delay_ms}__|{command}"
            
        return command
    
    def _apply_feedback_manipulation(self, command, params):
        """Manipulate control feedback loops"""
        import re
        import random
        
        # Add noise to position feedback
        if 'G1' in command or 'G0' in command:
            for axis in ['X', 'Y', 'Z']:
                pattern = f'{axis}([\\-\\d.]+)'
                match = re.search(pattern, command)
                if match:
                    val = float(match.group(1))
                    noise = random.uniform(-params['noise_injection'], params['noise_injection'])
                    new_val = val * params['gain_modification'] + noise
                    command = command.replace(f'{axis}{val}', f'{axis}{new_val:.3f}')
                    
        return command
    
    def _apply_economic_sabotage(self, command, params, context):
        """Target high-value operations"""
        if not context:
            return command
            
        # Check if high-value material detected
        material_cost = context.get('material_cost', 0)
        
        if material_cost >= params['threshold']:
            # Intensify attack proportionally
            import re
            
            # Reduce laser power for expensive materials (cause defects)
            if 'S' in command:
                power_match = re.search(r'S(\d+)', command)
                if power_match:
                    power = int(power_match.group(1))
                    # Subtle reduction that causes defects
                    new_power = int(power * params['subtlety_factor'])
                    command = command.replace(f'S{power}', f'S{new_power}')
                    
        return command
    
    def _apply_safety_erosion(self, command, params):
        """Gradually erode safety margins"""
        import re
        
        # Calculate erosion factor based on time
        elapsed = (datetime.now() - self.scenario_state['start_time']).total_seconds()
        erosion_factor = min(elapsed / params['recovery_time'], 1.0)
        reduction = 1.0 - (params['margin_reduction_rate'] * erosion_factor)
        
        # Apply to safety-critical parameters
        if 'F' in command:  # Feed rate
            feed_match = re.search(r'F(\d+)', command)
            if feed_match:
                feed = int(feed_match.group(1))
                # Increase feed rate (reduce safety margin)
                new_feed = int(feed / reduction)
                command = command.replace(f'F{feed}', f'F{new_feed}')
                
        if 'S' in command:  # Spindle/laser power
            power_match = re.search(r'S(\d+)', command)
            if power_match:
                power = int(power_match.group(1))
                # Increase power (reduce safety margin)
                new_power = int(power / reduction)
                command = command.replace(f'S{power}', f'S{new_power}')
                
        return command


class StatisticalDataLogger:
    """Comprehensive data logging for research analysis"""
    
    def __init__(self, db_path='attack_research.db'):
        self.db_path = db_path
        self.log_queue = queue.Queue()
        self.init_database()
        self.start_logging_thread()
        
    def init_database(self):
        """Initialize SQLite database for research data"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Attack events table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS attack_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                scenario_id TEXT,
                attack_type TEXT,
                command_original TEXT,
                command_modified TEXT,
                modification_type TEXT,
                impact_metrics TEXT,
                detection_score REAL,
                session_id TEXT
            )
        ''')
        
        # Network metrics table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS network_metrics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                packet_size INTEGER,
                latency_ms REAL,
                jitter_ms REAL,
                packet_loss_rate REAL,
                throughput_bps REAL,
                session_id TEXT
            )
        ''')
        
        # Physical impact table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS physical_impacts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                position_error_x REAL,
                position_error_y REAL,
                position_error_z REAL,
                surface_quality_score REAL,
                dimensional_accuracy REAL,
                material_waste_grams REAL,
                energy_consumption_joules REAL,
                session_id TEXT
            )
        ''')
        
        # Detection metrics table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS detection_metrics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                detection_method TEXT,
                true_positives INTEGER,
                false_positives INTEGER,
                true_negatives INTEGER,
                false_negatives INTEGER,
                detection_latency_ms REAL,
                confidence_score REAL,
                session_id TEXT
            )
        ''')
        
        # Session metadata table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS sessions (
                session_id TEXT PRIMARY KEY,
                start_time DATETIME,
                end_time DATETIME,
                scenario_id TEXT,
                target_device TEXT,
                network_config TEXT,
                notes TEXT
            )
        ''')
        
        conn.commit()
        conn.close()
        
    def start_logging_thread(self):
        """Start background thread for database writes"""
        def logging_worker():
            while True:
                try:
                    log_entry = self.log_queue.get(timeout=1)
                    if log_entry is None:
                        break
                        
                    self._write_to_database(log_entry)
                    
                except queue.Empty:
                    continue
                except Exception as e:
                    print(f"Logging error: {e}")
                    
        self.logging_thread = threading.Thread(target=logging_worker, daemon=True)
        self.logging_thread.start()
        
    def _write_to_database(self, log_entry):
        """Write log entry to appropriate table"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        table = log_entry.pop('table')
        
        columns = ', '.join(log_entry.keys())
        placeholders = ', '.join(['?' for _ in log_entry])
        query = f"INSERT INTO {table} ({columns}) VALUES ({placeholders})"
        
        cursor.execute(query, list(log_entry.values()))
        conn.commit()
        conn.close()
        
    def log_attack_event(self, scenario_id, attack_type, original_cmd, modified_cmd,
                        modification_type, impact_metrics, detection_score, session_id):
        """Log an attack event for analysis"""
        self.log_queue.put({
            'table': 'attack_events',
            'scenario_id': scenario_id,
            'attack_type': attack_type,
            'command_original': original_cmd,
            'command_modified': modified_cmd,
            'modification_type': modification_type,
            'impact_metrics': json.dumps(impact_metrics),
            'detection_score': detection_score,
            'session_id': session_id
        })
        
    def log_network_metrics(self, packet_size, latency, jitter, loss_rate, 
                           throughput, session_id):
        """Log network performance metrics"""
        self.log_queue.put({
            'table': 'network_metrics',
            'packet_size': packet_size,
            'latency_ms': latency,
            'jitter_ms': jitter,
            'packet_loss_rate': loss_rate,
            'throughput_bps': throughput,
            'session_id': session_id
        })
        
    def log_physical_impact(self, position_errors, quality_score, accuracy,
                          waste, energy, session_id):
        """Log physical/manufacturing impacts"""
        self.log_queue.put({
            'table': 'physical_impacts',
            'position_error_x': position_errors['x'],
            'position_error_y': position_errors['y'],
            'position_error_z': position_errors['z'],
            'surface_quality_score': quality_score,
            'dimensional_accuracy': accuracy,
            'material_waste_grams': waste,
            'energy_consumption_joules': energy,
            'session_id': session_id
        })
        
    def log_detection_metrics(self, method, tp, fp, tn, fn, latency, 
                            confidence, session_id):
        """Log detection system performance"""
        self.log_queue.put({
            'table': 'detection_metrics',
            'detection_method': method,
            'true_positives': tp,
            'false_positives': fp,
            'true_negatives': tn,
            'false_negatives': fn,
            'detection_latency_ms': latency,
            'confidence_score': confidence,
            'session_id': session_id
        })
        
    def create_session(self, scenario_id, target_device, network_config, notes=''):
        """Create new research session"""
        session_id = hashlib.sha256(
            f"{datetime.now().isoformat()}{scenario_id}".encode()
        ).hexdigest()[:16]
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO sessions (session_id, start_time, scenario_id, 
                                target_device, network_config, notes)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (session_id, datetime.now(), scenario_id, target_device, 
             json.dumps(network_config), notes))
        
        conn.commit()
        conn.close()
        
        return session_id
        
    def end_session(self, session_id):
        """Mark session as ended"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE sessions SET end_time = ? WHERE session_id = ?
        ''', (datetime.now(), session_id))
        
        conn.commit()
        conn.close()
        
    def export_session_data(self, session_id, output_format='csv'):
        """Export session data for analysis"""
        conn = sqlite3.connect(self.db_path)
        
        tables = ['attack_events', 'network_metrics', 'physical_impacts', 
                 'detection_metrics']
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        for table in tables:
            query = f"SELECT * FROM {table} WHERE session_id = ?"
            
            if output_format == 'csv':
                df = pd.read_sql_query(query, conn, params=(session_id,))
                filename = f"{table}_{session_id}_{timestamp}.csv"
                df.to_csv(filename, index=False)
                
            elif output_format == 'json':
                cursor = conn.cursor()
                cursor.execute(query, (session_id,))
                columns = [description[0] for description in cursor.description]
                rows = cursor.fetchall()
                
                data = [dict(zip(columns, row)) for row in rows]
                filename = f"{table}_{session_id}_{timestamp}.json"
                
                with open(filename, 'w') as f:
                    json.dump(data, f, indent=2, default=str)
                    
        conn.close()
        
        return f"Exported session {session_id} to {output_format} files"
        
    def get_statistics(self, session_id=None):
        """Generate statistical summary for research"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        where_clause = f"WHERE session_id = '{session_id}'" if session_id else ""
        
        stats = {}
        
        # Attack event statistics
        cursor.execute(f'''
            SELECT 
                COUNT(*) as total_attacks,
                COUNT(DISTINCT attack_type) as unique_attack_types,
                AVG(detection_score) as avg_detection_score
            FROM attack_events {where_clause}
        ''')
        stats['attacks'] = dict(zip(
            ['total', 'unique_types', 'avg_detection_score'],
            cursor.fetchone()
        ))
        
        # Network performance statistics
        cursor.execute(f'''
            SELECT 
                AVG(latency_ms) as avg_latency,
                MAX(latency_ms) as max_latency,
                AVG(packet_loss_rate) as avg_loss_rate,
                AVG(throughput_bps) as avg_throughput
            FROM network_metrics {where_clause}
        ''')
        stats['network'] = dict(zip(
            ['avg_latency', 'max_latency', 'avg_loss_rate', 'avg_throughput'],
            cursor.fetchone()
        ))
        
        # Physical impact statistics
        cursor.execute(f'''
            SELECT 
                AVG(position_error_x) as avg_error_x,
                AVG(position_error_y) as avg_error_y,
                AVG(position_error_z) as avg_error_z,
                AVG(surface_quality_score) as avg_quality,
                SUM(material_waste_grams) as total_waste,
                SUM(energy_consumption_joules) as total_energy
            FROM physical_impacts {where_clause}
        ''')
        stats['physical'] = dict(zip(
            ['avg_error_x', 'avg_error_y', 'avg_error_z', 'avg_quality', 
             'total_waste', 'total_energy'],
            cursor.fetchone()
        ))
        
        # Detection performance (if data exists)
        cursor.execute(f'''
            SELECT 
                SUM(true_positives) as tp,
                SUM(false_positives) as fp,
                SUM(true_negatives) as tn,
                SUM(false_negatives) as fn,
                AVG(detection_latency_ms) as avg_latency
            FROM detection_metrics {where_clause}
        ''')
        detection_data = cursor.fetchone()
        
        if detection_data[0]:  # If we have detection data
            tp, fp, tn, fn = detection_data[:4]
            
            precision = tp / (tp + fp) if (tp + fp) > 0 else 0
            recall = tp / (tp + fn) if (tp + fn) > 0 else 0
            f1_score = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0
            
            stats['detection'] = {
                'precision': precision,
                'recall': recall,
                'f1_score': f1_score,
                'avg_latency': detection_data[4]
            }
        
        conn.close()
        
        return stats


# Pandas import for data export (optional)
try:
    import pandas as pd
except ImportError:
    pd = None
    print("Warning: pandas not installed. CSV export will use basic method.")

if __name__ == "__main__":
    # Example usage for testing
    scenario_manager = ResearchScenarioManager()
    data_logger = StatisticalDataLogger()
    
    # Create research session
    session_id = data_logger.create_session(
        scenario_id='calibration_drift',
        target_device='Test CNC',
        network_config={'subnet': '192.168.0.0/24', 'vlan': 100},
        notes='Testing calibration drift attack scenario'
    )
    
    print(f"Started research session: {session_id}")
    
    # Activate scenario
    scenario = scenario_manager.activate_scenario('calibration_drift')
    print(f"Activated scenario: {scenario['name']}")
    
    # Simulate some commands
    test_commands = [
        'G1 X10 Y10 F1500',
        'G1 X20 Y10',
        'G1 X20 Y20',
        'G1 X10 Y20'
    ]
    
    for cmd in test_commands:
        modified = scenario_manager.get_scenario_modification(cmd)
        
        # Log the attack event
        data_logger.log_attack_event(
            scenario_id='calibration_drift',
            attack_type='position_drift',
            original_cmd=cmd,
            modified_cmd=modified,
            modification_type='coordinate_shift',
            impact_metrics={'drift_amount': 0.1},
            detection_score=0.3,
            session_id=session_id
        )
        
        print(f"Original: {cmd}")
        print(f"Modified: {modified}")
        print()
    
    # Get statistics
    stats = data_logger.get_statistics(session_id)
    print(f"Session statistics: {json.dumps(stats, indent=2)}")
    
    # End session
    data_logger.end_session(session_id)
    print(f"Session {session_id} ended")
