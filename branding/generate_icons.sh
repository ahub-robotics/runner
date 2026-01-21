#!/bin/bash
# =================================================================
# Generate Icons for All Platforms
# =================================================================
# Convierte el logo principal a todos los formatos necesarios
# para Windows (.ico), macOS (.icns) y Linux (.png)
#
# Requisitos:
#   - ImageMagick: brew install imagemagick (macOS)
#   - iconutil (incluido en macOS)
#   - png2icns: npm install -g png2icns
# =================================================================

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
SOURCE_LOGO="$PROJECT_ROOT/static/images/logo.png"
OUTPUT_DIR="$SCRIPT_DIR/icons"

echo -e "${CYAN}═══════════════════════════════════════════════════════════${NC}"
echo -e "${CYAN}  📦 GENERADOR DE ICONOS MULTIPLATAFORMA${NC}"
echo -e "${CYAN}═══════════════════════════════════════════════════════════${NC}"
echo ""

# Verificar que existe el logo fuente
if [ ! -f "$SOURCE_LOGO" ]; then
    echo -e "${RED}❌ Logo fuente no encontrado: $SOURCE_LOGO${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Logo fuente: $SOURCE_LOGO${NC}"
echo ""

# Crear directorios
mkdir -p "$OUTPUT_DIR/temp"
mkdir -p "$OUTPUT_DIR/windows"
mkdir -p "$OUTPUT_DIR/macos"
mkdir -p "$OUTPUT_DIR/linux"

# =================================================================
# WINDOWS - .ico con múltiples resoluciones
# =================================================================
echo -e "${YELLOW}🪟  Generando iconos para Windows...${NC}"

# Verificar ImageMagick
if ! command -v convert &> /dev/null; then
    echo -e "${RED}❌ ImageMagick no instalado${NC}"
    echo -e "${YELLOW}   Instalar: brew install imagemagick${NC}"
    exit 1
fi

# Generar .ico con múltiples resoluciones (16, 32, 48, 64, 128, 256)
convert "$SOURCE_LOGO" \
    -background none \
    -resize 256x256 "$OUTPUT_DIR/temp/icon-256.png"

convert "$SOURCE_LOGO" \
    -background none \
    -resize 128x128 "$OUTPUT_DIR/temp/icon-128.png"

convert "$SOURCE_LOGO" \
    -background none \
    -resize 64x64 "$OUTPUT_DIR/temp/icon-64.png"

convert "$SOURCE_LOGO" \
    -background none \
    -resize 48x48 "$OUTPUT_DIR/temp/icon-48.png"

convert "$SOURCE_LOGO" \
    -background none \
    -resize 32x32 "$OUTPUT_DIR/temp/icon-32.png"

convert "$SOURCE_LOGO" \
    -background none \
    -resize 16x16 "$OUTPUT_DIR/temp/icon-16.png"

# Crear .ico con todas las resoluciones
convert "$OUTPUT_DIR/temp/icon-16.png" \
        "$OUTPUT_DIR/temp/icon-32.png" \
        "$OUTPUT_DIR/temp/icon-48.png" \
        "$OUTPUT_DIR/temp/icon-64.png" \
        "$OUTPUT_DIR/temp/icon-128.png" \
        "$OUTPUT_DIR/temp/icon-256.png" \
        "$OUTPUT_DIR/windows/app.ico"

echo -e "${GREEN}✅ Windows: app.ico (16x16 a 256x256)${NC}"

# Copiar también a resources para PyInstaller
cp "$OUTPUT_DIR/windows/app.ico" "$PROJECT_ROOT/resources/logo.ico"
echo -e "${GREEN}✅ Copiado a resources/logo.ico${NC}"

# =================================================================
# macOS - .icns
# =================================================================
echo ""
echo -e "${YELLOW}🍎  Generando iconos para macOS...${NC}"

# Crear iconset directory
ICONSET_DIR="$OUTPUT_DIR/temp/app.iconset"
mkdir -p "$ICONSET_DIR"

