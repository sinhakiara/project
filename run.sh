#!/bin/bash
# Quick start script for StealthCrawler v17

set -e

echo "================================================"
echo "  StealthCrawler v17 - Quick Start Script"
echo "================================================"
echo ""

# Check Python version
echo "[1/5] Checking Python version..."
python_version=$(python3 --version 2>&1 | awk '{print $2}')
echo "  ✓ Python $python_version found"

# Install dependencies
echo ""
echo "[2/5] Installing dependencies..."
if [ -f "requirements.txt" ]; then
    pip3 install -r requirements.txt -q
    echo "  ✓ Dependencies installed"
else
    echo "  ✗ requirements.txt not found!"
    exit 1
fi

# Install Playwright browsers
echo ""
echo "[3/5] Installing Playwright browsers..."
playwright install chromium
echo "  ✓ Playwright browsers installed"

# Create necessary directories
echo ""
echo "[4/5] Creating directories..."
mkdir -p output logs checkpoints
echo "  ✓ Directories created"

# Copy environment file
echo ""
echo "[5/5] Setting up environment..."
if [ ! -f ".env" ] && [ -f ".env.example" ]; then
    cp .env.example .env
    echo "  ✓ Created .env file from .env.example"
    echo "  ℹ Please edit .env file to configure your settings"
else
    echo "  ℹ .env file already exists or .env.example not found"
fi

echo ""
echo "================================================"
echo "  Setup Complete!"
echo "================================================"
echo ""
echo "Quick Start Commands:"
echo "  Basic crawl:     python3 main.py crawl https://example.com"
echo "  Scope test:      python3 main.py scope-test --help"
echo "  API server:      python3 main.py server"
echo "  Distributed:     python3 main.py distributed --help"
echo ""
echo "For more options: python3 main.py --help"
echo ""
