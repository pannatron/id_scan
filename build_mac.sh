#!/bin/bash

# Build script for macOS
# Thai ID Card Reader - Build for Mac

echo "🍎 Thai ID Card Reader - Mac Build Script"
echo "=========================================="
echo ""

# Check if Python 3 is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed. Please install Python 3 first."
    exit 1
fi

echo "✓ Python 3 found: $(python3 --version)"
echo ""

# Create virtual environment
echo "📦 Creating virtual environment..."
python3 -m venv venv
source venv/bin/activate

# Upgrade pip
echo "📦 Upgrading pip..."
pip install --upgrade pip

# Install dependencies
echo "📦 Installing dependencies..."
pip install -r build_requirements.txt

# Build with PyInstaller
echo "🔨 Building application..."
pyinstaller --clean id_card_reader.spec

# Check if build was successful
if [ -f "dist/ThaiIDCardReader.app/Contents/MacOS/ThaiIDCardReader" ]; then
    echo ""
    echo "✅ Build successful!"
    echo "📦 Application: dist/ThaiIDCardReader.app"
    echo ""
    echo "To create a DMG installer:"
    echo "  1. Install create-dmg: brew install create-dmg"
    echo "  2. Run: ./create_dmg_mac.sh"
    echo ""
    echo "To test the app:"
    echo "  open dist/ThaiIDCardReader.app"
else
    echo ""
    echo "❌ Build failed!"
    exit 1
fi

# Deactivate virtual environment
deactivate
