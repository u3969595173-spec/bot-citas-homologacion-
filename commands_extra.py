"""
Comandos adicionales para el bot
"""
import logging
from telegram import Update
from telegram.ext import ContextTypes

logger = logging.getLogger(__name__)

async def pausar_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Pausar monitoreo temporalmente"""
    from main import monitor, usuarios_activos
    
    user_id = update.effective_user.id
    
    if user_id not in usuarios_activos:
        await update.message.reply_text(' No tienes monitoreo activo.\nUsa /registrar para activarlo.')
        return
    
    # Pausar para este usuario
    usuarios_activos[user_id]['pausado'] = True
    
    await update.message.reply_text(
        ' **Monitoreo pausado**\n\n'
        'Tu monitoreo está temporalmente pausado.\n'
        'Usa /reanudar cuando quieras continuar.'
    )
    logger.info(f'Usuario {user_id} pausó monitoreo')

async def reanudar_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Reanudar monitoreo"""
    from main import monitor, usuarios_activos
    
    user_id = update.effective_user.id
    
    if user_id not in usuarios_activos:
        await update.message.reply_text(' No tienes monitoreo activo.\nUsa /registrar para activarlo.')
        return
    
    if not usuarios_activos[user_id].get('pausado', False):
        await update.message.reply_text('ℹ Tu monitoreo ya está activo.')
        return
    
    # Reanudar
    usuarios_activos[user_id]['pausado'] = False
    
    await update.message.reply_text(
        ' **Monitoreo reanudado**\n\n'
        ' Volviste al monitoreo activo.\n'
        'Te notificaré cuando haya citas disponibles.'
    )
    logger.info(f'Usuario {user_id} reanudó monitoreo')

async def test_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Probar notificación"""
    await update.message.reply_text(
        ' **Test de notificación**\n\n'
        ' Bot funcionando correctamente\n'
        ' Notificaciones activas\n\n'
        'Recibirás alertas como esta cuando haya citas.'
    )
    logger.info(f'Test de notificación para usuario {update.effective_user.id}')

async def stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Estadísticas del bot"""
    from main import monitor, usuarios_activos
    
    if not monitor:
        await update.message.reply_text(' Monitor no inicializado')
        return
    
    stats = monitor.get_stats()
    
    uptime_seconds = (datetime.now() - monitor.start_time).total_seconds() if hasattr(monitor, 'start_time') else 0
    uptime_hours = uptime_seconds / 3600
    
    texto = (
        f' **Estadísticas del Bot**\n\n'
        f' Estado: {"Activo" if monitor.running else "Inactivo"}\n'
        f' Checks realizados: {stats["checks_realizados"]}\n'
        f' Último check: {stats["last_check"]}\n'
        f' Intervalo actual: {stats["current_interval"]}s\n'
        f' Usuarios monitoreando: {len(usuarios_activos)}\n'
        f' Uptime: {uptime_hours:.1f}h\n\n'
        f' Bot ultra-rápido: ~20 checks/segundo'
    )
    
    await update.message.reply_text(texto, parse_mode='Markdown')


async def cola_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Ver posición en la cola"""
    from main import citas_queue
    
    user_id = update.effective_user.id
    position = citas_queue.get_position(user_id)
    stats = citas_queue.get_queue_stats()
    
    if position == -1:
        await update.message.reply_text(
            ' **Ya tienes cita asignada**\n\n'
            'Ya fuiste procesado y se te asignó una cita.\n'
            'Revisa tus mensajes anteriores.'
        )
    elif position == 0:
        await update.message.reply_text(
            ' **No estás en la cola**\n\n'
            f' Usuarios en espera: {stats["en_espera"]}\n'
            f' Usuarios procesados: {stats["procesados"]}\n\n'
            'Usa /registrar para unirte a la cola.'
        )
    else:
        await update.message.reply_text(
            f' **Tu posición en la cola: #{position}**\n\n'
            f' Total en espera: {stats["en_espera"]}\n'
            f' Ya procesados: {stats["procesados"]}\n\n'
            f' Serás el {"próximo" if position == 1 else f"{position}º"} en recibir cita.\n'
            'Cuando aparezca una cita, se te asignará automáticamente.'
        )
    
    logger.info(f'Usuario {user_id} consultó su posición: {position}')