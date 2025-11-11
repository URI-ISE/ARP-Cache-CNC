# Setup & Deployment Guide

Complete installation, configuration, and deployment instructions for Doom-and-Gloom.

## Prerequisites

### Required Software
- **Docker Desktop** (Windows/Mac) or Docker Engine (Linux) - Version 20.10+
- **Docker Compose** - v2.0+
- **Python** - 3.8 or higher
- **Git** - Latest version

### System Requirements
- **OS**: Windows 10/11 with WSL2, Linux (Ubuntu 20.04+), or macOS
- **RAM**: 8GB minimum, 16GB recommended
- **Disk**: 10GB free space
- **Network**: Isolated test network for CNC testing

### Hardware (Optional - for Physical Testing)
- GRBL-compatible CNC controller
- Network-accessible machine (Ethernet)
- Isolated testing network (no production systems)

---

## Installation

### 1. Windows with WSL2 (Recommended for Development)

**Install WSL2:**
```powershell
# In PowerShell (Admin)
wsl --install
wsl --set-default-version 2
```

**Install Docker Desktop:**
1. Download from https://www.docker.com/products/docker-desktop/
2. Enable WSL2 backend during installation
3. Settings → Resources → WSL Integration → Enable your distro

**Clone Repository:**
```bash
# In WSL terminal
cd /mnt/c/Users/YourUsername/Documents
git clone https://github.com/lpep64/Doom-and-Gloom.git
cd Doom-and-Gloom
```

**Setup Python Environment:**
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 2. Linux (Ubuntu/Debian)

```bash
# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER
newgrp docker

# Install Docker Compose
sudo apt install docker-compose-plugin

# Clone and setup
git clone https://github.com/lpep64/Doom-and-Gloom.git
cd Doom-and-Gloom
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 3. macOS

```bash
# Install Docker Desktop from website
# Or use Homebrew:
brew install --cask docker

# Clone and setup
git clone https://github.com/lpep64/Doom-and-Gloom.git
cd Doom-and-Gloom
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

---

## Configuration

### Network Settings

Edit `analysis/dashboard_enhanced.py` or use API/UI:

```python
network_config = {
    'cnc_ip': '192.168.0.170',     # Target CNC machine IP
    'cnc_port': 8080,               # CNC port (GRBL default)
    'proxy_port': 8888,             # Interception proxy port
    'interface': 'eth0'             # Network interface
}
```

### Attack Parameters

Configure via `/api/attack_config` or Dash UI:
- **Axis Swap**: Swap X/Y coordinates
- **Calibration Drift**: Gradual position offset (rate, max drift)
- **Power Reduction**: Reduce spindle/feed (reduction factor)
- **Y-Injection**: Add offset to Y-axis (injection amount)
- **Home Override**: Replace homing command

---

## Running the Dashboard

### Option 1: Development Mode (WSL2)

```bash
cd /mnt/c/Users/YourUsername/Documents/Doom-and-Gloom
source .venv/bin/activate
cd analysis/frontend
python3 arp_loader.py
```

**Access:**
- Dash ARP UI: http://localhost:5000/dash/
- Flask Dashboard: http://localhost:5000/
- API: http://localhost:5000/api/status

**Stop:** `Ctrl+C` or `pkill -f arp_loader.py`

### Option 2: Docker (Production)

**Start:**
```bash
cd Doom-and-Gloom
docker-compose up -d
```

**Monitor:**
```bash
docker-compose logs -f dashboard
```

**Stop:**
```bash
docker-compose down
```

**Access:** Same URLs as development mode.

### Option 3: Docker with ARP Infrastructure

**For full ARP attack environment:**
```bash
cd infrastructure/docker
docker-compose up -d

# Access containers
docker exec -it A-10.9.0.5 /bin/bash      # HostA (victim)
docker exec -it B-10.9.0.6 /bin/bash      # HostB (target)
docker exec -it M-10.9.0.105 /bin/bash    # HostM (attacker)
```

---

## IPTables Setup

### Enable Interception (via API)

```bash
curl -X POST http://localhost:5000/api/iptables/setup \
  -H "Content-Type: application/json" \
  -d '{
    "interface": "eth0",
    "cnc_ip": "192.168.0.170",
    "proxy_port": 8888
  }'
```

### Check Status

```bash
curl http://localhost:5000/api/iptables/status
```

### Disable

```bash
curl -X POST http://localhost:5000/api/iptables/disable
```

### Docker Permissions

