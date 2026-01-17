#!/bin/bash

# PHOW Setup Script
# This script helps you configure the project with your own API keys

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}"
echo "╔═══════════════════════════════════════════════════════════╗"
echo "║                                                           ║"
echo "║   ██████╗ ██╗  ██╗ ██████╗ ██╗    ██╗                    ║"
echo "║   ██╔══██╗██║  ██║██╔═══██╗██║    ██║                    ║"
echo "║   ██████╔╝███████║██║   ██║██║ █╗ ██║                    ║"
echo "║   ██╔═══╝ ██╔══██║██║   ██║██║███╗██║                    ║"
echo "║   ██║     ██║  ██║╚██████╔╝╚███╔███╔╝                    ║"
echo "║   ╚═╝     ╚═╝  ╚═╝ ╚═════╝  ╚══╝╚══╝                     ║"
echo "║                                                           ║"
echo "║   AI-Powered Business Analytics Platform                  ║"
echo "║                                                           ║"
echo "╚═══════════════════════════════════════════════════════════╝"
echo -e "${NC}"

echo ""
echo -e "${GREEN}Welcome to PHOW Setup!${NC}"
echo ""
echo "This script will help you configure the project with your own API keys."
echo "No credentials will be shared - you'll use your own accounts."
echo ""

# Check for Docker
echo -e "${YELLOW}Checking prerequisites...${NC}"
if command -v docker &> /dev/null; then
    echo -e "  ${GREEN}✓${NC} Docker is installed"
else
    echo -e "  ${RED}✗${NC} Docker is not installed"
    echo "    Please install Docker: https://docs.docker.com/get-docker/"
    exit 1
fi

if command -v docker-compose &> /dev/null || docker compose version &> /dev/null; then
    echo -e "  ${GREEN}✓${NC} Docker Compose is available"
else
    echo -e "  ${RED}✗${NC} Docker Compose is not available"
    echo "    Please install Docker Compose"
    exit 1
fi

echo ""
echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"
echo ""

# API Keys Information
echo -e "${YELLOW}You'll need the following API keys:${NC}"
echo ""
echo "1. ${GREEN}Google Maps API Key${NC} (Required)"
echo "   - FREE \$200/month credit"
echo "   - Get it at: https://console.cloud.google.com/apis/credentials"
echo "   - Enable: Geocoding API, Places API"
echo ""
echo "2. ${GREEN}LLM API Key${NC} (Required - choose one)"
echo "   - OpenAI: https://platform.openai.com/api-keys"
echo "   - Anthropic: https://console.anthropic.com/"
echo ""
echo "3. ${GREEN}Yelp API Key${NC} (Optional - for Competitor Analyzer)"
echo "   - Get it at: https://www.yelp.com/developers/v3/manage_app"
echo ""

read -p "Press Enter when you have your API keys ready..."
echo ""

# Copy .env.example files
echo -e "${YELLOW}Setting up environment files...${NC}"

if [ -f "backend/.env" ]; then
    read -p "backend/.env already exists. Overwrite? (y/N): " overwrite
    if [ "$overwrite" != "y" ] && [ "$overwrite" != "Y" ]; then
        echo "Keeping existing backend/.env"
    else
        cp backend/.env.example backend/.env
        echo -e "  ${GREEN}✓${NC} Created backend/.env"
    fi
else
    cp backend/.env.example backend/.env
    echo -e "  ${GREEN}✓${NC} Created backend/.env"
fi

if [ -f "frontend/.env" ]; then
    read -p "frontend/.env already exists. Overwrite? (y/N): " overwrite
    if [ "$overwrite" != "y" ] && [ "$overwrite" != "Y" ]; then
        echo "Keeping existing frontend/.env"
    else
        cp frontend/.env.example frontend/.env
        echo -e "  ${GREEN}✓${NC} Created frontend/.env"
    fi
else
    cp frontend/.env.example frontend/.env
    echo -e "  ${GREEN}✓${NC} Created frontend/.env"
fi

echo ""

# Collect API Keys
echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"
echo ""
echo -e "${YELLOW}Enter your API keys:${NC}"
echo ""

# Google Maps API Key
read -p "Google Maps API Key: " GOOGLE_MAPS_KEY
if [ -z "$GOOGLE_MAPS_KEY" ]; then
    echo -e "${RED}Google Maps API Key is required!${NC}"
    exit 1
fi

echo ""

# LLM Provider
echo "Which LLM provider will you use?"
echo "  1) OpenAI (GPT-4)"
echo "  2) Anthropic (Claude)"
read -p "Enter choice (1 or 2): " llm_choice

case $llm_choice in
    1)
        LLM_PROVIDER="openai"
        read -p "OpenAI API Key: " LLM_KEY
        ;;
    2)
        LLM_PROVIDER="anthropic"
        read -p "Anthropic API Key: " LLM_KEY
        ;;
    *)
        echo -e "${RED}Invalid choice. Defaulting to Anthropic.${NC}"
        LLM_PROVIDER="anthropic"
        read -p "Anthropic API Key: " LLM_KEY
        ;;
