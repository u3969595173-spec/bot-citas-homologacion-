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
            timeout=httpx.Timeout(1.5, connect=0.5),  # Timeouts ULTRA agresivos
            limits=httpx.Limits(max_keepalive_connections=10, max_connections=20),
            http2=True,  # HTTP/2 para mayor velocidad
            verify=False  # Sin verificar SSL para máxima velocidad
        )
        self._warmed_up = False
    
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
                # INTENTO 1: SHOTGUN - Intentar TODOS los horarios EN PARALELO
                common_times = ["09:00", "09:30", "10:00", "10:30", "11:00", "11:30", 
                               "12:00", "12:30", "13:00", "13:30", "14:00", "14:30",
                               "15:00", "15:30", "16:00", "16:30"]
                logger.info(f"🎯 MODO SHOTGUN: Intentando {len(common_times)} horarios EN PARALELO...")
                
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
        """Crear reserva (rápido con httpx)"""
        url = f"{self.base_url}/appointments"
        
        # Separar nombre completo
        nombre_completo = user_data.get('nombre', '')
        partes = nombre_completo.strip().split(maxsplit=1)
        first_name = partes[0] if partes else ''
        last_name = partes[1] if len(partes) > 1 else ''
        
        payload = {
            "services": [{"publicId": self.service_id}],
            "branch": {"publicId": self.branch_id},
            "customer": {
                "firstName": first_name,
                "lastName": last_name,
                "email": user_data.get('email', ''),
                "phone": user_data.get('phone', ''),
                "identificationNumber": user_data.get('document', '')
            },
            "start": f"{date}T{time}",
            "customSlotLength": self.custom_slot_length
        }
        
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
            logger.error(f"Error POST appointment: {e}")
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
