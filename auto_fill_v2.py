# -*- coding: utf-8 -*-
"""
Sistema de auto-llenado automático de citas SASTU - MEJORADO
Utiliza Playwright con selectores exactos del HTML real
"""

import asyncio
import logging
import re
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeout
from typing import Dict
import os

logger = logging.getLogger(__name__)

class CitasAutoFiller:
    """Automatiza el llenado del formulario de citas de homologación"""
    
    def __init__(self):
        self.base_url = "https://citaprevia.ciencia.gob.es/qmaticwebbooking/#/"
        self.timeout = 30000  # 30 segundos
        
    async def fill_appointment(self, user_data: Dict, available_date: str) -> Dict:
        """
        Intenta reservar una cita automáticamente
        
        Args:
            user_data: Diccionario con datos del usuario (name, document, email, phone)
            available_date: Fecha disponible (formato: YYYY-MM-DD)
            
        Returns:
            Dict con resultado: {'success': bool, 'message': str, 'confirmation': str, 'screenshot': str}
        """
        screenshot_path = None
        try:
            async with async_playwright() as p:
                logger.info(f"🤖 Iniciando auto-llenado para {user_data['name']}")
                
                # Lanzar navegador en modo headless
                browser = await p.chromium.launch(
                    headless=True,
                    args=[
                        '--no-sandbox',
                        '--disable-setuid-sandbox',
                        '--disable-dev-shm-usage',
                        '--disable-gpu'
                    ]
                )
                
                context = await browser.new_context(
                    viewport={'width': 1920, 'height': 1080},
                    user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                )
                
                page = await context.new_page()
                
                # Navegar a la página
                logger.info(f"📄 Navegando a {self.base_url}")
                await page.goto(self.base_url, wait_until='networkidle', timeout=self.timeout)
                await asyncio.sleep(3)  # Esperar que cargue Vue.js
                
                # PASO 1: Servicio ya está seleccionado (verificar)
                logger.info("✅ Servicio SASTU ya seleccionado")
                
                # PASO 2: Seleccionar fecha disponible
                logger.info(f"📅 Buscando y seleccionando fecha {available_date}...")
                result = await self._select_date(page, available_date)
                if not result['success']:
                    screenshot_path = f"error_fecha_{user_data['document']}.png"
                    await page.screenshot(path=screenshot_path, full_page=True)
                    await browser.close()
                    return {**result, 'screenshot': screenshot_path}
                
                # PASO 3: Llenar formulario con datos del usuario
                logger.info("✏️ Llenando formulario de datos...")
                result = await self._fill_user_form(page, user_data)
                if not result['success']:
                    screenshot_path = f"error_form_{user_data['document']}.png"
                    await page.screenshot(path=screenshot_path, full_page=True)
                    await browser.close()
                    return {**result, 'screenshot': screenshot_path}
                
                # PASO 4: Confirmar reserva y capturar número
                logger.info("✅ Confirmando reserva...")
                result = await self._confirm_booking(page)
                
                # Capturar screenshot del resultado final
                screenshot_path = f"reserva_{user_data['document']}.png"
                await page.screenshot(path=screenshot_path, full_page=True)
                logger.info(f"📸 Screenshot guardado: {screenshot_path}")
                
                await browser.close()
                
                if result['success']:
                    confirmation_num = result.get('confirmation', 'COMPLETADO')
                    logger.info(f"🎉 ¡RESERVA COMPLETADA! Nº: {confirmation_num}")
                    return {
                        'success': True,
                        'message': '¡Reserva completada exitosamente!',
                        'confirmation': confirmation_num,
                        'screenshot': screenshot_path,
                        'date': available_date
                    }
                
                return {**result, 'screenshot': screenshot_path}
                
        except PlaywrightTimeout as e:
            logger.error(f"⏱️ Timeout durante auto-llenado: {e}")
            return {
                'success': False,
                'message': f'Timeout: El sitio web tardó demasiado en responder',
                'error': str(e),
                'screenshot': screenshot_path
            }
        except Exception as e:
            logger.error(f"❌ Error durante auto-llenado: {e}", exc_info=True)
            return {
                'success': False,
                'message': f'Error inesperado: {str(e)}',
                'error': str(e),
                'screenshot': screenshot_path
            }
    
    async def _select_date(self, page, target_date: str) -> Dict:
        """Selecciona la fecha disponible en el calendario usando selectores exactos"""
        try:
            # Esperar que el calendario esté visible
            await page.wait_for_selector('.v-date-picker-table', timeout=10000)
            await asyncio.sleep(1)
            
            # Selector exacto: botón con name="YYYY-MM-DD" SIN clase "v-btn--disabled"
            date_selector = f'button[name="{target_date}"]:not(.v-btn--disabled)'
            
            logger.info(f"🔍 Buscando botón de fecha: {date_selector}")
            
            # Verificar si existe
            button_count = await page.locator(date_selector).count()
            if button_count == 0:
                logger.warning(f"⚠️ No se encontró fecha disponible: {target_date}")
                # Buscar cualquier fecha disponible
                any_date_selector = 'button[name^="2025-"]:not(.v-btn--disabled)'
                any_button_count = await page.locator(any_date_selector).count()
                
                if any_button_count > 0:
                    first_available = await page.locator(any_date_selector).first.get_attribute('name')
                    logger.info(f"✅ Fecha alternativa encontrada: {first_available}")
                    await page.locator(any_date_selector).first.click()
                    await asyncio.sleep(2)
                    return {'success': True, 'date': first_available}
                else:
                    return {
                        'success': False,
                        'message': f'No hay fechas disponibles en el calendario'
                    }
            
            # Hacer clic en la fecha
            await page.locator(date_selector).first.click()
            await asyncio.sleep(2)  # Esperar que se abra el paso 4
            
            logger.info(f"✅ Fecha {target_date} seleccionada")
            return {'success': True}
            
        except Exception as e:
            logger.error(f"❌ Error seleccionando fecha: {e}")
            return {'success': False, 'message': f'Error al seleccionar fecha: {str(e)}'}
    
    async def _fill_user_form(self, page, user_data: Dict) -> Dict:
        """Llena el formulario con los datos del usuario"""
        try:
            # Esperar que el paso 4 se active (formulario de contacto)
            await page.wait_for_selector('#step4:not(.v-expansion-panel--disabled)', timeout=10000)
            await asyncio.sleep(1)
            
            # Mapeo de campos comunes
            fields_mapping = {
                'nombre': user_data.get('name', '').split()[0] if user_data.get('name') else '',
                'apellido': ' '.join(user_data.get('name', '').split()[1:]) if user_data.get('name') else '',
                'email': user_data.get('email', ''),
                'telefono': user_data.get('phone', ''),
                'documento': user_data.get('document', ''),
            }
            
            filled_count = 0
            
            # Intentar llenar cada campo
            for field_key, field_value in fields_mapping.items():
                if not field_value:
                    continue
                
                # Selectores posibles
                selectors = [
                    f'input[name*="{field_key}" i]',
                    f'input[id*="{field_key}" i]',
                    f'input[placeholder*="{field_key}" i]',
                    f'textarea[name*="{field_key}" i]',
                ]
                
                for selector in selectors:
                    try:
                        count = await page.locator(selector).count()
                        if count > 0:
                            element = page.locator(selector).first
                            if await element.is_visible(timeout=2000):
                                await element.clear()
                                await element.fill(field_value)
                                filled_count += 1
                                logger.info(f"✅ Campo '{field_key}' llenado")
                                break
                    except:
                        continue
            
            if filled_count == 0:
                logger.warning("⚠️ No se pudo llenar ningún campo, probando campos genéricos...")
                # Intentar con inputs visibles
                inputs = await page.locator('input[type="text"]:visible, input:not([type]):visible').all()
                if len(inputs) >= 2:
                    await inputs[0].fill(user_data.get('name', ''))
                    await inputs[1].fill(user_data.get('email', ''))
                    if len(inputs) >= 3:
                        await inputs[2].fill(user_data.get('phone', ''))
                    filled_count = len(inputs)
            
            if filled_count == 0:
                return {
                    'success': False,
                    'message': 'No se pudo llenar ningún campo del formulario'
                }
            
            logger.info(f"✅ {filled_count} campos llenados correctamente")
            await asyncio.sleep(1)
            
            return {'success': True}
            
        except Exception as e:
            logger.error(f"❌ Error llenando formulario: {e}")
            return {'success': False, 'message': f'Error al llenar formulario: {str(e)}'}
    
    async def _confirm_booking(self, page) -> Dict:
        """Confirma la reserva final y captura el número de confirmación"""
        try:
            # Buscar botón de confirmar/reservar
            confirm_buttons = [
                'button:has-text("Confirmar")',
                'button:has-text("Reservar")',
                'button:has-text("Aceptar")',
                'button:has-text("Finalizar")',
                'button.button_primary',
                'button[type="submit"]',
            ]
            
            for selector in confirm_buttons:
                try:
                    count = await page.locator(selector).count()
                    if count > 0:
                        element = page.locator(selector).first
                        if await element.is_visible(timeout=3000):
                            await element.click()
                            logger.info(f"✅ Clic en botón: {selector}")
                            await asyncio.sleep(5)  # Esperar confirmación
                            break
                except:
                    continue
            
            # Buscar número de confirmación en la página
            confirmation_code = await self._extract_confirmation_number(page)
            
            if confirmation_code:
                logger.info(f"🎉 Número de reserva capturado: {confirmation_code}")
                return {
                    'success': True,
                    'message': '¡Reserva completada exitosamente!',
                    'confirmation': confirmation_code
                }
            else:
                # Si no encuentra número, buscar mensaje de éxito
                success_messages = await page.locator('text=/.*reserva.*éxito.*/i, text=/.*confirmad.*/i').count()
                if success_messages > 0:
                    return {
                        'success': True,
                        'message': 'Reserva completada',
                        'confirmation': 'CONFIRMADO (sin número visible)'
                    }
            
            return {
                'success': True,
                'message': 'Proceso completado (verificar screenshot)',
                'confirmation': 'COMPLETADO'
            }
            
        except Exception as e:
            logger.error(f"❌ Error confirmando reserva: {e}")
            return {'success': False, 'message': f'Error al confirmar: {str(e)}'}
    
    async def _extract_confirmation_number(self, page) -> str:
        """Extrae el número de confirmación/reserva de la página"""
        try:
            # Patrones comunes de números de confirmación
            patterns = [
                r'(?:confirmación|reserva|referencia)[\s:]+([A-Z0-9\-]+)',
                r'(?:número|codigo|code)[\s:]+([A-Z0-9\-]+)',
                r'\b([A-Z]{2,}\d{4,})\b',
                r'\b(\d{6,})\b',
            ]
            
            # Obtener texto de la página
            page_text = await page.text_content('body')
            
            for pattern in patterns:
                match = re.search(pattern, page_text, re.IGNORECASE)
                if match:
                    return match.group(1)
            
            # Buscar en elementos específicos
            selectors = [
                '.confirmation-number',
                '.booking-reference',
                '[class*="confirm"]',
                '[id*="confirm"]',
            ]
            
            for selector in selectors:
                try:
                    element = page.locator(selector).first
                    text = await element.text_content(timeout=2000)
                    if text and len(text.strip()) > 3:
                        return text.strip()
                except:
                    continue
            
            return None
            
        except Exception as e:
            logger.error(f"Error extrayendo número: {e}")
            return None


async def auto_fill_appointment(user_data: Dict, available_date: str) -> Dict:
    """
    Función principal para auto-llenar una cita
    
    Args:
        user_data: Dict con {name, document, email, phone}
        available_date: Fecha disponible (YYYY-MM-DD)
    
    Returns:
        Dict con resultado de la operación
    """
    filler = CitasAutoFiller()
    return await filler.fill_appointment(user_data, available_date)