esac

if [ -z "$LLM_KEY" ]; then
    echo -e "${RED}LLM API Key is required!${NC}"
    exit 1
fi

echo ""

# Yelp API Key (optional)
read -p "Yelp API Key (optional, press Enter to skip): " YELP_KEY

echo ""

# Update backend/.env
echo -e "${YELLOW}Configuring backend...${NC}"

# Use sed to update the values (works on both Linux and macOS)
if [[ "$OSTYPE" == "darwin"* ]]; then
    # macOS
    sed -i '' "s|^GOOGLE_MAPS_API_KEY=.*|GOOGLE_MAPS_API_KEY=$GOOGLE_MAPS_KEY|" backend/.env
    sed -i '' "s|^LLM_PROVIDER=.*|LLM_PROVIDER=$LLM_PROVIDER|" backend/.env
    if [ "$LLM_PROVIDER" == "openai" ]; then
        sed -i '' "s|^OPENAI_API_KEY=.*|OPENAI_API_KEY=$LLM_KEY|" backend/.env
    else
        sed -i '' "s|^ANTHROPIC_API_KEY=.*|ANTHROPIC_API_KEY=$LLM_KEY|" backend/.env
    fi
    if [ -n "$YELP_KEY" ]; then
        sed -i '' "s|^YELP_API_KEY=.*|YELP_API_KEY=$YELP_KEY|" backend/.env
    fi
else
    # Linux
    sed -i "s|^GOOGLE_MAPS_API_KEY=.*|GOOGLE_MAPS_API_KEY=$GOOGLE_MAPS_KEY|" backend/.env
    sed -i "s|^LLM_PROVIDER=.*|LLM_PROVIDER=$LLM_PROVIDER|" backend/.env
    if [ "$LLM_PROVIDER" == "openai" ]; then
        sed -i "s|^OPENAI_API_KEY=.*|OPENAI_API_KEY=$LLM_KEY|" backend/.env
    else
        sed -i "s|^ANTHROPIC_API_KEY=.*|ANTHROPIC_API_KEY=$LLM_KEY|" backend/.env
    fi
    if [ -n "$YELP_KEY" ]; then
        sed -i "s|^YELP_API_KEY=.*|YELP_API_KEY=$YELP_KEY|" backend/.env
    fi
fi

echo -e "  ${GREEN}✓${NC} Backend configured"

# Update frontend/.env
echo -e "${YELLOW}Configuring frontend...${NC}"

if [[ "$OSTYPE" == "darwin"* ]]; then
    sed -i '' "s|^NEXT_PUBLIC_GOOGLE_MAPS_API_KEY=.*|NEXT_PUBLIC_GOOGLE_MAPS_API_KEY=$GOOGLE_MAPS_KEY|" frontend/.env
else
    sed -i "s|^NEXT_PUBLIC_GOOGLE_MAPS_API_KEY=.*|NEXT_PUBLIC_GOOGLE_MAPS_API_KEY=$GOOGLE_MAPS_KEY|" frontend/.env
fi

echo -e "  ${GREEN}✓${NC} Frontend configured"

echo ""
echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"
echo ""
echo -e "${GREEN}Setup complete!${NC}"
echo ""
echo "Your configuration:"
echo "  - Google Maps API Key: ${GOOGLE_MAPS_KEY:0:10}..."
echo "  - LLM Provider: $LLM_PROVIDER"
echo "  - LLM API Key: ${LLM_KEY:0:10}..."
if [ -n "$YELP_KEY" ]; then
    echo "  - Yelp API Key: ${YELP_KEY:0:10}..."
fi
echo ""

# Offer to start services
echo -e "${YELLOW}Would you like to start the services now?${NC}"
echo ""
echo "This will run: docker-compose up"
echo ""
read -p "Start services? (Y/n): " start_services

if [ "$start_services" != "n" ] && [ "$start_services" != "N" ]; then
    echo ""
    echo -e "${YELLOW}Starting services...${NC}"
    echo ""
    echo "Backend API will be available at: http://localhost:8000"
    echo "Frontend will need to be started separately:"
    echo "  cd frontend && npm install && npm run dev"
    echo ""
    echo -e "${BLUE}Starting Docker services...${NC}"
    echo ""
    docker-compose up
else
    echo ""
    echo "To start the services later, run:"
    echo ""
    echo "  # Start backend services (API, Database, Redis)"
    echo "  docker-compose up"
    echo ""
    echo "  # Start frontend (in a separate terminal)"
    echo "  cd frontend && npm install && npm run dev"
    echo ""
    echo "Then open http://localhost:3000 in your browser."
fi
