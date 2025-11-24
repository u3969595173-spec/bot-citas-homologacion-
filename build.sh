#!/usr/bin/env bash
# Build script para Render

set -e

echo "Instalando dependencias de Python..."
pip install --upgrade pip
pip install -r requirements.txt

echo "Instalando navegadores de Playwright..."
playwright install chromium

echo "Instalando dependencias de sistema para Playwright..."
playwright install-deps chromium

echo "Build completado exitosamente"

