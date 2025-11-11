"""
Manufacturing Systems Security Framework - Attack Modules

This package contains attack scenario implementations for testing
CNC system vulnerabilities through ARP poisoning and G-code manipulation.

Available Modules:
- arp_attack_orchestrator: ARP cache poisoning orchestration
- attack_simulator: Basic G-code attack simulations
- attack_simulator_advanced: Advanced attack scenarios
- gcode_proxy: MITM proxy for G-code interception

Usage:
    from scenarios.attack_modules import GCodeAttackSimulator
    
    simulator = GCodeAttackSimulator('192.168.0.170', 8080)
    simulator.connect()
    simulator.simulate_calibration_drift()
"""

__version__ = '1.0.0'
__author__ = 'Manufacturing Systems Security Research Team'
