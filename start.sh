#!/bin/bash
#
# SOLAR PhotoSync v1.0 - Quick Start Script
# Для Mac Mini / Linux
#

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="$SCRIPT_DIR/venv"
CONFIG_FILE="$SCRIPT_DIR/config/photosync.config.json"

# Цвета для вывода
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}"
echo "╔═══════════════════════════════════════╗"
echo "║     ☀️  SOLAR PhotoSync v1.0          ║"
echo "║     Quick Start Script               ║"
echo "╚═══════════════════════════════════════╝"
echo -e "${NC}"

# Проверяем Python
check_python() {
    if command -v python3 &> /dev/null; then
        PYTHON_CMD="python3"
    elif command -v python &> /dev/null; then
        PYTHON_CMD="python"
    else
        echo -e "${RED}Error: Python not found!${NC}"
        echo "Please install Python 3.9 or higher"
        exit 1
    fi
    
    echo -e "${GREEN}✓ Python found: $($PYTHON_CMD --version)${NC}"
}

# Создаём виртуальное окружение
setup_venv() {
    if [ ! -d "$VENV_DIR" ]; then
        echo -e "${YELLOW}Creating virtual environment...${NC}"
        $PYTHON_CMD -m venv "$VENV_DIR"
    fi
    
    # Активируем
    source "$VENV_DIR/bin/activate"
    echo -e "${GREEN}✓ Virtual environment activated${NC}"
}

# Устанавливаем зависимости
install_deps() {
    echo -e "${YELLOW}Installing dependencies...${NC}"
    pip install --upgrade pip -q
    pip install -r "$SCRIPT_DIR/requirements.txt" -q
    echo -e "${GREEN}✓ Dependencies installed${NC}"
}

# Проверяем конфигурацию
check_config() {
    if [ ! -f "$CONFIG_FILE" ]; then
        echo -e "${YELLOW}Config file not found. Will be created on first run.${NC}"
        return
    fi
    
    # Проверяем токен
    TOKEN=$(grep -o '"token"[[:space:]]*:[[:space:]]*"[^"]*"' "$CONFIG_FILE" | head -1 | cut -d'"' -f4)
    
    if [ "$TOKEN" = "YOUR_TELEGRAM_BOT_TOKEN_HERE" ] || [ -z "$TOKEN" ]; then
        echo -e "${RED}⚠️  WARNING: Bot token not configured!${NC}"
        echo ""
        echo "Please edit: $CONFIG_FILE"
        echo "And set your Telegram Bot Token in 'bot.token' field"
        echo ""
        echo "Or set environment variable: export TELEGRAM_BOT_TOKEN=your_token"
        echo ""
    else
        echo -e "${GREEN}✓ Bot token configured${NC}"
    fi
}

# Устанавливаем HEIC конвертер (macOS)
install_heic_support() {
    if [[ "$OSTYPE" == "darwin"* ]]; then
        # macOS - sips встроен, но можем установить ImageMagick
        if ! command -v magick &> /dev/null; then
            echo -e "${YELLOW}Tip: Install ImageMagick for better HEIC support:${NC}"
            echo "  brew install imagemagick"
        else
            echo -e "${GREEN}✓ ImageMagick found${NC}"
        fi
    elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
        if ! command -v convert &> /dev/null; then
            echo -e "${YELLOW}Tip: Install ImageMagick for HEIC support:${NC}"
            echo "  sudo apt-get install imagemagick libheif-examples"
        else
            echo -e "${GREEN}✓ ImageMagick found${NC}"
        fi
    fi
}

# Запуск
run_bot() {
    echo ""
    echo -e "${GREEN}Starting SOLAR PhotoSync...${NC}"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    
    cd "$SCRIPT_DIR"
    $PYTHON_CMD src/bot.py "$@"
}

# Main
main() {
    check_python
    setup_venv
    install_deps
    check_config
    install_heic_support
    
    echo ""
    echo -e "${GREEN}Setup complete!${NC}"
    echo ""
    
    # Если передан аргумент --no-run, не запускаем
    if [[ "$1" != "--setup-only" ]]; then
        run_bot "$@"
    fi
}

# Помощь
if [[ "$1" == "-h" ]] || [[ "$1" == "--help" ]]; then
    echo "Usage: ./start.sh [options]"
    echo ""
    echo "Options:"
    echo "  --setup-only    Only setup, don't run"
    echo "  -p, --port      Server port (default: 8080)"
    echo "  -c, --config    Path to config file"
    echo "  -h, --help      Show this help"
    exit 0
fi

main "$@"
