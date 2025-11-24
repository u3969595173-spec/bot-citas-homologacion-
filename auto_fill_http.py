# -*- coding: utf-8 -*-
"""
Auto-llenado mediante peticiones HTTP directas (ULTRA RÁPIDO)
Sin navegador - Solo API calls
"""

import asyncio
import json
import logging
import subprocess
import os
from typing import Dict
from config import QMATIC_BASE_URL, BRANCH_ID, SERVICE_ID, CUSTOM_SLOT_LENGTH

logger = logging.getLogger(__name__)


class HTTPAutoFiller:
    """Auto-llenado de citas usando peticiones HTTP directas"""
    
    def __init__(self):
        self.base_url = QMATIC_BASE_URL
        self.branch_id = BRANCH_ID
        self.service_id = SERVICE_ID
        self.custom_slot_length = CUSTOM_SLOT_LENGTH
    
    async def fill_appointment(self, user_data: Dict, available_date: str) -> Dict:
        """
        Reservar cita mediante API HTTP directa
        
        Args:
            user_data: Datos del usuario (name, email, phone, document)
            available_date: Fecha disponible (YYYY-MM-DD)
        
        Returns:
            Dict con resultado de la reserva
        """
        try:
            logger.info(f"🚀 Iniciando reserva HTTP para {user_data.get('name')}")
            
            # PASO 1: Obtener horas disponibles para la fecha
            logger.info(f"⏰ Obteniendo horas disponibles para {available_date}...")
            times = await self._get_available_times(available_date)
            
            if not times or len(times) == 0:
                logger.error("❌ No hay horas disponibles")
                return {
                    'success': False,
                    'message': 'No hay horas disponibles para esta fecha'
                }
            
            # Tomar la primera hora disponible
            first_time = times[0]
            time_str = first_time.get('time', '')
            logger.info(f"✅ Hora seleccionada: {time_str}")
            
            # PASO 2: Crear la reserva
            logger.info("📝 Creando reserva...")
            appointment = await self._create_appointment(
                available_date,
                time_str,
                user_data
            )
            
            if appointment and appointment.get('publicId'):
                confirmation_num = appointment.get('publicId')
                logger.info(f"🎉 ¡RESERVA COMPLETADA! Nº: {confirmation_num}")
                
                return {
                    'success': True,
                    'message': '¡Reserva completada exitosamente!',
                    'confirmation': confirmation_num,
                    'date': available_date,
                    'time': time_str
                }
            else:
                logger.error("❌ No se pudo crear la reserva")
                return {
                    'success': False,
                    'message': 'Error al crear la reserva'
                }
                
        except Exception as e:
            logger.error(f"❌ Error durante reserva HTTP: {e}", exc_info=True)
            return {
                'success': False,
                'message': f'Error inesperado: {str(e)}',
                'error': str(e)
            }
    
    async def _get_available_times(self, date: str) -> list:
        """Obtener horas disponibles para una fecha"""
        url = f"{self.base_url}/schedule/branches/{self.branch_id}/dates/{date}/times;servicePublicId={self.service_id};customSlotLength={self.custom_slot_length}"
        
        try:
            result = await asyncio.to_thread(self._http_get, url)
            if result:
                logger.debug(f"Horas disponibles: {len(result)} slots")
                return result
            return []
        except Exception as e:
            logger.error(f"Error obteniendo horas: {e}")
            return []
    
    async def _create_appointment(self, date: str, time: str, user_data: Dict) -> Dict:
        """Crear reserva mediante POST"""
        url = f"{self.base_url}/schedule/appointments"
        
        # Construir payload de la reserva
        # Separar nombre y apellido
        name_parts = user_data.get('name', '').split(maxsplit=1)
        first_name = name_parts[0] if len(name_parts) > 0 else ''
        last_name = name_parts[1] if len(name_parts) > 1 else ''
        
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
            result = await asyncio.to_thread(self._http_post, url, payload)
            return result
        except Exception as e:
            logger.error(f"Error creando reserva: {e}")
            return None
    
    def _http_get(self, url: str):
        """Petición GET con curl"""
        try:
            result = subprocess.run(
                [
                    'curl',
                    '-s',
                    '-k',
                    '--max-time', '5',
                    '--connect-timeout', '2',
                    '-H', 'User-Agent: Mozilla/5.0',
                    '-H', 'Accept: application/json',
                    url
                ],
                capture_output=True,
                text=True,
                timeout=7
            )
            
            if result.returncode == 0 and result.stdout.strip():
                return json.loads(result.stdout)
            return None
            
        except Exception as e:
            logger.error(f"Error HTTP GET: {e}")
            return None
    
    def _http_post(self, url: str, data: Dict):
        """Petición POST con curl"""
        try:
            json_data = json.dumps(data)
            
            result = subprocess.run(
                [
                    'curl',
                    '-s',
                    '-k',
                    '--max-time', '5',
                    '--connect-timeout', '2',
                    '-X', 'POST',
                    '-H', 'User-Agent: Mozilla/5.0',
                    '-H', 'Content-Type: application/json',
                    '-H', 'Accept: application/json',
                    '-d', json_data,
                    url
                ],
                capture_output=True,
                text=True,
                timeout=7
            )
            
            if result.returncode == 0 and result.stdout.strip():
                return json.loads(result.stdout)
            
            logger.error(f"Error POST: {result.stderr}")
            return None
            
        except Exception as e:
            logger.error(f"Error HTTP POST: {e}")
            return None


async def fill_appointment(user_data: Dict, available_date: str) -> Dict:
    """
    Función principal para auto-llenar cita (versión HTTP rápida)
    
    Args:
        user_data: Diccionario con datos del usuario
        available_date: Fecha disponible en formato YYYY-MM-DD
    
    Returns:
        Dict con resultado de la operación
    """
    filler = HTTPAutoFiller()
    return await filler.fill_appointment(user_data, available_date)
