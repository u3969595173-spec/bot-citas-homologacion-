"""
Tarea programada para confirmación diaria
"""
import asyncio
import logging
from datetime import datetime, time

logger = logging.getLogger(__name__)

async def daily_heartbeat(application):
    """Enviar mensaje diario confirmando que el bot está vivo"""
    from config import ADMIN_USER_ID
    
    while True:
        try:
            # Esperar hasta las 9:00 AM
            now = datetime.now()
            target_time = datetime.combine(now.date(), time(9, 0))
            
            if now > target_time:
                # Si ya pasó, programar para mañana
                target_time = datetime.combine(now.date(), time(9, 0))
                target_time = target_time.replace(day=target_time.day + 1)
            
            wait_seconds = (target_time - now).total_seconds()
            await asyncio.sleep(wait_seconds)
            
            # Enviar heartbeat
            if ADMIN_USER_ID:
                await application.bot.send_message(
                    chat_id=ADMIN_USER_ID,
                    text=' **Bot activo - Confirmación diaria**\n\n'
                         ' Sistema funcionando correctamente\n'
                         ' Monitoreo 24/7 activo\n'
                         f' {datetime.now().strftime("%d/%m/%Y %H:%M")}'
                )
                logger.info('Heartbeat diario enviado')
        
        except Exception as e:
            logger.error(f'Error en heartbeat diario: {e}')
            await asyncio.sleep(3600)  # Reintentar en 1 hora
