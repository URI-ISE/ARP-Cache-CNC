# ARP-Cache-CNC: CNC Security Research Dashboard

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![Docker](https://img.shields.io/badge/docker-required-blue.svg)](https://www.docker.com/)
[![CI](https://github.com/uri-ise/ARP-Cache-CNC/workflows/CI/badge.svg)](https://github.com/uri-ise/ARP-Cache-CNC/actions)

## Overview

Advanced network interception and attack modification platform for CNC machine security research. Combines ARP cache poisoning, G-code manipulation, and real-time IPTables control with an interactive Dash UI.

**⚠️ Research Use Only**: Authorized security testing on isolated networks.

## Features

- **Real-time Network Interception**: IPTables-based traffic redirection with ARP poisoning
- **G-Code Attack Vectors**: Axis swap, calibration drift, power reduction, Y-injection, home override
- **Interactive Dashboards**: Plotly Dash UI with 3D visualization + Flask API
- **Docker Support**: NET_ADMIN capability for IPTables control
- **Attack Analytics**: Success rates, timing analysis, firmware response tracking

## Quick Start

### WSL2 (Development)
```bash
cd /mnt/c/Users/lukep/Documents/Doom-and-Gloom
source .venv/bin/activate
cd analysis/frontend
python3 arp_loader.py
```

**Access:**
- Dash UI: http://localhost:5000/dash/
- Flask Dashboard: http://localhost:5000/
- API: http://localhost:5000/api/status

### Docker (Local)
```bash
# Build and run locally
docker-compose up -d
docker-compose logs -f dashboard
```

### GitHub Container Registry (Production)
```bash
# Pull from GHCR
docker pull ghcr.io/uri-ise/ARP-Cache-CNC:latest

# Run from GHCR
docker run -d \
  -p 5000:5000 \
  --cap-add=NET_ADMIN \
  -v $(pwd)/logs:/app/logs \
  ghcr.io/uri-ise/ARP-Cache-CNC:latest
```

See [SETUP.md](SETUP.md) for detailed installation and [CONTAINER.md](docs/CONTAINER.md) for container deployment options.

## Architecture

```
Browser → Flask+SocketIO (Port 5000) → IPTables → CNC (192.168.0.170:8080)
            ├─ Dash UI (/dash/)
            ├─ API (/api/*)
            └─ Attack Logic + Logging
```

## Project Structure

```
ARP-Cache-CNC/
├── analysis/
│   ├── dashboard_enhanced.py      # Flask server + IPTables control
│   └── frontend/
│       ├── arp_loader.py          # Dash UI loader
│       └── simple_dash.py         # Minimal UI
├── infrastructure/
│   ├── arp-labsetup/              # ARP lab setup & documentation
│   └── docker/                    # Container configs
├── scenarios/
│   ├── research_scenarios.py      # Attack research framework
│   ├── prevention_modules.py      # Defense mechanisms
│   ├── research_framework.py      # Experiment framework
│   ├── attack_simulator.py        # G-code attack simulator
│   └── other_modules/             # Additional attack tools
├── tests/
│   ├── test_basics.py            # Unit tests
│   └── smoke_test.py             # Integration tests
├── docs/
│   ├── CONTAINER.md              # Container deployment guide
│   ├── EXPERIMENT.md             # Research experiment framework
│   └── EXPERIMENT_REPORT.md      # Sample results
├── docker-compose.yml
├── Dockerfile                     # GHCR-optimized image
├── pyproject.toml
├── requirements.txt
└── .github/workflows/
    ├── ci.yml                     # Test pipeline
    └── container.yml              # GHCR build pipeline
```

## API Endpoints

- `GET /api/status` - System status & statistics
- `POST /api/iptables/setup` - Enable traffic interception
- `POST /api/iptables/disable` - Disable interception
- `POST /api/connect` - Connect to CNC
- `POST /api/send_command` - Send G-code command
- `POST /api/attack_config` - Configure attack parameters

See [REFERENCE.md](REFERENCE.md) for complete API documentation.

## Testing

```bash
# Run endpoint tests
python3 tests/smoke_test.py

# Docker infrastructure test
cd infrastructure/docker
docker-compose up -d
docker ps  # Verify 3 containers running
```

## Safety & Ethics

⚠️ **Research Use Only** - Authorized testing on isolated networks required.

1. Never deploy on production systems
2. Use isolated test networks
3. Implement safety interlocks for hardware
4. Follow IRB guidelines
5. Comply with applicable laws

## Contributing

Research collaborators, graduate students, and industry partners welcome. See [CONTRIBUTING.md](CONTRIBUTING.md) for contribution guidelines and development setup.

## License

MIT License - See [LICENSE](LICENSE) for details.

## Documentation

- [SETUP.md](SETUP.md) - Installation, Docker, deployment
- [CONTRIBUTING.md](CONTRIBUTING.md) - Development guidelines
- [CONTAINER.md](docs/CONTAINER.md) - Docker & GHCR deployment options
- [EXPERIMENT.md](docs/EXPERIMENT.md) - Research experiment framework
- [REFERENCE.md](REFERENCE.md) - Commands, API, troubleshooting

## Citation

```bibtex
@software{arp_cache_cnc,
  title={ARP-Cache-CNC: CNC Security Research Dashboard},
  author={University of Rhode Island, Industrial Systems Engineering},
  year={2025},
  url={https://github.com/uri-ise/ARP-Cache-CNC}
}
```
- **Organization**: University of Rhode Island, Industrial Systems Engineering
- **Primary Investigator**: [Your Name]
- **Email**: [Your Email]

## Related Projects

- [SEED Labs - ARP Cache Poisoning](https://seedsecuritylabs.org/)
- [GRBL Project](https://github.com/gnea/grbl)
- [Industrial Control System Security](https://ics-cert.us-cert.gov/)

---

**Version**: 1.0.0  
**Last Updated**: November 10, 2025  
**Status**: Active Research
