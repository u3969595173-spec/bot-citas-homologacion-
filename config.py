# -*- coding: utf-8 -*-
"""
Configuración del Bot de Citas - Homologación Médicos
Compatible con variables de entorno para Render
"""

import os

# Telegram Bot Token (de variable de entorno o hardcoded)
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN', '8337512957:AAFcmCb8t14oDuwpzKG7-8Bh_S9Jxeyi1Uw')

# API Qmatic - URL base
QMATIC_BASE_URL = "https://citaprevia.ciencia.gob.es/qmaticwebbooking/rest"

# IDs de servicio y sucursal
BRANCH_ID = "7c2c5344f7ec051bc265995282e38698f770efab83ed9de0f9378d102f700630"
SERVICE_ID = "e97539664874283b583f0ff0b25d1e34f0f14e083d59fb10b2dafb76e4544019"
CUSTOM_SLOT_LENGTH = 10

# Configuración de monitoreo - MODO SNIPER
CHECK_INTERVAL_NORMAL = 0.005  # 200 checks/segundo (el doble de rápido)
CHECK_INTERVAL_TURBO = 0.005   # 200 checks/segundo constante
TURBO_START_HOUR = 0           # 24/7 modo turbo
TURBO_END_HOUR = 24

# Admin del bot (de variable de entorno o hardcoded)
ADMIN_USER_ID = int(os.getenv('ADMIN_USER_ID', '5901833301'))
