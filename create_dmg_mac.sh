#!/bin/bash

# Create DMG installer for macOS
# Thai ID Card Reader - DMG Creator

echo "💿 Creating DMG installer for Mac..."
echo "====================================="
echo ""

# Check if app exists
if [ ! -d "dist/ThaiIDCardReader.app" ]; then
    echo "❌ ThaiIDCardReader.app not found!"
    echo "Please run ./build_mac.sh first."
    exit 1
fi

# Check if create-dmg is installed
if ! command -v create-dmg &> /dev/null; then
    echo "⚠️  create-dmg is not installed."
    echo ""
    echo "Installing create-dmg via Homebrew..."
    if ! command -v brew &> /dev/null; then
        echo "❌ Homebrew is not installed."
        echo "Please install Homebrew first: https://brew.sh"
        exit 1
    fi
    brew install create-dmg
fi

# Create DMG directory
mkdir -p dist/dmg

# Create DMG
echo "Creating DMG installer..."
create-dmg \
  --volname "Thai ID Card Reader" \
  --volicon "dist/ThaiIDCardReader.app/Contents/Resources/icon-windowed.icns" \
  --window-pos 200 120 \
  --window-size 800 400 \
  --icon-size 100 \
  --icon "ThaiIDCardReader.app" 200 190 \
  --hide-extension "ThaiIDCardReader.app" \
  --app-drop-link 600 185 \
  --no-internet-enable \
  "dist/ThaiIDCardReader.dmg" \
  "dist/ThaiIDCardReader.app" \
  2>/dev/null || \
create-dmg \
  --volname "Thai ID Card Reader" \
  --window-pos 200 120 \
  --window-size 800 400 \
  --icon-size 100 \
  --app-drop-link 600 185 \
  "dist/ThaiIDCardReader.dmg" \
  "dist/ThaiIDCardReader.app"

# Check if DMG was created
if [ -f "dist/ThaiIDCardReader.dmg" ]; then
    echo ""
    echo "✅ DMG created successfully!"
    echo "📦 Installer: dist/ThaiIDCardReader.dmg"
    echo ""
    echo "You can now distribute this DMG file to users."
else
    echo ""
    echo "❌ Failed to create DMG!"
    exit 1
fi
