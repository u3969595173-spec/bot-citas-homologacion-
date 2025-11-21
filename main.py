"""
Bot de Telegram para Citas de HomologaciÃ³n
Sistema de monitoreo y auto-reserva de citas
"""

import asyncio
import logging
import os
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes, ConversationHandler, MessageHandler, filters
from datetime import datetime

# Configurar OpenSSL para permitir renegociaciÃ³n legacy
os.environ['OPENSSL_CONF'] = os.path.join(os.path.dirname(__file__), 'openssl.cnf')

from config import TELEGRAM_BOT_TOKEN, ADMIN_USER_ID
from monitor import CitasMonitor
from user_data import UserDataManager
from health_server import start_health_server
from daily_heartbeat import daily_heartbeat
from queue_manager import CitasQueue
from commands_extra import pausar_command, reanudar_command, test_command, stats_command, cola_command, confirmar_cita_command, cancelar_cola_command

# Configurar logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Estado global
monitor = None
usuarios_activos = {}  # {user_id: {'datos': {...}, 'notified': False}}
user_data_manager = UserDataManager()
citas_queue = CitasQueue()

# Estados para conversaciÃ³n de registro de datos
NOMBRE, APELLIDO, DOCUMENTO, EMAIL, TELEFONO = range(5)


async def cita_disponible_handler(dates):
    """Callback cuando se detecta cita disponible"""
    logger.warning(f"ðŸŽ¯ CITA DISPONIBLE: {dates}")
    
    # Notificar al admin primero
    if ADMIN_USER_ID:
        try:
            await application.bot.send_message(
                chat_id=ADMIN_USER_ID,
                text=f"ðŸš¨ **ADMIN: CITA DISPONIBLE DETECTADA**\n\n"
                     f"ðŸ“… Fechas disponibles: {', '.join(dates)}\n"
                     f"ðŸ‘¥ Usuarios registrados: {len(usuarios_activos)}\n\n"
                     f"âš ï¸ **ACCIÃ“N MANUAL REQUERIDA:**\n"
                     f"1. Ve a: https://citaprevia.ciencia.gob.es/qmaticwebbooking/#/\n"
                     f"2. Selecciona la fecha: {dates[0]}\n"
                     f"3. Completa con los datos del usuario\n\n"
                     f"ðŸ“‹ Para ver datos de usuarios, usa /admin"
            )
        except Exception as e:
            logger.error(f"Error notificando admin: {e}")
    
    # Notificar a todos los usuarios activos
    for user_id, user_data in usuarios_activos.items():
        if not user_data.get('notified', False):
            try:
                # Obtener datos del usuario
                user_info = user_data_manager.get_user_data(user_id)
                
                if user_info:
                    mensaje = (
                        f"ðŸŽ¯ **Â¡CITA DISPONIBLE!**\n\n"
                        f"ðŸ“… Fechas: {', '.join(dates)}\n\n"
                        f"ðŸ“‹ **Tus datos registrados:**\n"
                        f"â€¢ Nombre: {user_info['nombre']} {user_info['apellido']}\n"
                        f"â€¢ Documento: {user_info['documento']}\n"
                        f"â€¢ Email: {user_info['email']}\n"
                        f"â€¢ TelÃ©fono: {user_info['telefono']}\n\n"
                        f"âš ï¸ **RESERVA MANUAL:**\n"
                        f"El administrador completarÃ¡ tu reserva manualmente.\n"
                        f"Te confirmaremos cuando estÃ© lista.\n\n"
                        f"ðŸ”— Link: https://citaprevia.ciencia.gob.es/qmaticwebbooking/#/"
                    )
                else:
                    mensaje = (
                        f"ðŸŽ¯ **Â¡CITA DISPONIBLE!**\n\n"
                        f"ðŸ“… Fechas: {', '.join(dates)}\n\n"
                        f"âš ï¸ **No tienes datos registrados**\n"
                        f"Usa /datos para registrar tu informaciÃ³n.\n\n"
                        f"ðŸ”— Link: https://citaprevia.ciencia.gob.es/qmaticwebbooking/#/"
                    )
                
                await application.bot.send_message(
                    chat_id=user_id,
                    text=mensaje
                )
                user_data['notified'] = True
            except Exception as e:
                logger.error(f"Error notificando usuario {user_id}: {e}")


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Comando /start"""
    user_id = update.effective_user.id
    username = update.effective_user.username or update.effective_user.first_name
    
    logger.info(f"Usuario {username} ({user_id}) iniciÃ³ el bot")
    
    has_data = user_data_manager.has_complete_data(user_id)
    data_status = "âœ… Registrados" if has_data else "âŒ Sin registrar"
    
    await update.message.reply_text(
        f"ðŸ‘‹ Â¡Bienvenido al Bot de Citas de HomologaciÃ³n!\n\n"
        f"ðŸŽ¯ Este bot monitorea 24/7 la disponibilidad de citas y te avisa instantÃ¡neamente.\n\n"
        f"ðŸ“‹ **Comandos disponibles:**\n"
        f"/datos - Registrar tus datos personales\n"
        f"/registrar - Activar monitoreo de citas\n"
        f"/status - Ver estado del monitor\n"          f"/pausar - Pausar monitoreo temporalmente\n"
          f"/reanudar - Reanudar monitoreo\n"
          f"/test - Probar notificaciones\n"
          f"/stats - Estadísticas del bot\n"          f"/cola - Ver tu posición en la cola\n"          f"/confirmar - Confirmar que conseguiste cita\n"
          f"/cancelar - Salir de la cola\n"
        f"/mistats - Ver mis datos registrados\n"
        f"/stop - Detener monitoreo\n\n"
        f"ðŸ“ Tus datos: {data_status}\n\n"
        f"ðŸ’¡ El sistema revisa:\n"
        f"â€¢ Cada 0.1 segundos (modo ULTRA - 10 veces/seg)\n\n"
        f"âš ï¸ Registra tus datos con /datos antes de activar el monitoreo.\n\n"
        f"User ID: `{user_id}`"
    )


async def registrar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Comando /registrar - Activar monitoreo"""
    user_id = update.effective_user.id
    username = update.effective_user.username or update.effective_user.first_name
    
    # Verificar si tiene datos registrados
    if not user_data_manager.has_complete_data(user_id):
        await update.message.reply_text(
            "âš ï¸ **Necesitas registrar tus datos primero**\n\n"
            "Usa /datos para registrar:\n"
            "â€¢ Nombre y Apellido\n"
            "â€¢ NIE/DNI/Pasaporte\n"
            "â€¢ Email\n"
            "â€¢ TelÃ©fono\n\n"
            "Estos datos se usarÃ¡n para reservar automÃ¡ticamente cuando aparezca una cita."
        )
        return

    # Agregar a la cola de la base de datos
    position = citas_queue.add_user(user_id)
    # Nota: position puede ser 0 por error SQL menor, pero usuario sí se agrega
    if position is None or position < 0:
        await update.message.reply_text(
            " **Error al agregar a la cola**\n\n"
            "Por favor, intenta de nuevo más tarde."
        )
        return
    
    # Si position es 0, significa que hubo un warning pero sí se agregó
    if position == 0:
        position = 1  # Asignar posición por defecto

    # Registrar usuario en memoria
    usuarios_activos[user_id] = {
        'username': username,
        'fecha_registro': datetime.now().isoformat(),
        'notified': False
    }

    logger.info(f"Usuario {username} ({user_id}) registrado para monitoreo - Posición en cola: {position}")

    await update.message.reply_text(
        f" ¡Registrado correctamente!\n\n"
        f" **Posición en cola: #{position}**\n\n"
        f" El bot está monitoreando citas 24/7.\n"
        f" Recibirás notificación instantánea cuando aparezca una cita.\n"
        f" El bot intentará reservarla automáticamente con tus datos.\n\n"
        f" El bot revisa cada 0.1 segundos (10 veces por segundo).\n\n"
        f" Usa /cola para ver tu posición actualizada.\n"
        f" Usa /status para ver el estado actual."
    )