# Generar todas las resoluciones requeridas para macOS
convert "$SOURCE_LOGO" -resize 16x16     "$ICONSET_DIR/icon_16x16.png"
convert "$SOURCE_LOGO" -resize 32x32     "$ICONSET_DIR/icon_16x16@2x.png"
convert "$SOURCE_LOGO" -resize 32x32     "$ICONSET_DIR/icon_32x32.png"
convert "$SOURCE_LOGO" -resize 64x64     "$ICONSET_DIR/icon_32x32@2x.png"
convert "$SOURCE_LOGO" -resize 128x128   "$ICONSET_DIR/icon_128x128.png"
convert "$SOURCE_LOGO" -resize 256x256   "$ICONSET_DIR/icon_128x128@2x.png"
convert "$SOURCE_LOGO" -resize 256x256   "$ICONSET_DIR/icon_256x256.png"
convert "$SOURCE_LOGO" -resize 512x512   "$ICONSET_DIR/icon_256x256@2x.png"
convert "$SOURCE_LOGO" -resize 512x512   "$ICONSET_DIR/icon_512x512.png"
convert "$SOURCE_LOGO" -resize 1024x1024 "$ICONSET_DIR/icon_512x512@2x.png"

# Convertir iconset a .icns usando iconutil (nativo de macOS)
iconutil -c icns "$ICONSET_DIR" -o "$OUTPUT_DIR/macos/app.icns"

echo -e "${GREEN}✅ macOS: app.icns (16x16 a 1024x1024 con @2x)${NC}"

# Copiar también a resources
cp "$OUTPUT_DIR/macos/app.icns" "$PROJECT_ROOT/resources/logo.icns"
echo -e "${GREEN}✅ Copiado a resources/logo.icns${NC}"

# =================================================================
# LINUX - PNG en múltiples resoluciones
# =================================================================
echo ""
echo -e "${YELLOW}🐧  Generando iconos para Linux...${NC}"

# Resoluciones estándar de Linux
for size in 16 32 48 64 128 256 512; do
    convert "$SOURCE_LOGO" \
        -resize ${size}x${size} \
        "$OUTPUT_DIR/linux/app-${size}.png"
    echo -e "${GREEN}✅ Linux: app-${size}.png${NC}"
done

# Copiar el de mayor resolución como icon principal
cp "$OUTPUT_DIR/linux/app-256.png" "$OUTPUT_DIR/linux/app.png"
echo -e "${GREEN}✅ Linux: app.png (256x256 por defecto)${NC}"

# =================================================================
# LIMPIAR TEMPORALES
# =================================================================
echo ""
echo -e "${YELLOW}🧹 Limpiando archivos temporales...${NC}"
rm -rf "$OUTPUT_DIR/temp"
echo -e "${GREEN}✅ Limpieza completada${NC}"

# =================================================================
# RESUMEN
# =================================================================
echo ""
echo -e "${CYAN}═══════════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}  ✅ ICONOS GENERADOS EXITOSAMENTE${NC}"
echo -e "${CYAN}═══════════════════════════════════════════════════════════${NC}"
echo ""
echo -e "${CYAN}📂 Archivos generados:${NC}"
echo ""
echo -e "${YELLOW}Windows:${NC}"
echo "   • $OUTPUT_DIR/windows/app.ico"
echo "   • resources/logo.ico (PyInstaller)"
echo ""
echo -e "${YELLOW}macOS:${NC}"
echo "   • $OUTPUT_DIR/macos/app.icns"
echo "   • resources/logo.icns (PyInstaller)"
echo ""
echo -e "${YELLOW}Linux:${NC}"
echo "   • $OUTPUT_DIR/linux/app.png (256x256)"
echo "   • $OUTPUT_DIR/linux/app-{16,32,48,64,128,256,512}.png"
echo ""
echo -e "${CYAN}📝 Tamaños totales:${NC}"
du -sh "$OUTPUT_DIR/windows" "$OUTPUT_DIR/macos" "$OUTPUT_DIR/linux"
echo ""