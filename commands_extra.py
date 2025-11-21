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

async def confirmar_cita_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Usuario confirma que ya consiguió cita y sale de la cola"""
    from main import citas_queue, usuarios_activos
    
    user_id = update.effective_user.id
    position = citas_queue.get_position(user_id)
    
    if position == -1:
        await update.message.reply_text(
            ' **Ya estabas marcado como procesado**\n\n'
            'Tu cita ya fue confirmada anteriormente.'
        )
        return
    
    if position == 0:
        await update.message.reply_text(
            ' **No estás en la cola**\n\n'
            'No tienes monitoreo activo.\n'
            'Si ya conseguiste cita por otro medio, ¡felicidades! '
        )
        return
    
    # Remover de la cola
    removed = citas_queue.remove_user(user_id)
    
    if removed:
        # Marcar como procesado manualmente
        citas_queue.mark_processed(user_id, 'Confirmada manualmente')
        
        # Remover de usuarios activos
        if user_id in usuarios_activos:
            del usuarios_activos[user_id]
        
        stats = citas_queue.get_queue_stats()
        
        await update.message.reply_text(
            ' **¡Felicidades por tu cita!**\n\n'
            ' Has sido removido de la cola\n'
            ' Tu monitoreo ha sido desactivado\n\n'
            f' Usuarios restantes en cola: {stats["en_espera"]}\n\n'
            '¡Buena suerte con tu homologación! '
        )
        
        # Notificar al admin
        from config import ADMIN_USER_ID
        from main import application
        
        if ADMIN_USER_ID:
            try:
                await application.bot.send_message(
                    chat_id=ADMIN_USER_ID,
                    text=f'ℹ **Usuario confirmó cita**\n\n'
                         f' User ID: {user_id}\n'
                         f' Removido de cola (era #{position})\n'
                         f' Cola actual: {stats["en_espera"]} usuarios'
                )
            except:
                pass
        
        logger.info(f'Usuario {user_id} confirmó cita y salió de cola (era #{position})')
    else:
        await update.message.reply_text(
            ' Error al remover de la cola.\n'
            'Intenta de nuevo o contacta al admin.'
        )


async def cancelar_cola_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Usuario cancela su participación en la cola"""
    from main import citas_queue, usuarios_activos
    
    user_id = update.effective_user.id
    position = citas_queue.get_position(user_id)
    
    if position <= 0:
        await update.message.reply_text(
            ' **No estás en la cola**\n\n'
            'No tienes monitoreo activo.'
        )
        return
    
    # Remover de la cola
    removed = citas_queue.remove_user(user_id)
    
    if removed:
        # Remover de usuarios activos
        if user_id in usuarios_activos:
            del usuarios_activos[user_id]
        
        stats = citas_queue.get_queue_stats()
        
        await update.message.reply_text(
            ' **Cancelado exitosamente**\n\n'
            f'Has sido removido de la cola (eras #{position})\n'
            f'Tu monitoreo ha sido desactivado\n\n'
            f' Usuarios restantes: {stats["en_espera"]}\n\n'
            'Puedes volver a registrarte cuando quieras con /registrar'
        )
        
        logger.info(f'Usuario {user_id} canceló participación en cola (era #{position})')
    else:
        await update.message.reply_text(' Error al cancelar. Intenta de nuevo.')