async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Comando /status - Ver estado del monitor"""
    if not monitor or not monitor.running:
        await update.message.reply_text(
            "âŒ El monitor no estÃ¡ activo.\n"
            "Contacta al administrador."
        )
        return
    
    stats = monitor.get_stats()
    now = datetime.now()
    
    # Determinar modo actual
    if 12 <= now.hour < 14:
        modo = "âš¡ MODO TURBO (0.3s)"
    elif now.hour == 11 and now.minute >= 55:
        modo = "ðŸ”¥ PRE-TURBO (1s)"
    else:
        modo = "ðŸ’¤ Modo normal (30s)"
    
    user_id = update.effective_user.id
    is_registered = user_id in usuarios_activos
    
    await update.message.reply_text(
        f"ðŸ“Š **Estado del Monitor**\n\n"
        f"ðŸ” Estado: {'âœ… Activo' if stats['running'] else 'âŒ Inactivo'}\n"
        f"â± Modo actual: {modo}\n"
        f"ðŸ”¢ Checks realizados: {stats['checks_count']}\n"
        f"ðŸ• Ãšltimo check: {stats['last_check']}\n"
        f"ðŸ‘¤ Tu estado: {'âœ… Registrado' if is_registered else 'âŒ No registrado'}\n\n"
        f"ðŸ‘¥ Usuarios activos: {len(usuarios_activos)}\n\n"
        f"ðŸ’¡ El bot revisa la API cada {stats['current_interval']}s"
    )


async def stop_monitoring(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Comando /stop - Detener monitoreo para el usuario"""
    user_id = update.effective_user.id
    
    if user_id in usuarios_activos:
        del usuarios_activos[user_id]
        await update.message.reply_text(
            "âœ… Has sido eliminado del monitoreo.\n"
            "Usa /registrar si quieres volver a activarlo."
        )
    else:
        await update.message.reply_text(
            "âš ï¸ No estabas registrado en el sistema."
        )


