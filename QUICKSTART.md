# Quick Start Commands - Doom-and-Gloom Dashboard

## 🚀 Start the Dashboard (WSL2 - Development)

```bash
cd /mnt/c/Users/lukep/Documents/Doom-and-Gloom
source .venv/bin/activate
cd analysis/frontend
python3 arp_loader.py
```

**Access in browser:**
- Dash UI: http://localhost:5000/dash/
- Flask Dashboard: http://localhost:5000/
- API: http://localhost:5000/api/status

## 🐳 Start with Docker (Production)

```bash
cd /mnt/c/Users/lukep/Documents/Doom-and-Gloom

# Build and start
docker-compose up -d

# View logs
docker-compose logs -f dashboard

# Stop
docker-compose down
```

## 🧪 Run Tests

```bash
cd /mnt/c/Users/lukep/Documents/Doom-and-Gloom
source .venv/bin/activate
python3 tests/smoke_test.py
```

## 🔧 Common Operations

### Check if server is running
```bash
curl http://localhost:5000/api/status
```

### Kill existing process
```bash
pkill -f arp_loader.py
```

### Enable IPTables interception
```bash
curl -X POST http://localhost:5000/api/iptables/setup \
  -H "Content-Type: application/json" \
  -d '{"interface":"eth0","cnc_ip":"192.168.0.170","proxy_port":8888}'
```

### Check IPTables status
```bash
curl http://localhost:5000/api/iptables/status
```

### Disable IPTables
```bash
curl -X POST http://localhost:5000/api/iptables/disable
```

## 📝 Files Changed/Created

### Core Application
- ✅ `analysis/dashboard_enhanced.py` - Fixed template paths
- ✅ `analysis/frontend/arp_loader.py` - Created Dash loader with URL prefix
- ✅ `requirements.txt` - Added dash-bootstrap-components, flask-socketio, eventlet

### Docker Files
- ✅ `Dockerfile` - Multi-stage build with IPTables support
- ✅ `docker-compose.yml` - Service definition with NET_ADMIN caps
- ✅ `DOCKER_SETUP.md` - Complete Docker setup guide

### Testing & Docs
- ✅ `tests/smoke_test.py` - Endpoint validation tests
- ✅ `QUICKSTART.md` - This file

## 🎯 Next Steps

1. **Open the dashboard**: http://localhost:5000/dash/
2. **Configure network**: Set CNC IP and interface in UI
3. **Enable IPTables**: Click "Enable Interception" button
4. **Connect to CNC**: Use connection panel
5. **Configure attacks**: Enable specific attack types
6. **Monitor**: Watch real-time stats and logs

## ⚠️ Troubleshooting

| Problem | Solution |
|---------|----------|
| Port 5000 in use | `pkill -f arp_loader.py` |
| Template not found | Already fixed in `dashboard_enhanced.py` |
| Dash UI not loading | Check URL is `/dash/` not `/` |
| IPTables permission denied | Use Docker or run with `sudo` |
| Module not found | `pip install -r requirements.txt` |

## 🔗 URLs Reference

- Main Dash UI: http://localhost:5000/dash/
- Flask Dashboard: http://localhost:5000/
- System Status: http://localhost:5000/api/status
- Network Config: http://localhost:5000/api/network/config
- IPTables Status: http://localhost:5000/api/iptables/status
- IPTables Setup: POST http://localhost:5000/api/iptables/setup
- IPTables Disable: POST http://localhost:5000/api/iptables/disable
