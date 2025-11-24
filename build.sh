#!/usr/bin/env bash
# Build script para Render

set -e

echo "Instalando dependencias de Python..."
pip install --upgrade pip
pip install -r requirements.txt

echo "Instalando Playwright chromium..."
playwright install chromium chromium-headless-shell

echo "Build completado"

