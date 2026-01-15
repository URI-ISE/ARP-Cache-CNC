# ARP-Cache-CNC: CNC Security Research Dashboard
# Optimized for GitHub Container Registry
FROM python:3.9-slim

# Metadata
LABEL org.opencontainers.image.title="ARP-Cache-CNC"
LABEL org.opencontainers.image.description="CNC Security Research Dashboard with network interception and G-code attack analysis"
LABEL org.opencontainers.image.url="https://github.com/uri-ise/ARP-Cache-CNC"
LABEL org.opencontainers.image.source="https://github.com/uri-ise/ARP-Cache-CNC"

# Install system dependencies for networking tools
RUN apt-get update && apt-get install -y --no-install-recommends \
    iptables \
    iproute2 \
    net-tools \
    curl \
    tcpdump \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create necessary directories
RUN mkdir -p /app/logs /app/static /app/templates /app/data

# Create non-root user for security
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

# Expose ports
EXPOSE 5000

# Set environment variables
ENV FLASK_APP=analysis/dashboard_enhanced.py
ENV FLASK_ENV=production
ENV PYTHONUNBUFFERED=1
ENV PATH="/app/bin:${PATH}"

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:5000/api/status || exit 1

# Run the dashboard loader which starts both Flask and Dash UIs
CMD ["python3", "analysis/frontend/arp_loader.py"]
