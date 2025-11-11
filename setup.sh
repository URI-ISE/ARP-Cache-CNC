#!/bin/bash
# Setup script for Manufacturing Systems Security Framework
# Run this script after cloning the repository

set -e  # Exit on error

echo "========================================================================"
echo "Manufacturing Systems Security Framework - Setup Script"
echo "========================================================================"
echo ""

# Check for required commands
check_command() {
    if ! command -v $1 &> /dev/null; then
        echo "[!] Error: $1 is not installed"
        echo "    Please install $1 and try again"
        exit 1
    else
        echo "[+] Found: $1"
    fi
}

echo "[*] Checking prerequisites..."
check_command docker
check_command python3
check_command git

# Check Docker Compose
if docker compose version &> /dev/null; then
    echo "[+] Found: docker compose (v2)"
elif docker-compose --version &> /dev/null; then
    echo "[+] Found: docker-compose (v1)"
else
    echo "[!] Error: docker compose is not available"
    echo "    Please install Docker Compose and try again"
    exit 1
fi

echo ""
echo "[*] Setting up Python virtual environment..."

# Create virtual environment
if [ ! -d "venv" ]; then
    python3 -m venv venv
    echo "[+] Virtual environment created"
else
    echo "[+] Virtual environment already exists"
fi

# Activate virtual environment
source venv/bin/activate

# Upgrade pip
echo "[*] Upgrading pip..."
pip install --upgrade pip > /dev/null 2>&1

# Install requirements
echo "[*] Installing Python dependencies..."
pip install -r requirements.txt

echo ""
echo "[*] Creating required directories..."

# Ensure all data directories exist
mkdir -p data/archived_experiments
mkdir -p data/baseline
mkdir -p data/captures
mkdir -p infrastructure/volumes/logs
mkdir -p infrastructure/volumes/scripts

echo "[+] Directories created"

echo ""
echo "[*] Copying scripts to Docker volume..."

# Copy attack orchestrator to volume
cp scenarios/attack_modules/arp_attack_orchestrator.py infrastructure/volumes/
chmod +x infrastructure/volumes/arp_attack_orchestrator.py

echo "[+] Scripts copied"

echo ""
echo "[*] Pulling Docker images (this may take a few minutes)..."

cd infrastructure/docker
docker compose pull

echo ""
echo "========================================================================"
echo "[+] Setup Complete!"
echo "========================================================================"
echo ""
echo "Next steps:"
echo ""
echo "1. Start the infrastructure:"
echo "   cd infrastructure/docker"
echo "   docker compose up -d"
echo ""
echo "2. Verify containers are running:"
echo "   docker ps"
echo ""
echo "3. Access the attacker container:"
echo "   docker exec -it M-10.9.0.105 /bin/bash"
echo ""
echo "4. Read the documentation:"
echo "   - docs/GETTING_STARTED.md for detailed setup"
echo "   - docs/ARCHITECTURE.md for system overview"
echo ""
echo "For more information, see README.md"
echo "========================================================================"
