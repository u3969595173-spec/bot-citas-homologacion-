#!/usr/bin/env bash
# Build script para Render

echo " Instalando dependencias del sistema..."
apt-get update
apt-get install -y libpq-dev gcc

echo " Instalando dependencias para navegador headless..."
apt-get install -y \
    libnss3 libnspr4 libatk1.0-0 libatk-bridge2.0-0 \
    libcups2 libdrm2 libdbus-1-3 libxkbcommon0 \
    libxcomposite1 libxdamage1 libxfixes3 libxrandr2 \
    libgbm1 libpango-1.0-0 libcairo2 libasound2 \
    libatspi2.0-0 libxshmfence1

echo " Instalando dependencias de Python..."
pip install --upgrade pip
pip install -r requirements.txt

echo " Instalando navegador Chromium para Playwright..."
python -m playwright install chromium

echo " Build completado"

