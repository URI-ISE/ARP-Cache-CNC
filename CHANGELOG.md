# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2025-11-10

### Added - Initial Release

#### Infrastructure
- Docker-based network topology with three-node architecture
- Docker Compose configuration for reproducible environments
- ARP poisoning infrastructure using dsniff/arpspoof
- Containerized testing platform with proper isolation

#### Attack Modules
- ARP cache poisoning orchestrator
- G-code MITM proxy with real-time command modification
- Attack simulator for GRBL CNC systems
- Multiple attack scenarios:
  - Calibration drift attacks
  - Power reduction attacks
  - Command injection attacks
  - Command suppression

#### Defense Modules
- Authentication module (HMAC-based)
- Encryption module (AES-256)
- Anomaly detection framework
- Integrity verification system
- Rate limiting module
- Network isolation controls
- Audit logging system
- Command rollback capabilities

#### Research Framework
- Experiment orchestration system
- Statistical data logging
- Baseline measurement tools
- Scenario management
- Configuration management

#### Analysis Tools
- Enhanced dashboard with Plotly/Dash
- Data visualization scripts
- Statistical analysis framework
- Report generation tools

#### Documentation
- Comprehensive README.md
- Getting Started guide
- Architecture overview
- API reference structure
- Experiment protocols
- Contributing guidelines

#### Data Management
- Archived experimental data from September 2025
- Baseline measurement storage
- Structured data formats (JSON, CSV)
- Packet capture support (PCAP)

### Project Structure
```
Doom-and-Gloom/
├── infrastructure/        # Docker and network setup
├── scenarios/            # Attack and defense modules
├── data/                 # Experimental data
├── analysis/             # Analysis tools
├── docs/                 # Documentation
├── scripts/              # Utility scripts
└── tests/                # Test suites (planned)
```

### Validated Features
- ✅ ARP poisoning in containerized environment
- ✅ G-code interception and modification
- ✅ Physical GRBL controller integration
- ✅ Real-time command logging
- ✅ Attack success metrics (100% in undefended scenarios)
- ✅ Multiple attack vector demonstrations

### Known Limitations
- Defense mechanisms not yet integrated into live testing
- Dashboard requires manual configuration for different setups
- Limited automated testing coverage
- Hardware testing requires manual safety verification

### Security Considerations
- All testing designed for isolated laboratory environments
- Proper authorization required for hardware testing
- Responsible disclosure practices encouraged
- Safety interlocks recommended for physical testing

---

## [Unreleased]

### Planned for Future Releases

#### Version 1.1.0 (Q1 2026)
- [ ] Integrated defense testing framework
- [ ] Automated experiment orchestration
- [ ] ML-based anomaly detection
- [ ] Enhanced visualization dashboard
- [ ] Comprehensive test suite
- [ ] CI/CD pipeline

#### Version 1.2.0 (Q2 2026)
- [ ] Multi-device testing support
- [ ] Additional CNC protocol support (beyond GRBL)
- [ ] Advanced statistical analysis tools
- [ ] Real-time threat intelligence
- [ ] Performance optimization

#### Version 2.0.0 (Future)
- [ ] Production-ready defense deployment
- [ ] Commercial CNC system integration
- [ ] Scalable architecture for multiple simultaneous experiments
- [ ] Web-based experiment management interface
- [ ] Published research integration

---

## Release Notes Format

Each release includes:
- **Added**: New features
- **Changed**: Changes to existing functionality
- **Deprecated**: Soon-to-be removed features
- **Removed**: Removed features
- **Fixed**: Bug fixes
- **Security**: Security fixes

---

**Maintained by**: Manufacturing Systems Security Research Team  
**Repository**: [GitHub Repository URL]  
**Last Updated**: November 10, 2025
