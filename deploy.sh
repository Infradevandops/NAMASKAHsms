#!/bin/bash
# VRENUM SMS - Linux VPS Deployment Script
# Run this on your fresh Ubuntu 22.04 VPS

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${GREEN}🚀 VRENUM SMS - VPS Deployment${NC}"
echo "=================================="

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    echo -e "${RED}Please run as root (sudo)${NC}"
    exit 1
fi

# =============================================================================
# 1. System Update
# =============================================================================
echo -e "\n${YELLOW}[1/7] Updating system...${NC}"
apt update && apt upgrade -y

# =============================================================================
# 2. Install Docker
# =============================================================================
echo -e "\n${YELLOW}[2/7] Installing Docker...${NC}"
if ! command -v docker &> /dev/null; then
    curl -fsSL https://get.docker.com | sh
    systemctl enable docker
    systemctl start docker
    echo -e "${GREEN}✅ Docker installed${NC}"
else
    echo -e "${GREEN}✅ Docker already installed${NC}"
fi

# Install Docker Compose plugin
apt install -y docker-compose-plugin

# =============================================================================
# 3. Create app user
# =============================================================================
echo -e "\n${YELLOW}[3/7] Creating app user...${NC}"
if ! id "vrenum" &>/dev/null; then
    useradd -m -s /bin/bash vrenum
    usermod -aG docker vrenum
    echo -e "${GREEN}✅ User 'vrenum' created${NC}"
else
    echo -e "${GREEN}✅ User 'vrenum' already exists${NC}"
fi

# =============================================================================
# 4. Setup firewall
# =============================================================================
echo -e "\n${YELLOW}[4/7] Configuring firewall...${NC}"
apt install -y ufw
ufw default deny incoming
ufw default allow outgoing
ufw allow ssh
ufw allow 80/tcp
ufw allow 443/tcp
ufw --force enable
echo -e "${GREEN}✅ Firewall configured${NC}"

# =============================================================================
# 5. Clone/Update repository
# =============================================================================
echo -e "\n${YELLOW}[5/7] Setting up application...${NC}"
APP_DIR="/home/vrenum/app"

if [ -d "$APP_DIR" ]; then
    cd $APP_DIR
    sudo -u vrenum git pull origin main
    echo -e "${GREEN}✅ Repository updated${NC}"
else
    sudo -u vrenum git clone https://github.com/Infradevandops/NAMASKAHsms.git $APP_DIR
    echo -e "${GREEN}✅ Repository cloned${NC}"
fi

cd $APP_DIR

# =============================================================================
# 6. Setup environment
# =============================================================================
echo -e "\n${YELLOW}[6/7] Setting up environment...${NC}"
if [ ! -f "$APP_DIR/.env" ]; then
    cp .env.production.example .env
    echo -e "${YELLOW}⚠️  Please edit .env with your credentials:${NC}"
    echo "   nano $APP_DIR/.env"
else
    echo -e "${GREEN}✅ .env file exists${NC}"
fi

# Create directories
mkdir -p logs uploads backups/db certs
chown -R vrenum:vrenum $APP_DIR

# =============================================================================
# 7. Start application
# =============================================================================
echo -e "\n${YELLOW}[7/7] Starting application...${NC}"

# Check if .env is configured
if grep -q "your-secret-key" .env 2>/dev/null; then
    echo -e "${RED}❌ Please configure .env before starting:${NC}"
    echo "   nano $APP_DIR/.env"
    echo ""
    echo "Then run:"
    echo "   cd $APP_DIR && docker compose up -d"
    exit 1
fi

# Start with Docker Compose
docker compose up -d --build

echo -e "\n${GREEN}=================================="
echo "✅ VRENUM SMS Deployed!"
echo "==================================${NC}"
echo ""
echo "Next steps:"
echo "1. Setup SSL: ./scripts/setup-ssl.sh vrenum.app"
echo "2. Check logs: docker compose logs -f"
echo "3. Check health: curl http://localhost:8000/health"
echo ""
echo "Useful commands:"
echo "  docker compose logs -f app     # App logs"
echo "  docker compose restart app     # Restart app"
echo "  docker compose down            # Stop all"
echo "  docker compose up -d           # Start all"
