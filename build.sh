#!/usr/bin/env bash
# Build script para Render

set -e

echo "Instalando dependencias de Python..."
pip install --upgrade pip
pip install -r requirements.txt

echo "Instalando Playwright y navegadores..."
playwright install --with-deps chromium

echo "Build completado"

