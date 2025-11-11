# Manufacturing Systems Security: ARP-Based Attack Framework for CNC Network Analysis

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![Docker Required](https://img.shields.io/badge/docker-required-blue.svg)](https://www.docker.com/)

## Overview

This repository contains a comprehensive research framework for analyzing security vulnerabilities in industrial manufacturing systems, specifically focusing on Computer Numerical Control (CNC) machines using the GRBL protocol. The framework employs Address Resolution Protocol (ARP) cache poisoning as a mechanism to enable Man-in-the-Middle (MITM) attacks on G-code command streams.

**Academic Context**: This research platform is designed for academic investigation of cyber-physical system vulnerabilities in manufacturing environments, with potential applications in developing defensive security mechanisms for industrial control systems.

## Research Objectives

1. **Network-Layer Attack Infrastructure**: Establish reproducible ARP cache poisoning environment using containerized network topology
2. **G-Code Manipulation Analysis**: Investigate the impact of command-stream attacks on CNC machining operations
3. **Defense Mechanism Development**: Design and test countermeasures for manufacturing system security
4. **Statistical Validation**: Provide rigorous data collection and analysis framework for security research

## Key Features

### Current Implementation
- ✅ **ARP Poisoning Infrastructure**: Docker-based network environment with three-node topology (HostA, HostB, Attacker)
- ✅ **G-Code Attack Scenarios**: Multiple attack vectors including calibration drift, power reduction, and command injection
- ✅ **GRBL Proxy Implementation**: Man-in-the-middle proxy with real-time command modification capabilities
- ✅ **Data Collection Framework**: Comprehensive logging and statistical analysis tools
- ✅ **Hardware Testing Support**: Direct integration with physical GRBL controllers

### Planned Development
- 🔄 Defense mechanism implementation and evaluation
- 🔄 Machine learning-based anomaly detection
- 🔄 Automated experiment orchestration
- 🔄 Real-time visualization dashboard

## Project Structure

```
Doom-and-Gloom/
├── infrastructure/          # Network and environment setup
│   ├── docker/             # Docker Compose configurations
│   └── volumes/            # Shared volumes for containers
├── scenarios/              # Attack and defense implementations
│   ├── attack_modules/     # G-code attack scenarios
│   └── defense_modules/    # Security countermeasures
├── data/                   # Experimental data and results
│   ├── archived_experiments/  # Historical experiment data
│   └── baseline/           # Baseline measurements
├── analysis/               # Data analysis and visualization tools
├── docs/                   # Documentation and research notes
├── scripts/                # Utility scripts
└── tests/                  # Test suites
```

## Prerequisites

### Required Software
- **Docker**: Version 20.10 or higher with Docker Compose v2
- **Python**: Version 3.8 or higher
- **Git**: For version control and collaboration

### Required Hardware (for physical testing)
- GRBL-compatible CNC controller
- Network-accessible machine interface
- Dedicated testing network (isolated from production)

### System Requirements
- **OS**: Linux (Ubuntu 20.04+ recommended) or macOS
- **RAM**: Minimum 4GB, 8GB recommended
- **Network**: Ability to run Docker with custom networking

## Quick Start

See [GETTING_STARTED.md](docs/GETTING_STARTED.md) for detailed setup instructions.

### Basic Setup

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd Doom-and-Gloom
   ```

2. **Start the ARP poisoning infrastructure**
   ```bash
   cd infrastructure/docker
   docker-compose up -d
   ```

3. **Verify container status**
   ```bash
   docker ps
   ```

4. **Access the attacker container**
   ```bash
   docker exec -it M-10.9.0.105 /bin/bash
   ```

## Research Methodology

### Phase 1: Infrastructure Setup
Establish the containerized network environment with three hosts:
- **HostA (10.9.0.5)**: Simulated legitimate controller
- **HostB (10.9.0.6)**: Simulated CNC machine endpoint
- **HostM (10.9.0.105)**: Attacker/researcher node with ARP poisoning capabilities

### Phase 2: Baseline Measurement
Collect baseline performance metrics without attack interference:
- Network latency and throughput
- Command processing time
- Position accuracy

### Phase 3: Attack Scenario Execution
Implement and test various G-code attack vectors:
- Calibration drift attacks
- Power/speed modification
- Command injection
- Command suppression

### Phase 4: Defense Evaluation
Test and validate defense mechanisms:
- Command authentication (HMAC)
- Anomaly detection
- Rate limiting
- Network segmentation

### Phase 5: Statistical Analysis
Analyze experimental results using statistical methods:
- Attack success rates
- Detection rates
- Performance impact analysis
- Risk assessment

## Documentation

- **[Getting Started Guide](docs/GETTING_STARTED.md)**: Detailed setup and configuration
- **[Architecture Overview](docs/ARCHITECTURE.md)**: System design and components
- **[API Reference](docs/API_REFERENCE.md)**: Module and function documentation
- **[Experiment Guide](docs/EXPERIMENTS.md)**: How to design and run experiments
- **[Publications](docs/PUBLICATIONS.md)**: Related academic papers and presentations

## Safety and Ethics

⚠️ **IMPORTANT SAFETY NOTICE** ⚠️

This framework is designed for **RESEARCH PURPOSES ONLY** in controlled laboratory environments. Users must:

1. **Never deploy on production systems** without explicit authorization
2. **Use isolated test networks** separate from operational networks
3. **Implement proper safety interlocks** when testing with physical hardware
4. **Follow institutional review board (IRB)** guidelines if applicable
5. **Comply with all applicable laws** and regulations regarding network security research

The authors assume no liability for misuse of this software.

## Contributing

This is an academic research project. Contributions are welcome from:
- Research collaborators
- Graduate students in related fields
- Industry partners interested in manufacturing security

Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## Citation

If you use this framework in your research, please cite:

```bibtex
@software{manufacturing_security_framework,
  title={Manufacturing Systems Security: ARP-Based Attack Framework for CNC Network Analysis},
  author={[Your Name]},
  year={2025},
  url={https://github.com/[your-username]/Doom-and-Gloom}
}
```

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- Office of Naval Research (ONR) for research support
- SEED Labs project for Docker container base images
- Open-source GRBL community

## Contact

For research inquiries, collaborations, or questions:
- **Primary Investigator**: [Your Name]
- **Email**: [Your Email]
- **Institution**: [Your Institution]

## Related Projects

- [SEED Labs - ARP Cache Poisoning](https://seedsecuritylabs.org/)
- [GRBL Project](https://github.com/gnea/grbl)
- [Industrial Control System Security](https://ics-cert.us-cert.gov/)

---

**Version**: 1.0.0  
**Last Updated**: November 10, 2025  
**Status**: Active Research