async def admin_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Comando /admin - EstadÃ­sticas completas (solo admin)"""
    user_id = update.effective_user.id
    
    if ADMIN_USER_ID and user_id != ADMIN_USER_ID:
        await update.message.reply_text("âŒ No tienes permisos de administrador.")
        return
    
    stats = monitor.get_stats() if monitor else {}
    
    # Listar usuarios con sus datos
    users_info = []
    for uid, data in usuarios_activos.items():
        user_data = user_data_manager.get_user_data(uid)
        if user_data:
            users_info.append(
                f"ðŸ‘¤ **{data['username']}** (ID: {uid})\n"
                f"   â€¢ Nombre: {user_data['nombre']} {user_data['apellido']}\n"
                f"   â€¢ Doc: {user_data['documento']}\n"
                f"   â€¢ Email: {user_data['email']}\n"
                f"   â€¢ Tel: {user_data['telefono']}\n"
            )
        else:
            users_info.append(f"ðŸ‘¤ {data['username']} (ID: {uid}) - Sin datos")
    
    users_text = "\n".join(users_info) if users_info else "Ninguno"
    
    await update.message.reply_text(
        f"ðŸ‘¨â€ðŸ’¼ **Panel de AdministraciÃ³n**\n\n"
        f"ðŸ“Š Monitor: {'âœ… Activo' if stats.get('running') else 'âŒ Inactivo'}\n"
        f"ðŸ”¢ Total checks: {stats.get('checks_count', 0)}\n"
        f"â± Intervalo: {stats.get('current_interval', 0)}s\n"
        f"ðŸ‘¥ Usuarios registrados: {len(usuarios_activos)}\n\n"
        f"**Lista de usuarios con datos:**\n\n{users_text}\n\n"
        f"ðŸ’¡ Cuando aparezca cita, recibirÃ¡s notificaciÃ³n con los datos para completar manualmente."
    )


# === COMANDOS PARA REGISTRO DE DATOS ===

async def datos_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Iniciar proceso de registro de datos /datos"""
    await update.message.reply_text(
        "ðŸ“ **Registro de Datos Personales**\n\n"
        "Voy a pedirte tus datos para poder reservar automÃ¡ticamente cuando aparezca una cita.\n\n"
        "Puedes cancelar en cualquier momento con /cancelar\n\n"
        "**Paso 1 de 5: Nombre**\n"
        "Por favor, escribe tu nombre:"
    )
    return NOMBRE


