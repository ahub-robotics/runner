#!/bin/bash
################################################################################
# Build Robot Runner for macOS
################################################################################
#
# Compila Robot Runner en un ejecutable standalone para macOS.
#
# Requisitos:
#   - Python 3.9+
#   - PyInstaller instalado (pip install pyinstaller)
#   - Todas las dependencias instaladas (pip install -r requirements.txt)
#
# Uso:
#   ./build/scripts/build_macos.sh
#
# Output:
#   dist/RobotRunner/RobotRunner (executable)
#   dist/RobotRunner-macOS.zip (distributable)
#
################################################################################

set -e  # Exit on error

echo "======================================================================"
echo "  Building Robot Runner for macOS"
echo "======================================================================"
echo ""

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Check Python version
echo -e "${YELLOW}➤${NC} Checking Python version..."
PYTHON_VERSION=$(python3 --version | cut -d' ' -f2)
echo "  Python $PYTHON_VERSION"

# Check PyInstaller
echo -e "${YELLOW}➤${NC} Checking PyInstaller..."
if ! command -v pyinstaller &> /dev/null; then
    echo -e "${RED}✗${NC} PyInstaller not found. Installing..."
    pip install pyinstaller
else
    PYINSTALLER_VERSION=$(pyinstaller --version)
    echo "  PyInstaller $PYINSTALLER_VERSION"
fi

# Clean previous build
echo -e "${YELLOW}➤${NC} Cleaning previous build..."
rm -rf build/RobotRunner dist/RobotRunner dist/RobotRunner-macOS.zip
echo "  Cleaned"

# Build
echo -e "${YELLOW}➤${NC} Building with PyInstaller..."
pyinstaller app.spec

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓${NC} Build successful!"
else
    echo -e "${RED}✗${NC} Build failed!"
    exit 1
fi

# Check output
if [ -f "dist/RobotRunner/RobotRunner" ]; then
    SIZE=$(du -sh dist/RobotRunner | cut -f1)
    echo -e "${GREEN}✓${NC} Executable created: dist/RobotRunner/RobotRunner ($SIZE)"
else
    echo -e "${RED}✗${NC} Executable not found!"
    exit 1
fi

# Create ZIP for distribution
echo -e "${YELLOW}➤${NC} Creating distribution package..."
cd dist
zip -r RobotRunner-macOS.zip RobotRunner/
cd ..

if [ -f "dist/RobotRunner-macOS.zip" ]; then
    SIZE=$(du -sh dist/RobotRunner-macOS.zip | cut -f1)
    echo -e "${GREEN}✓${NC} Distribution package: dist/RobotRunner-macOS.zip ($SIZE)"
else
    echo -e "${RED}✗${NC} Failed to create distribution package"
    exit 1
fi

# Optional: Create DMG (requires create-dmg)
if command -v create-dmg &> /dev/null; then
    echo -e "${YELLOW}➤${NC} Creating DMG installer..."
    create-dmg \
        --volname "Robot Runner" \
        --window-pos 200 120 \
        --window-size 600 400 \
        --icon-size 100 \
        --hide-extension "RobotRunner" \
        --app-drop-link 425 120 \
        "dist/RobotRunner.dmg" \
        "dist/RobotRunner/" || true

    if [ -f "dist/RobotRunner.dmg" ]; then
        SIZE=$(du -sh dist/RobotRunner.dmg | cut -f1)
        echo -e "${GREEN}✓${NC} DMG created: dist/RobotRunner.dmg ($SIZE)"
    fi
else
    echo -e "${YELLOW}ⓘ${NC} create-dmg not found. Skipping DMG creation."
    echo "  Install with: brew install create-dmg"
fi

# Test executable
echo -e "${YELLOW}➤${NC} Testing executable..."
./dist/RobotRunner/RobotRunner --help &> /dev/null || true
echo -e "${GREEN}✓${NC} Executable runs"

echo ""
echo "======================================================================"
echo -e "${GREEN}✓ Build completed successfully!${NC}"
echo "======================================================================"
echo ""
echo "Output files:"
echo "  • dist/RobotRunner/RobotRunner"
echo "  • dist/RobotRunner-macOS.zip"
if [ -f "dist/RobotRunner.dmg" ]; then
    echo "  • dist/RobotRunner.dmg"
fi
echo ""
echo "To test:"
echo "  cd dist/RobotRunner && ./RobotRunner"
echo ""
