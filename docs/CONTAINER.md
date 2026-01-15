# Container Deployment Guide

This guide covers building and deploying the ARP-Cache-CNC container to GitHub Container Registry (GHCR) and running it in various environments.

## GitHub Container Registry (GHCR)

The container is automatically built and published to GHCR on every push to `main` and `develop` branches, as well as for version tags.

### Registry Location

```
ghcr.io/uri-ise/ARP-Cache-CNC
```

### Available Tags

- `latest` - Latest stable version from main branch
- `develop` - Development branch (most recent features)
- `vX.Y.Z` - Semantic version releases
- `sha-<commit>` - Specific commit SHA

### Pulling from GHCR

```bash
# Latest stable
docker pull ghcr.io/uri-ise/ARP-Cache-CNC:latest

# Development version
docker pull ghcr.io/uri-ise/ARP-Cache-CNC:develop

# Specific version
docker pull ghcr.io/uri-ise/ARP-Cache-CNC:v1.0.0
```

### Authentication

For private repositories or to increase pull rate limits:

```bash
# Using GitHub CLI
gh auth login

# Using PAT (Personal Access Token)
echo $CR_PAT | docker login ghcr.io -u <username> --password-stdin

# Using GitHub token
echo ${{ secrets.GITHUB_TOKEN }} | docker login ghcr.io -u <username> --password-stdin
```

## Local Development

### Build locally

```bash
# Build from current directory
docker build -t arp-cache-cnc:dev .

# Build with custom tag
docker build -t arp-cache-cnc:custom-tag .

# Build with build arguments
docker build --build-arg PYTHON_VERSION=3.10 -t arp-cache-cnc:py310 .
```

### Run locally

```bash
# Basic run with port mapping
docker run -p 5000:5000 arp-cache-cnc:latest

# Run with volume mounts for data persistence
docker run -p 5000:5000 \
  -v $(pwd)/logs:/app/logs \
  -v $(pwd)/data:/app/data \
  arp-cache-cnc:latest

# Run with Docker Compose
docker-compose up -d
docker-compose logs -f dashboard

# Stop and clean up
docker-compose down
```

## Production Deployment

### With Docker

```bash
# Pull from GHCR
docker pull ghcr.io/uri-ise/ARP-Cache-CNC:latest

# Run with recommended settings
docker run -d \
  --name arp-cache-cnc \
  -p 5000:5000 \
  --restart unless-stopped \
  --cap-add=NET_ADMIN \
  --cap-add=NET_RAW \
  -v /data/logs:/app/logs \
  -v /data/experiments:/app/data \
  -e FLASK_ENV=production \
  -e LOG_LEVEL=INFO \
  ghcr.io/uri-ise/ARP-Cache-CNC:latest
```

### With Docker Compose (Production)

Create `docker-compose.prod.yml`:

```yaml
version: '3.8'

services:
  dashboard:
    image: ghcr.io/uri-ise/ARP-Cache-CNC:latest
    container_name: arp-cache-cnc-prod
    restart: always
    ports:
      - "5000:5000"
    volumes:
      - /opt/arp-cache-cnc/logs:/app/logs
      - /opt/arp-cache-cnc/data:/app/data
    environment:
      - FLASK_ENV=production
      - LOG_LEVEL=WARNING
    cap_add:
      - NET_ADMIN
      - NET_RAW
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:5000/api/status"]
      interval: 30s
      timeout: 10s
      retries: 3
```

Run with:
```bash
docker-compose -f docker-compose.prod.yml up -d
```

### Kubernetes Deployment

Create `k8s-deployment.yaml`:

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: arp-cache-cnc
  labels:
    app: arp-cache-cnc
spec:
  replicas: 1
  selector:
    matchLabels:
      app: arp-cache-cnc
  template:
    metadata:
      labels:
        app: arp-cache-cnc
    spec:
      containers:
      - name: dashboard
        image: ghcr.io/uri-ise/ARP-Cache-CNC:latest
        imagePullPolicy: Always
        ports:
        - containerPort: 5000
        env:
        - name: FLASK_ENV
          value: "production"
        - name: LOG_LEVEL
          value: "INFO"
        volumeMounts:
        - name: logs
          mountPath: /app/logs
        - name: data
          mountPath: /app/data
        resources:
          requests:
            memory: "256Mi"
            cpu: "250m"
          limits:
            memory: "1Gi"
            cpu: "1000m"
        livenessProbe:
          httpGet:
            path: /api/status
            port: 5000
          initialDelaySeconds: 30
          periodSeconds: 10
      volumes:
      - name: logs
        emptyDir: {}
      - name: data
        emptyDir: {}
```

Deploy with:
```bash
kubectl apply -f k8s-deployment.yaml
```

## Security Considerations

### Capabilities

The container requires the following Linux capabilities for network interception:

- `NET_ADMIN` - Required for IPTables manipulation
- `NET_RAW` - Required for raw socket access

**Warning**: Only use these capabilities on isolated research networks. Never use on production systems without proper authorization.

### User Permissions

The container runs as non-root user (`appuser`, UID 1000) for security. Some operations may require elevated privileges via:

- Docker run with `--privileged` flag (less secure)
- Capabilities binding (recommended)
- User namespace remapping

### Image Scanning

Container images are automatically scanned with Trivy for vulnerabilities. Results are published to GitHub Security tab.

## Troubleshooting

### Permission Denied Errors

If you see permission errors related to IPTables:

```bash
# Ensure capabilities are properly set
docker run --cap-add=NET_ADMIN --cap-add=NET_RAW ...

# Or use privileged mode (less secure)
docker run --privileged ...
```

### Port Already in Use

```bash
# Use a different port
docker run -p 8000:5000 arp-cache-cnc:latest

# Or find and stop the existing process
docker ps
docker stop <container-id>
```

### View Logs

```bash
# Docker
docker logs arp-cache-cnc-dashboard

# Docker Compose
docker-compose logs -f dashboard

# Inside container
docker exec -it arp-cache-cnc-dashboard bash
tail -f /app/logs/flask.log
```

### Health Check Status

```bash
# Check container health
docker inspect --format='{{.State.Health.Status}}' arp-cache-cnc-dashboard

# Manual health check
curl http://localhost:5000/api/status
```

## Image Information

### Labels

The container includes OCI-compliant labels:

```
org.opencontainers.image.title=ARP-Cache-CNC
org.opencontainers.image.description=CNC Security Research Dashboard
org.opencontainers.image.url=https://github.com/uri-ise/ARP-Cache-CNC
org.opencontainers.image.source=https://github.com/uri-ise/ARP-Cache-CNC
```

### Layer Information

```bash
# Inspect image layers
docker inspect ghcr.io/uri-ise/ARP-Cache-CNC:latest

# Check image size
docker images ghcr.io/uri-ise/ARP-Cache-CNC:latest
```

## CI/CD Pipeline

The container build pipeline includes:

1. **Build Phase** - Multi-stage Docker build with caching
2. **Push Phase** - Push to GHCR with semantic versioning
3. **Scan Phase** - Trivy security scanning
4. **Report Phase** - Publish results to GitHub Security

Workflow file: [.github/workflows/container.yml](.github/workflows/container.yml)

## Support

For issues with container deployment, refer to:

- [README.md](../README.md) - Main project documentation
- [CONTRIBUTING.md](../CONTRIBUTING.md) - Development guidelines
- [GitHub Issues](https://github.com/uri-ise/ARP-Cache-CNC/issues) - Report problems

---

**Last Updated**: January 2026
**Organization**: University of Rhode Island, Industrial Systems Engineering
