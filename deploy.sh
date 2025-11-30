#!/bin/bash
#
# SOLAR PhotoSync v1.1.0 - Deploy Script
# Автоматическая установка на production сервер
#

set -e

# Цвета
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

# Конфигурация
INSTALL_DIR="/var/www/SolarPhotoSync"
SERVICE_NAME="solarphotosync"
SERVICE_USER="www-data"

echo -e "${BLUE}"
echo "╔═══════════════════════════════════════════════════╗"
echo "║     ☀️  SOLAR PhotoSync v1.1.0                    ║"
echo "║     Deploy Script for Production                  ║"
echo "╚═══════════════════════════════════════════════════╝"
echo -e "${NC}"

# Проверка root
check_root() {
    if [ "$EUID" -ne 0 ]; then
        echo -e "${RED}Error: Please run as root (sudo)${NC}"
        exit 1
    fi
}

# Установка системных зависимостей
install_deps() {
    echo -e "${YELLOW}[1/7] Installing system dependencies...${NC}"
    apt update
    apt install -y python3 python3-pip python3-venv nginx imagemagick libheif-examples git
    echo -e "${GREEN}✓ Dependencies installed${NC}"
}

# Создание структуры директорий
create_dirs() {
    echo -e "${YELLOW}[2/7] Creating directory structure...${NC}"
    
    mkdir -p $INSTALL_DIR
    mkdir -p $INSTALL_DIR/logs
    mkdir -p $INSTALL_DIR/config
    mkdir -p $INSTALL_DIR/SOLAR-PhotoSync
    
    chown -R $SERVICE_USER:$SERVICE_USER $INSTALL_DIR
    chmod -R 755 $INSTALL_DIR
    
    echo -e "${GREEN}✓ Directories created${NC}"
}

# Копирование файлов
copy_files() {
    echo -e "${YELLOW}[3/7] Copying application files...${NC}"
    
    SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
    
    # Копируем всё кроме venv и некоторых файлов
    cp -r $SCRIPT_DIR/src $INSTALL_DIR/
    cp -r $SCRIPT_DIR/tools $INSTALL_DIR/
    cp -r $SCRIPT_DIR/docs $INSTALL_DIR/
    cp $SCRIPT_DIR/requirements.txt $INSTALL_DIR/
    cp $SCRIPT_DIR/config/photosync.production.json $INSTALL_DIR/config/photosync.config.json
    cp $SCRIPT_DIR/config/secret.env.example $INSTALL_DIR/config/
    
    chown -R $SERVICE_USER:$SERVICE_USER $INSTALL_DIR
    
    echo -e "${GREEN}✓ Files copied${NC}"
}

# Создание виртуального окружения
setup_venv() {
    echo -e "${YELLOW}[4/7] Setting up Python virtual environment...${NC}"
    
    cd $INSTALL_DIR
    sudo -u $SERVICE_USER python3 -m venv venv
    sudo -u $SERVICE_USER ./venv/bin/pip install --upgrade pip
    sudo -u $SERVICE_USER ./venv/bin/pip install -r requirements.txt
    
    echo -e "${GREEN}✓ Virtual environment ready${NC}"
}

# Установка systemd сервиса
setup_service() {
    echo -e "${YELLOW}[5/7] Installing systemd service...${NC}"
    
    SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
    cp $SCRIPT_DIR/service/solarphotosync.service /etc/systemd/system/
    
    systemctl daemon-reload
    systemctl enable $SERVICE_NAME
    
    echo -e "${GREEN}✓ Service installed${NC}"
}

# Проверка secret.env
check_secret() {
    echo -e "${YELLOW}[6/7] Checking configuration...${NC}"
    
    if [ ! -f "$INSTALL_DIR/config/secret.env" ]; then
        echo -e "${RED}⚠️  WARNING: secret.env not found!${NC}"
        echo ""
        echo "Please create $INSTALL_DIR/config/secret.env with:"
        echo "  TELEGRAM_BOT_TOKEN=your_token_here"
        echo ""
        echo "Then run: sudo systemctl start $SERVICE_NAME"
        return 1
    fi
    
    chmod 600 $INSTALL_DIR/config/secret.env
    chown $SERVICE_USER:$SERVICE_USER $INSTALL_DIR/config/secret.env
    
    echo -e "${GREEN}✓ Configuration OK${NC}"
    return 0
}

# Запуск
start_service() {
    echo -e "${YELLOW}[7/7] Starting service...${NC}"
    
    systemctl start $SERVICE_NAME
    sleep 2
    
    if systemctl is-active --quiet $SERVICE_NAME; then
        echo -e "${GREEN}✓ Service started successfully${NC}"
        
        # Проверяем health
        sleep 2
        HEALTH=$(curl -s http://127.0.0.1:8080/api/photosync/health 2>/dev/null || echo "")
        
        if [ -n "$HEALTH" ]; then
            echo ""
            echo -e "${GREEN}Health check:${NC}"
            echo "$HEALTH" | python3 -m json.tool
        fi
    else
        echo -e "${RED}✗ Service failed to start${NC}"
        echo "Check logs: journalctl -u $SERVICE_NAME -n 50"
        exit 1
    fi
}

# Вывод информации
print_info() {
    echo ""
    echo -e "${BLUE}═══════════════════════════════════════════════════${NC}"
    echo -e "${GREEN}☀️  SOLAR PhotoSync v1.1.0 installed!${NC}"
    echo -e "${BLUE}═══════════════════════════════════════════════════${NC}"
    echo ""
    echo "Installation directory: $INSTALL_DIR"
    echo ""
    echo "Next steps:"
    echo "  1. Configure Nginx (see docs/DEPLOY.md)"
    echo "  2. Set webhook:"
    echo "     $INSTALL_DIR/venv/bin/python tools/webhook_setup.py set --url https://your-domain.com/api/photosync/webhook"
    echo ""
    echo "Useful commands:"
    echo "  sudo systemctl status $SERVICE_NAME"
    echo "  sudo systemctl restart $SERVICE_NAME"
    echo "  tail -f $INSTALL_DIR/logs/photosync.log"
    echo ""
}

# Main
main() {
    check_root
    install_deps
    create_dirs
    copy_files
    setup_venv
    setup_service
    
    if check_secret; then
        start_service
    fi
    
    print_info
}

# Помощь
if [[ "$1" == "-h" ]] || [[ "$1" == "--help" ]]; then
    echo "Usage: sudo ./deploy.sh"
    echo ""
    echo "Installs SOLAR PhotoSync to /var/www/SolarPhotoSync"
    echo ""
    echo "Prerequisites:"
    echo "  - Ubuntu 20.04+ or Debian 11+"
    echo "  - Root access"
    echo "  - Internet connection"
    exit 0
fi

main
