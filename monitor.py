# -*- coding: utf-8 -*-
"""
Monitor de disponibilidad de citas - API Qmatic
"""

import asyncio
from datetime import datetime
import logging
from http_client import HTTPClient
from config import *

logger = logging.getLogger(__name__)


class CitasMonitor:
    def __init__(self, on_cita_available):
        """
        on_cita_available: callback cuando se detecta cita disponible
        """
        self.client = HTTPClient()
        self.running = False
        self.on_cita_available = on_cita_available
        self.last_check = None
        self.checks_count = 0
        
    async def check_availability(self):
        """Revisar si hay fechas disponibles usando PowerShell"""
        url = f"{QMATIC_BASE_URL}/schedule/branches/{BRANCH_ID}/dates;servicePublicId={SERVICE_ID};customSlotLength={CUSTOM_SLOT_LENGTH}"
        
        try:
            # Ejecutar peticiÃ³n en thread separado para no bloquear
            dates = await asyncio.to_thread(self.client.get, url)
            
            self.last_check = datetime.now()
            self.checks_count += 1
            
            if dates and len(dates) > 0:
                logger.info(f"ðŸŽ¯ CITAS DISPONIBLES: {dates}")
                return dates
            else:
                if self.checks_count % 100 == 0:  # Log cada 100 checks
                    logger.info(f"âœ“ Check #{self.checks_count} - Sin citas disponibles")
                return []
                
        except Exception as e:
            logger.error(f"Error al revisar disponibilidad: {e}")
            return []
    
    def get_check_interval(self):
        """Determinar intervalo segÃºn hora del dÃ­a"""
        now = datetime.now()
        
        # Modo TURBO de 12:00 a 14:00
        if TURBO_START_HOUR <= now.hour < TURBO_END_HOUR:
            return CHECK_INTERVAL_TURBO
        
        # Pre-activaciÃ³n: 5 minutos antes del horario
        if now.hour == TURBO_START_HOUR - 1 and now.minute >= 55:
            return 1.0  # Revisar cada segundo
        
        # Resto del dÃ­a: modo normal
        return CHECK_INTERVAL_NORMAL
    
    async def start_monitoring(self):
        """Iniciar monitoreo continuo"""
        self.running = True
        logger.info(" Monitor de citas iniciado")
        
        while self.running:
            try:
                # Revisar disponibilidad
                dates = await self.check_availability()
                
                # Si hay citas disponibles, notificar
                if dates:
                    await self.on_cita_available(dates)
                
                # Esperar segÃºn el intervalo
                interval = self.get_check_interval()
                
                # Informar cambio de modo
                now = datetime.now()
                if now.hour == TURBO_START_HOUR and now.minute == 0 and now.second < 5:
                    logger.warning(f"âš¡ MODO TURBO ACTIVADO - Revisando cada {interval}s")
                elif now.hour == TURBO_END_HOUR and now.minute == 0 and now.second < 5:
                    logger.info(f"ðŸ’¤ Modo normal - Revisando cada {interval}s")
                
                await asyncio.sleep(interval)
                
            except Exception as e:
                logger.error(f"Error en loop de monitoreo: {e}")
                await asyncio.sleep(5)
    
    def stop_monitoring(self):
        """Detener monitoreo"""
        self.running = False
        logger.info("Monitor de citas detenido")
    
    def get_stats(self):
        """Obtener estadÃ­sticas del monitor"""
        return {
            'running': self.running,
            'checks_count': self.checks_count,
            'last_check': self.last_check.strftime('%H:%M:%S') if self.last_check else 'Nunca',
            'current_interval': self.get_check_interval()
        }

