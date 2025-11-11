# Doom-and-Gloom CNC Security Dashboard
# Dockerfile for running with IPTables control
FROM python:3.9-slim

# Install system dependencies for networking tools
RUN apt-get update && apt-get install -y \
    iptables \
    iproute2 \
    net-tools \
    curl \
    tcpdump \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create necessary directories
RUN mkdir -p /app/logs /app/static /app/templates

# Expose ports
EXPOSE 5000

# Set environment variables
ENV FLASK_APP=analysis/dashboard_enhanced.py
ENV FLASK_ENV=production
ENV PYTHONUNBUFFERED=1

# Run the dashboard loader which starts both Flask and Dash UIs
CMD ["python3", "analysis/frontend/arp_loader.py"]
