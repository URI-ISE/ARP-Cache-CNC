"""
Manufacturing Systems Security Framework - Defense Modules

This package contains defense mechanism implementations for protecting
CNC systems against network-based attacks.

Available Modules:
- prevention_modules: Comprehensive defense system with multiple layers

Defense Mechanisms:
- Authentication (HMAC-based)
- Encryption (AES-256)
- Anomaly Detection
- Integrity Verification
- Rate Limiting
- Network Isolation
- Audit Logging
- Command Rollback

Usage:
    from scenarios.defense_modules.prevention_modules import DefenseSystem
    
    defense = DefenseSystem()
    defense.enable_defense('authentication')
    result = defense.process_command(command)
"""

__version__ = '1.0.0'
__author__ = 'Manufacturing Systems Security Research Team'
