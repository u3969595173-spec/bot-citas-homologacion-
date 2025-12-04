"""
Auto-llenado HTTP ULTRA-RÁPIDO usando httpx nativo
Versión optimizada para competir con otros bots
"""

import httpx
import asyncio
import logging
from typing import Dict, Optional

logger = logging.getLogger(__name__)

class FastHTTPAutoFiller:
    """Auto-llenador ultra-rápido con httpx"""
    
    def __init__(self):
        self.base_url = "https://citaprevia.ciencia.gob.es/qmaticwebbooking/rest/schedule"
        self.service_id = "e97539664874283b583f0ff0b25d1e34f0f14e083d59fb10b2dafb76e4544019"
        self.branch_id = "7c2c5344f7ec051bc265995282e38698f770efab83ed9de0f9378d102f700630"
        self.custom_slot_length = 10
        
        # Cliente HTTP reutilizable (conexión persistente) - PRE-CALENTADO
        self.client = httpx.AsyncClient(
            timeout=httpx.Timeout(0.4, connect=0.1),  # ⚡ TIMEOUTS MÍNIMOS (NUCLEAR)
            limits=httpx.Limits(max_keepalive_connections=100, max_connections=200),
            http2=False,  # HTTP/1.1 más rápido para peticiones simples
            verify=False  # Sin verificar SSL para máxima velocidad
        )
        self._warmed_up = False
        self._payload_cache = {}  # Cache de payloads pre-generados
    
    async def warmup(self):
        """PRE-CALENTAR conexión (DNS + SSL handshake) ANTES de que aparezca cita"""
        if self._warmed_up:
            return
        
        try:
            logger.info("🔥 PRE-CALENTANDO conexión HTTP...")
            # Hacer petición dummy para establecer conexión TCP + SSL
            url = f"{self.base_url}/branches/{self.branch_id}/services"
            await self.client.get(url)
            self._warmed_up = True
            logger.info("✅ Conexión PRE-CALENTADA (DNS + SSL listos)")
        except Exception as e:
            logger.warning(f"⚠️ Error pre-calentando: {e}")
    
    async def close(self):
        """Cerrar cliente HTTP"""
        await self.client.aclose()
    
    async def fill_appointment(self, user_data: Dict, available_date: str, time_slot: str = None) -> Dict:
        """
        Reservar cita de forma ultra-rápida
        
        Args:
            user_data: Datos del usuario
            available_date: Fecha en formato YYYY-MM-DD
            time_slot: Hora específica (opcional, si no se pasa intenta obtener)
            
        Returns:
            Dict con resultado
        """
        try:
            # Asegurar conexión pre-calentada
            await self.warmup()
            
            logger.info(f"⚡ RESERVA ULTRA-RÁPIDA para {user_data.get('nombre', 'Usuario')}")
            
            # Si no hay hora específica, intentar con horarios comunes primero
            if not time_slot:
                # INTENTO 1: NUCLEAR-SHOTGUN - Intentar 72 horarios EN PARALELO (cada 5 min) 🔥
                common_times = ["08:00", "08:05", "08:10", "08:15", "08:20", "08:25", "08:30", "08:35", "08:40", "08:45", "08:50", "08:55",
                               "09:00", "09:05", "09:10", "09:15", "09:20", "09:25", "09:30", "09:35", "09:40", "09:45", "09:50", "09:55",
                               "10:00", "10:05", "10:10", "10:15", "10:20", "10:25", "10:30", "10:35", "10:40", "10:45", "10:50", "10:55",
                               "11:00", "11:05", "11:10", "11:15", "11:20", "11:25", "11:30", "11:35", "11:40", "11:45", "11:50", "11:55",
                               "12:00", "12:05", "12:10", "12:15", "12:20", "12:25", "12:30", "12:35", "12:40", "12:45", "12:50", "12:55",
                               "13:00", "13:05", "13:10", "13:15", "13:20", "13:25", "13:30", "13:35", "13:40", "13:45", "13:50", "13:55"]
                logger.info(f"🎯 MODO NUCLEAR-SHOTGUN: Intentando {len(common_times)} horarios EN PARALELO...")
                
                # Crear todas las tareas POST en paralelo
                tasks = [
                    self._create_appointment(user_data, available_date, test_time)
                    for test_time in common_times
                ]
                
                # Ejecutar TODAS a la vez y esperar la primera que tenga éxito
                results = await asyncio.gather(*tasks, return_exceptions=True)
                
                # Buscar primer éxito
                for idx, result in enumerate(results):
                    if isinstance(result, dict) and result.get('publicId'):
                        confirmation = result['publicId']
                        successful_time = common_times[idx]
                        logger.info(f"🎉 ¡CONSEGUIDA con {successful_time}! {confirmation}")
                        return {
                            'success': True,
                            'message': '¡Reserva exitosa!',
                            'confirmation': confirmation,
                            'date': available_date,
                            'time': successful_time
                        }
                
                # Si todas fallaron, intentar GET como fallback
                logger.info(f"🔍 Fallback: Consultando horas reales...")
                times = await self._get_available_times(available_date)
                
                if not times:
                    logger.error("❌ Sin horas disponibles")
                    return {
                        'success': False,
                        'message': 'No hay horas disponibles (ya cogidas)'
                    }
                
                time_slot = times[0].get('time', '')
                logger.info(f"✅ Hora real: {time_slot}")
            
            # POST con hora conocida
            logger.info(f"🚀 POST final: {available_date} {time_slot}...")
            appointment = await self._create_appointment(user_data, available_date, time_slot)
            
            if appointment and appointment.get('publicId'):
                confirmation = appointment['publicId']
                logger.info(f"🎉 CONFIRMADO: {confirmation}")
                
                return {
                    'success': True,
                    'message': '¡Reserva exitosa!',
                    'confirmation': confirmation,
                    'date': available_date,
                    'time': first_time
                }
            else:
                logger.error("❌ Fallo al crear reserva")
                return {
                    'success': False,
                    'message': 'Error creando reserva'
                }
                
        except Exception as e:
            logger.error(f"❌ Error: {e}", exc_info=True)
            return {
                'success': False,
                'message': f'Error: {str(e)}'
            }
    
    async def _get_available_times(self, date: str) -> list:
        """Obtener horas disponibles (rápido con httpx)"""
        # Usar ; como separador (formato de la API Qmatic)
        url = f"{self.base_url}/branches/{self.branch_id}/dates/{date}/times;servicePublicId={self.service_id};customSlotLength={self.custom_slot_length}"
        
        try:
            response = await self.client.get(url)
            response.raise_for_status()
            
            data = response.json()
            logger.info(f"✅ Respuesta times: {len(data)} slots")
            logger.debug(f"Datos: {data}")
            
            return data if isinstance(data, list) else []
            
        except Exception as e:
            logger.error(f"Error GET times: {e}")
            return []
    
    async def _create_appointment(self, user_data: Dict, date: str, time: str) -> Optional[Dict]:
        """Crear reserva (rápido con httpx) - CON CACHE DE PAYLOAD"""
        url = f"{self.base_url}/appointments"
        
        # Usar payload cacheado si existe (pre-generado)
        cache_key = user_data.get('document', '')
        if cache_key in self._payload_cache:
            payload_base = self._payload_cache[cache_key]
        else:
            # Separar nombre completo y cachear
            nombre_completo = user_data.get('nombre', '')
            partes = nombre_completo.strip().split(maxsplit=1)
            first_name = partes[0] if partes else ''
            last_name = partes[1] if len(partes) > 1 else ''
            
            payload_base = {
                "services": [{"publicId": self.service_id}],
                "branch": {"publicId": self.branch_id},
                "customer": {
                    "firstName": first_name,
                    "lastName": last_name,
                    "email": user_data.get('email', ''),
                    "phone": user_data.get('phone', ''),
                    "identificationNumber": user_data.get('document', '')
                },
                "customSlotLength": self.custom_slot_length
            }
            self._payload_cache[cache_key] = payload_base
        
        # Solo añadir el timestamp (lo único que cambia)
        payload = {**payload_base, "start": f"{date}T{time}"}
        
        try:
            response = await self.client.post(
                url,
                json=payload,
                headers={
                    'Content-Type': 'application/json',
                    'Accept': 'application/json'
                }
            )
            response.raise_for_status()
            
            result = response.json()
            logger.info(f"✅ Reserva creada: {result.get('publicId', 'N/A')}")
            return result
            
        except Exception as e:
            # No loguear para no perder tiempo (solo en paralelo)
            return None


# Instancia global (reutilizar cliente HTTP)
_filler_instance = None

async def _ensure_instance():
    """Asegurar instancia global y pre-calentarla"""
    global _filler_instance
    if _filler_instance is None:
        _filler_instance = FastHTTPAutoFiller()
        await _filler_instance.warmup()
    return _filler_instance

async def fill_appointment(user_data: Dict, available_date: str, time_slot: str = None) -> Dict:
    """
    Función principal para auto-llenar (versión ULTRA-RÁPIDA)
    Reutiliza conexión HTTP para máxima velocidad
    
    Args:
        user_data: Datos del usuario
        available_date: Fecha disponible
        time_slot: Hora específica (opcional)
    """
    filler = await _ensure_instance()
    return await filler.fill_appointment(user_data, available_date, time_slot)
