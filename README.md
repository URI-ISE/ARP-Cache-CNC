# Doom-and-Gloom: CNC Security Research Dashboard

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![Docker](https://img.shields.io/badge/docker-required-blue.svg)](https://www.docker.com/)

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

### Docker (Production)
```bash
docker-compose up -d
docker-compose logs -f
```

See [SETUP.md](SETUP.md) for detailed installation.

## Architecture

```
Browser → Flask+SocketIO (Port 5000) → IPTables → CNC (192.168.0.170:8080)
            ├─ Dash UI (/dash/)
            ├─ API (/api/*)
            └─ Attack Logic + Logging
```

## Project Structure

```
Doom-and-Gloom/
├── analysis/
│   ├── dashboard_enhanced.py      # Flask server + IPTables control
│   └── frontend/
│       ├── arp_loader.py          # Dash UI loader
│       └── simple_dash.py         # Minimal UI
├── infrastructure/docker/         # Container configs
├── scenarios/attack_modules/      # G-code attacks
├── tests/smoke_test.py           # Endpoint validation
├── docker-compose.yml
└── requirements.txt
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

Research collaborators, graduate students, and industry partners welcome. See [SETUP.md](SETUP.md) for contribution guidelines.

## License

MIT License - See [LICENSE](LICENSE) for details.

## Documentation

- [SETUP.md](SETUP.md) - Installation, Docker, deployment
- [REFERENCE.md](REFERENCE.md) - Commands, API, troubleshooting

## Citation

```bibtex
@software{doom_and_gloom,
  title={Doom-and-Gloom: CNC Security Research Dashboard},
  author={Research Team},
  year={2025},
  url={https://github.com/lpep64/Doom-and-Gloom}
}
```
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