IPTables requires `NET_ADMIN` capability. Verify `docker-compose.yml`:

```yaml
services:
  dashboard:
    cap_add:
      - NET_ADMIN
      - NET_RAW
    network_mode: host
```

**Manual verification inside container:**
```bash
docker exec -it doom-gloom-dashboard bash
iptables -L -n  # Should work without permission errors
```

---

## Testing

### Smoke Tests

```bash
source .venv/bin/activate
python3 tests/smoke_test.py
```

**Expected output:**
```
✓ GET http://localhost:5000/ - Status 200
✓ GET http://localhost:5000/api/status - Status 200
✓ GET http://localhost:5000/dash/ - Status 200
Results: 8 passed, 0 failed
```

### Docker Infrastructure Test

```bash
cd infrastructure/docker
docker-compose up -d
docker ps  # Should show 3 containers
docker-compose logs
```

### End-to-End Test

1. Start dashboard
2. Open http://localhost:5000/dash/
3. Configure network settings
4. Enable IPTables
5. Connect to CNC (or simulator)
6. Enable attack
7. Send test G-code
8. Verify attack statistics update

---

## Troubleshooting

### Port Already in Use

```bash
# Find process
lsof -i :5000  # Linux/Mac
netstat -ano | findstr :5000  # Windows

# Kill process
pkill -f arp_loader.py
pkill -f dashboard_enhanced.py
```

### Template Not Found Error

Already fixed in latest version. If you see this:
```bash
# Verify template_folder is set in dashboard_enhanced.py
grep -A2 "Flask(__name__" analysis/dashboard_enhanced.py
```

### Docker Permission Denied

```bash
# Linux - add user to docker group
sudo usermod -aG docker $USER
newgrp docker

# Test
docker run hello-world
```

### IPTables Operation Not Permitted

**Solution:** Run with Docker (NET_ADMIN capability) or use sudo:
```bash
sudo python3 analysis/frontend/arp_loader.py
```

### Module Not Found

```bash
source .venv/bin/activate
pip install -r requirements.txt
pip list | grep flask  # Verify installation
```

### Dash UI Not Loading

1. Verify URL is `/dash/` not `/`
2. Check server logs for errors
3. Test endpoint: `curl http://localhost:5000/dash/`

---

## Deployment Checklist

### Pre-Deployment
- [ ] Docker installed and running
- [ ] Python 3.8+ with venv
- [ ] Repository cloned
- [ ] Dependencies installed
- [ ] Isolated test network available

### Initial Setup
- [ ] Run `python3 tests/smoke_test.py`
- [ ] Start dashboard
- [ ] Access http://localhost:5000/dash/
- [ ] Verify API endpoints respond
- [ ] Test IPTables enable/disable

### Docker Deployment
- [ ] Build image: `docker-compose build`
- [ ] Start services: `docker-compose up -d`
- [ ] Check logs: `docker-compose logs -f`
- [ ] Verify NET_ADMIN capability
- [ ] Test IPTables inside container

### Security
- [ ] Review network isolation
- [ ] Verify no production systems on test network
- [ ] Document authorized testing scope
- [ ] Implement safety interlocks (hardware)

### Documentation
- [ ] Read README.md
- [ ] Review REFERENCE.md
- [ ] Understand attack vectors
- [ ] Review safety guidelines

---

## Advanced Configuration

### Custom Docker Build

```dockerfile
# Extend base Dockerfile
FROM doom-gloom-dashboard:latest
RUN apt-get install -y additional-tools
COPY custom_attacks/ /app/scenarios/attack_modules/
```

### Environment Variables

```bash
export FLASK_ENV=production
export FLASK_DEBUG=0
export CNC_IP=192.168.1.100
export PROXY_PORT=9999
```

### Custom Attack Modules

```python
# scenarios/attack_modules/custom_attack.py
def custom_attack(gcode):
    # Modify G-code
    return modified_gcode
```

Register in `dashboard_enhanced.py`:
```python
from scenarios.attack_modules.custom_attack import custom_attack
dashboard_data.custom_attacks['my_attack'] = custom_attack
```

---

## Next Steps

1. **Configure Network**: Set CNC IP via UI or API
2. **Enable IPTables**: Click "Enable Interception"
3. **Connect CNC**: Use connection panel
4. **Configure Attacks**: Select attack types
5. **Monitor**: Watch real-time dashboard

See [REFERENCE.md](REFERENCE.md) for command reference and API docs.