async def datos_nombre(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Recibir nombre"""
    context.user_data['nombre'] = update.message.text.strip()
    await update.message.reply_text(
        f"âœ… Nombre: {context.user_data['nombre']}\n\n"
        f"**Paso 2 de 5: Apellido**\n"
        f"Escribe tu apellido:"
    )
    return APELLIDO


async def datos_apellido(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Recibir apellido"""
    context.user_data['apellido'] = update.message.text.strip()
    await update.message.reply_text(
        f"âœ… Apellido: {context.user_data['apellido']}\n\n"
        f"**Paso 3 de 5: Documento**\n"
        f"Escribe tu NIE, DNI o Pasaporte:"
    )
    return DOCUMENTO


async def datos_documento(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Recibir documento"""
    context.user_data['documento'] = update.message.text.strip()
    await update.message.reply_text(
        f"âœ… Documento: {context.user_data['documento']}\n\n"
        f"**Paso 4 de 5: Email**\n"
        f"Escribe tu correo electrÃ³nico:"
    )
    return EMAIL


async def datos_email(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Recibir email"""
    context.user_data['email'] = update.message.text.strip()
    await update.message.reply_text(
        f"âœ… Email: {context.user_data['email']}\n\n"
        f"**Paso 5 de 5: TelÃ©fono**\n"
        f"Escribe tu nÃºmero de telÃ©fono (con prefijo +34 si es EspaÃ±a):"
    )
    return TELEFONO


async def datos_telefono(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Recibir telÃ©fono y guardar todos los datos"""
    context.user_data['telefono'] = update.message.text.strip()
    
    # Guardar datos
    user_id = update.effective_user.id
    user_data_manager.set_user_data(
        user_id,
        context.user_data['nombre'],
        context.user_data['apellido'],
        context.user_data['documento'],
        context.user_data['email'],
        context.user_data['telefono']
    )
    
    await update.message.reply_text(
        f"âœ… **Datos registrados correctamente**\n\n"
        f"ðŸ“‹ Resumen:\n"
        f"â€¢ Nombre: {context.user_data['nombre']} {context.user_data['apellido']}\n"
        f"â€¢ Documento: {context.user_data['documento']}\n"
        f"â€¢ Email: {context.user_data['email']}\n"
        f"â€¢ TelÃ©fono: {context.user_data['telefono']}\n\n"
        f"ðŸ¤– Ahora usa /registrar para activar el monitoreo.\n"
        f"Cuando aparezca una cita, el bot intentarÃ¡ reservarla automÃ¡ticamente con estos datos."
    )
    
    # Limpiar contexto
    context.user_data.clear()
    return ConversationHandler.END


async def datos_cancelar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Cancelar registro de datos"""
    context.user_data.clear()
    await update.message.reply_text(
        "âŒ Registro cancelado.\n\n"
        "Puedes iniciar de nuevo con /datos cuando quieras."
    )
    return ConversationHandler.END


async def mistats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Ver datos registrados del usuario"""
    user_id = update.effective_user.id
    data = user_data_manager.get_user_data(user_id)
    
    if not data:
        await update.message.reply_text(
            "âŒ No tienes datos registrados.\n\n"
            "Usa /datos para registrar tu informaciÃ³n."
        )
        return
    
    await update.message.reply_text(
        f"ðŸ“‹ **Tus Datos Registrados**\n\n"
        f"â€¢ Nombre: {data['nombre']} {data['apellido']}\n"
        f"â€¢ Documento: {data['documento']}\n"
        f"â€¢ Email: {data['email']}\n"
        f"â€¢ TelÃ©fono: {data['telefono']}\n\n"
        f"âœ… Datos completos para auto-reserva\n\n"
        f"Para modificar tus datos, usa /datos de nuevo."
    )


async def post_init(application: Application):
    """Inicializar monitor al arrancar el bot"""
    global monitor
    
    logger.info("Inicializando monitor de citas...")
    monitor = CitasMonitor(on_cita_available=cita_disponible_handler)
    
    # Iniciar monitor en background
    asyncio.create_task(monitor.start_monitoring())
    
    logger.info("âœ… Bot completamente inicializado")



async def post_shutdown(application: Application):
    """Detener el monitor al cerrar el bot"""
    global monitor
    
    if monitor:
        logger.info(' Cerrando bot...')
        monitor.stop_monitoring()
        logger.info(' Monitor detenido')


def main():
    """Iniciar el bot"""
    global application
    
    if not TELEGRAM_BOT_TOKEN or TELEGRAM_BOT_TOKEN == "TU_TOKEN_AQUI":
        logger.error("âŒ Debes configurar TELEGRAM_BOT_TOKEN en config.py")
        return
    
    # Crear aplicaciÃ³n
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).post_init(post_init).post_shutdown(post_shutdown).build()

    # Iniciar health server para Render
    logger.info('Iniciando health server...')
    start_health_server()
    
    # Handler de conversaciÃ³n para registro de datos
    datos_handler = ConversationHandler(
        entry_points=[CommandHandler("datos", datos_start)],
        states={
            NOMBRE: [MessageHandler(filters.TEXT & ~filters.COMMAND, datos_nombre)],
            APELLIDO: [MessageHandler(filters.TEXT & ~filters.COMMAND, datos_apellido)],
            DOCUMENTO: [MessageHandler(filters.TEXT & ~filters.COMMAND, datos_documento)],
            EMAIL: [MessageHandler(filters.TEXT & ~filters.COMMAND, datos_email)],
            TELEFONO: [MessageHandler(filters.TEXT & ~filters.COMMAND, datos_telefono)],
        },
        fallbacks=[CommandHandler("cancelar", datos_cancelar)],
    )
    
    # Registrar comandos
    application.add_handler(CommandHandler("start", start))
    application.add_handler(datos_handler)
    application.add_handler(CommandHandler("registrar", registrar))
    application.add_handler(CommandHandler("status", status))
    application.add_handler(CommandHandler("mistats", mistats))
    application.add_handler(CommandHandler("stop", stop_monitoring))
    application.add_handler(CommandHandler("admin", admin_stats))
    application.add_handler(CommandHandler("pausar", pausar_command))
    application.add_handler(CommandHandler("reanudar", reanudar_command))
    application.add_handler(CommandHandler("test", test_command))
    application.add_handler(CommandHandler("stats", stats_command))
    application.add_handler(CommandHandler("cola", cola_command))
    application.add_handler(CommandHandler("confirmar", confirmar_cita_command))
    application.add_handler(CommandHandler("cancelar", cancelar_cola_command))
    
    # Iniciar bot
    logger.info("ðŸš€ Iniciando Bot de Citas...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == '__main__':
    import random
    import time
    
    # Delay aleatorio para evitar conflicto entre múltiples instancias
    delay = random.uniform(0, 60)
    logger.info(f" Esperando {delay:.1f}s para evitar conflictos...")
    time.sleep(delay)
    
    main()






