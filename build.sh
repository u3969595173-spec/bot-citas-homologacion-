#!/usr/bin/env bash
# Build script para Render

echo " Instalando dependencias del sistema..."
apt-get update
apt-get install -y libpq-dev gcc

echo " Instalando dependencias de Python..."
pip install --upgrade pip
pip install -r requirements.txt

echo " Build completado"
