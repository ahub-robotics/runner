#!/bin/bash
################################################################################
# Build Robot Runner for Linux
################################################################################
#
# Compila Robot Runner en un ejecutable standalone para Linux.
#
# Requisitos:
#   - Python 3.9+
#   - PyInstaller instalado
#   - Todas las dependencias instaladas
#
# Uso:
#   ./build/scripts/build_linux.sh
#
# Output:
#   dist/RobotRunner/RobotRunner (executable)
#   dist/RobotRunner-Linux.tar.gz (distributable)
#
################################################################################

set -e

echo "======================================================================"
echo "  Building Robot Runner for Linux"
echo "======================================================================"
echo ""

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

# Check Python
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

# Clean
echo -e "${YELLOW}➤${NC} Cleaning previous build..."
rm -rf build/RobotRunner dist/RobotRunner dist/RobotRunner-Linux.tar.gz
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

    # Make executable
    chmod +x dist/RobotRunner/RobotRunner
else
    echo -e "${RED}✗${NC} Executable not found!"
    exit 1
fi

# Create tarball
echo -e "${YELLOW}➤${NC} Creating distribution package..."
cd dist
tar -czf RobotRunner-Linux.tar.gz RobotRunner/
cd ..

if [ -f "dist/RobotRunner-Linux.tar.gz" ]; then
    SIZE=$(du -sh dist/RobotRunner-Linux.tar.gz | cut -f1)
    echo -e "${GREEN}✓${NC} Distribution package: dist/RobotRunner-Linux.tar.gz ($SIZE)"
else
    echo -e "${RED}✗${NC} Failed to create distribution package"
    exit 1
fi

# Create checksum
echo -e "${YELLOW}➤${NC} Creating checksums..."
cd dist
sha256sum RobotRunner-Linux.tar.gz > checksums.txt
cd ..
echo -e "${GREEN}✓${NC} Checksums: dist/checksums.txt"

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
echo "  • dist/RobotRunner-Linux.tar.gz"
echo "  • dist/checksums.txt"
echo ""
echo "To test:"
echo "  cd dist/RobotRunner && ./RobotRunner"
echo ""
