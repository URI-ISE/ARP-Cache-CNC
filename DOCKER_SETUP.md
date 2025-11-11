# Docker Setup for Doom-and-Gloom Dashboard

This guide covers running the Doom-and-Gloom CNC Security Dashboard in Docker with IPTables control on Windows with WSL2.

## Prerequisites

### 1. Install Docker Desktop for Windows
- Download: https://www.docker.com/products/docker-desktop/
- Enable WSL2 backend during installation
- Docker Desktop will integrate with your WSL2 distro automatically

### 2. Verify Docker is Running
Open PowerShell or WSL terminal:
```bash
docker --version
docker-compose --version
```

### 3. Enable WSL2 Integration
1. Open Docker Desktop
2. Go to Settings → Resources → WSL Integration
3. Enable integration with your WSL distro (Ubuntu/Debian)
4. Click "Apply & Restart"

## Quick Start

### Option 1: Run with Docker Compose (Recommended)

**In WSL terminal:**
```bash
cd /mnt/c/Users/lukep/Documents/Doom-and-Gloom

# Build the image
docker-compose build

# Start the dashboard
docker-compose up -d

# View logs
docker-compose logs -f dashboard

# Stop
docker-compose down
```

Access the dashboard:
- Dash ARP UI: http://localhost:5000/dash/
- Flask API: http://localhost:5000/api/status
- Flask Dashboard: http://localhost:5000/

### Option 2: Run with Docker CLI

```bash
cd /mnt/c/Users/lukep/Documents/Doom-and-Gloom

# Build the image
docker build -t doom-gloom-dashboard .

# Run with NET_ADMIN capability for IPTables
docker run -d \
  --name doom-dashboard \
  --cap-add NET_ADMIN \
  --cap-add NET_RAW \
  --network host \
  -v "$(pwd)/logs:/app/logs" \
  -v "$(pwd)/../ARP_Attack:/ARP_Attack:ro" \
  doom-gloom-dashboard

# View logs
docker logs -f doom-dashboard

# Stop
docker stop doom-dashboard
docker rm doom-dashboard
```

## IPTables Control

### Why NET_ADMIN capability?
The dashboard needs to manipulate IPTables rules to intercept and modify CNC traffic. This requires the `NET_ADMIN` capability in Docker.

### Verify IPTables Works Inside Container
```bash
# Exec into running container
docker exec -it doom-dashboard bash

# Check IPTables (should work with NET_ADMIN)
iptables -L -n

# Test creating a rule
iptables -t nat -A OUTPUT -p tcp --dport 8080 -j REDIRECT --to-port 8888
iptables -t nat -L -n

# Clean up test rule
iptables -t nat -F
```

### Enable IPTables via Dashboard API
```bash
# From host (Windows or WSL)
curl -X POST http://localhost:5000/api/iptables/setup \
  -H "Content-Type: application/json" \
  -d '{
    "interface": "eth0",
    "cnc_ip": "192.168.0.170",
    "proxy_port": 8888
  }'

# Check status
curl http://localhost:5000/api/iptables/status

# Disable
curl -X POST http://localhost:5000/api/iptables/disable
```

## Troubleshooting

### Issue: "Operation not permitted" when using IPTables
**Solution**: Ensure container has `NET_ADMIN` capability or run with `privileged: true` in docker-compose.yml

### Issue: Container can't find ARP_Attack files
**Solution**: Update the volume mount path in docker-compose.yml:
```yaml
volumes:
  - /path/to/ARP_Attack:/ARP_Attack:ro
```

### Issue: Port 5000 already in use
**Solution**: Stop the WSL venv server first:
```bash
pkill -f arp_loader.py
```

### Issue: Docker commands not found in WSL
**Solution**: Restart Docker Desktop and ensure WSL integration is enabled in Settings.

## Development Mode

Run without Docker for faster iteration:
```bash
cd /mnt/c/Users/lukep/Documents/Doom-and-Gloom
source .venv/bin/activate
cd analysis/frontend
python3 arp_loader.py
```

Note: IPTables commands will require `sudo` when running outside Docker.

## Production Considerations

1. **Security**: Use `cap_add` instead of `privileged: true` for least-privilege principle
2. **Networking**: Use `network_mode: host` for IPTables to work on host network stack
3. **Persistence**: Mount `/app/logs` for persistent attack logs
4. **Secrets**: Store CNC IPs and credentials in environment variables or Docker secrets
5. **Monitoring**: Add health checks in docker-compose.yml:
   ```yaml
   healthcheck:
     test: ["CMD", "curl", "-f", "http://localhost:5000/api/status"]
     interval: 30s
     timeout: 10s
     retries: 3
   ```

## Next Steps

1. Open http://localhost:5000/dash/ in your browser
2. Configure network settings via the UI
3. Enable IPTables interception
4. Connect to CNC machine and start attacks
5. Monitor real-time dashboard for attack statistics
