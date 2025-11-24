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
        self.service_id = "4e5f0a7d-d72c-472c-b1f6-1c46034b5c40"
        self.branch_id = "40c40c84-f972-4eae-8c8f-e2d7f4e08c8b"
        self.custom_slot_length = 10
        
        # Cliente HTTP reutilizable (conexión persistente) - PRE-CALENTADO
        self.client = httpx.AsyncClient(
            timeout=httpx.Timeout(3.0, connect=1.0),  # Timeouts más agresivos
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
    
    async def fill_appointment(self, user_data: Dict, available_date: str) -> Dict:
        """
        Reservar cita de forma ultra-rápida
        
        Args:
            user_data: Datos del usuario
            available_date: Fecha en formato YYYY-MM-DD
            
        Returns:
            Dict con resultado
        """
        try:
            # Asegurar conexión pre-calentada
            await self.warmup()
            
            logger.info(f"⚡ RESERVA RÁPIDA para {user_data.get('nombre', 'Usuario')}")
            
            # PASO 1: Obtener horas disponibles (usando cliente rápido)
            logger.info(f"🔍 Consultando horas para {available_date}...")
            times = await self._get_available_times(available_date)
            
            if not times:
                logger.error("❌ Sin horas disponibles")
                return {
                    'success': False,
                    'message': 'No hay horas disponibles'
                }
            
            first_time = times[0].get('time', '')
            logger.info(f"✅ Primera hora: {first_time}")
            
            # PASO 2: Crear reserva inmediatamente
            logger.info("🚀 Creando reserva...")
            appointment = await self._create_appointment(user_data, available_date, first_time)
            
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
        url = f"{self.base_url}/branches/{self.branch_id}/dates/{date}/times"
        params = {
            'servicePublicId': self.service_id,
            'customSlotLength': self.custom_slot_length
        }
        
        try:
            response = await self.client.get(url, params=params)
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

async def fill_appointment(user_data: Dict, available_date: str) -> Dict:
    """
    Función principal para auto-llenar (versión ULTRA-RÁPIDA)
    Reutiliza conexión HTTP para máxima velocidad
    """
    filler = await _ensure_instance()
    return await filler.fill_appointment(user_data, available_date)
