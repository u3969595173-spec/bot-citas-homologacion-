# Bot de Citas - Homologación Médica

Bot de Telegram que monitorea 24/7 la disponibilidad de citas de homologación de títulos médicos en España.

##  Despliegue en Render

### Variables de Entorno Requeridas

En el dashboard de Render, configura:

```
TELEGRAM_BOT_TOKEN=tu_token_aqui
ADMIN_USER_ID=tu_user_id_aqui
```

### Instrucciones

1. Conecta este repositorio a Render
2. Selecciona "Web Service"
3. Runtime: Python 3
4. Build Command: `pip install -r requirements.txt`
5. Start Command: `python main.py`
6. Configura las variables de entorno
7. Deploy!

##  Comandos del Bot

- `/start` - Iniciar bot y ver info
- `/datos` - Registrar datos personales
- `/registrar` - Activar monitoreo
- `/status` - Ver estado del monitor
- `/mistats` - Ver tus datos registrados
- `/admin` - Panel admin (solo admin)
- `/stop` - Detener monitoreo

##  Funcionamiento

- Monitorea la API cada 0.1 segundos (10 checks/segundo)
- Compatible con Windows y Linux
- Bypass SSL para servidor gubernamental
- Notificaciones instantáneas a usuarios registrados
- Panel de administración para completar reservas manualmente

##  Estructura

- `main.py` - Bot de Telegram principal
- `monitor.py` - Monitor de disponibilidad
- `http_client.py` - Cliente HTTP multiplataforma
- `user_data.py` - Gestión de datos de usuarios
- `config.py` - Configuración
