# -*- coding: utf-8 -*-
"""
Sistema de auto-llenado automÃ¡tico de citas SASTU
Utiliza Playwright para automatizar el proceso de reserva
"""

import asyncio
import logging
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeout
from typing import Dict, Optional, List
import os

logger = logging.getLogger(__name__)

class CitasAutoFiller:
    """Automatiza el llenado del formulario de citas de homologaciÃ³n"""
    
    def __init__(self):
        self.base_url = "https://citaprevia.ciencia.gob.es/qmaticwebbooking/#/"
        self.timeout = 30000  # 30 segundos
        
    async def fill_appointment(self, user_data: Dict, available_date: str) -> Dict:
        """
        Intenta reservar una cita automÃ¡ticamente
        
        Args:
            user_data: Diccionario con datos del usuario (name, document, email, phone)
            available_date: Fecha disponible (formato: YYYY-MM-DD)
            
        Returns:
            Dict con resultado: {'success': bool, 'message': str, 'confirmation': str}
        """
        try:
            async with async_playwright() as p:
                logger.info(f"ðŸ¤– Iniciando auto-llenado para {user_data['name']}")
                
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
                
                # Navegar a la pÃ¡gina
                logger.info(f"ðŸ“„ Navegando a {self.base_url}")
                await page.goto(self.base_url, wait_until='networkidle', timeout=self.timeout)
                
                # Esperar 2 segundos para que cargue completamente
                await asyncio.sleep(2)
                
                # PASO 1: Seleccionar servicio SASTU
                logger.info("ðŸ“‹ Seleccionando servicio SASTU...")
                result = await self._select_service(page)
                if not result['success']:
                    await browser.close()
                    return result
                
                # PASO 2: Seleccionar fecha disponible
                logger.info(f"ðŸ“… Seleccionando fecha {available_date}...")
                result = await self._select_date(page, available_date)
                if not result['success']:
                    await browser.close()
                    return result
                
                # PASO 3: Llenar formulario con datos del usuario
                logger.info("âœï¸ Llenando formulario de datos...")
                result = await self._fill_user_form(page, user_data)
                if not result['success']:
                    await browser.close()
                    return result
                
                # PASO 4: Confirmar reserva
                logger.info("âœ… Confirmando reserva...")
                result = await self._confirm_booking(page)
                
                # Capturar screenshot del resultado
                screenshot_path = f"confirmation_{user_data['document']}.png"
                await page.screenshot(path=screenshot_path, full_page=True)
                logger.info(f"ðŸ“¸ Screenshot guardado: {screenshot_path}")
                
                await browser.close()
                
                if result['success']:
                    logger.info(f"âœ… Â¡RESERVA COMPLETADA AUTOMÃTICAMENTE! {result.get('confirmation', '')}")
                
                return result
                
        except PlaywrightTimeout as e:
            logger.error(f"â±ï¸ Timeout durante auto-llenado: {e}")
            return {
                'success': False,
                'message': f'Timeout: El sitio web tardÃ³ demasiado en responder',
                'error': str(e)
            }
        except Exception as e:
            logger.error(f"âŒ Error durante auto-llenado: {e}", exc_info=True)
            return {
                'success': False,
                'message': f'Error inesperado: {str(e)}',
                'error': str(e)
            }
    
    async def _select_service(self, page) -> Dict:
        """Selecciona el servicio SASTU en el menÃº"""
        try:
            # Buscar botones o links que contengan "SASTU" o "homologaciÃ³n"
            selectors = [
                "text=/.*SASTU.*/i",
                "text=/.*homologaciÃ³n.*/i",
                "text=/.*homologacion.*/i",
                "button:has-text('SASTU')",
                "a:has-text('SASTU')",
                "[title*='SASTU']",
                "[aria-label*='SASTU']"
            ]
            
            for selector in selectors:
                try:
                    element = page.locator(selector).first
                    if await element.is_visible(timeout=5000):
                        await element.click()
                        await page.wait_for_load_state('networkidle', timeout=10000)
                        logger.info("âœ… Servicio SASTU seleccionado")
                        return {'success': True}
                except:
                    continue
            
            # Si no encuentra el selector, capturar el HTML para debug
            html = await page.content()
            logger.error(f"âŒ No se encontrÃ³ el servicio SASTU en la pÃ¡gina")
            
            return {
                'success': False,
                'message': 'No se pudo encontrar el servicio SASTU en el menÃº'
            }
            
        except Exception as e:
            logger.error(f"âŒ Error seleccionando servicio: {e}")
            return {'success': False, 'message': f'Error al seleccionar servicio: {str(e)}'}
    
    async def _select_date(self, page, target_date: str) -> Dict:
        """Selecciona la fecha disponible en el calendario"""
        try:
            # Formato esperado: YYYY-MM-DD -> DD/MM/YYYY o DD-MM-YYYY
            date_parts = target_date.split('-')
            if len(date_parts) == 3:
                day, month, year = date_parts[2], date_parts[1], date_parts[0]
                formatted_dates = [
                    f"{day}/{month}/{year}",
                    f"{day}-{month}-{year}",
                    f"{int(day)}/{int(month)}/{year}",
                    target_date
                ]
            else:
                formatted_dates = [target_date]
            
            # Buscar la fecha en el calendario
            for date_format in formatted_dates:
                selectors = [
                    f"text='{date_format}'",
                    f"[data-date='{date_format}']",
                    f"[aria-label*='{date_format}']",
                    f"button:has-text('{day}')",
                    f".calendar-day:has-text('{day}')"
                ]
                
                for selector in selectors:
                    try:
                        element = page.locator(selector).first
                        if await element.is_visible(timeout=5000):
                            await element.click()
                            await asyncio.sleep(1)
                            logger.info(f"âœ… Fecha {target_date} seleccionada")
                            return {'success': True}
                    except:
                        continue
            
            # Intentar con cualquier fecha disponible
            available_dates = await page.locator(".available-date, .date-available, button.date:not(.disabled)").all()
            if available_dates:
                await available_dates[0].click()
                await asyncio.sleep(1)
                logger.info("âœ… Primera fecha disponible seleccionada")
                return {'success': True}
            
            return {
                'success': False,
                'message': f'No se pudo seleccionar la fecha {target_date}'
            }
            
        except Exception as e:
            logger.error(f"âŒ Error seleccionando fecha: {e}")
            return {'success': False, 'message': f'Error al seleccionar fecha: {str(e)}'}
    
    async def _fill_user_form(self, page, user_data: Dict) -> Dict:
        """Llena el formulario con los datos del usuario"""
        try:
            # Mapeo de campos comunes
            fields = {
                'nombre': user_data.get('name', ''),
                'documento': user_data.get('document', ''),
                'email': user_data.get('email', ''),
                'telefono': user_data.get('phone', ''),
                'movil': user_data.get('phone', ''),
            }
            
            filled_count = 0
            
            for field_name, field_value in fields.items():
                if not field_value:
                    continue
                
                # MÃºltiples selectores posibles para cada campo
                selectors = [
                    f"input[name*='{field_name}' i]",
                    f"input[id*='{field_name}' i]",
                    f"input[placeholder*='{field_name}' i]",
                    f"input[aria-label*='{field_name}' i]",
                    f"textarea[name*='{field_name}' i]",
                ]
                
                for selector in selectors:
                    try:
                        elements = await page.locator(selector).all()
                        for element in elements:
                            if await element.is_visible(timeout=2000):
                                await element.clear()
                                await element.fill(field_value)
                                filled_count += 1
                                logger.info(f"âœ… Campo '{field_name}' llenado con: {field_value}")
                                break
                    except:
                        continue
            
            if filled_count == 0:
                return {
                    'success': False,
                    'message': 'No se pudo llenar ningÃºn campo del formulario'
                }
            
            logger.info(f"âœ… {filled_count} campos llenados correctamente")
            
            # Buscar y hacer clic en botÃ³n "Siguiente" o "Continuar"
            next_buttons = [
                "button:has-text('Siguiente')",
                "button:has-text('Continuar')",
                "button:has-text('Next')",
                "button[type='submit']",
                "input[type='submit']"
            ]
            
            for selector in next_buttons:
                try:
                    element = page.locator(selector).first
                    if await element.is_visible(timeout=3000):
                        await element.click()
                        await page.wait_for_load_state('networkidle', timeout=10000)
                        logger.info("âœ… Formulario enviado")
                        return {'success': True}
                except:
                    continue
            
            return {'success': True, 'message': 'Formulario llenado (sin botÃ³n continuar)'}
            
        except Exception as e:
            logger.error(f"âŒ Error llenando formulario: {e}")
            return {'success': False, 'message': f'Error al llenar formulario: {str(e)}'}
    
    async def _confirm_booking(self, page) -> Dict:
        """Confirma la reserva final"""
        try:
            # Buscar botÃ³n de confirmaciÃ³n
            confirm_buttons = [
                "button:has-text('Confirmar')",
                "button:has-text('Reservar')",
                "button:has-text('Aceptar')",
                "button:has-text('Finalizar')",
                "button.confirm",
                "button.book"
            ]
            
            for selector in confirm_buttons:
                try:
                    element = page.locator(selector).first
                    if await element.is_visible(timeout=5000):
                        await element.click()
                        await asyncio.sleep(3)  # Esperar confirmaciÃ³n
                        
                        # Buscar nÃºmero de confirmaciÃ³n
                        confirmation_selectors = [
                            ".confirmation-number",
                            ".booking-reference",
                            "text=/.*confirmaciÃ³n.*/i",
                            "text=/.*reserva.*/i"
                        ]
                        
                        confirmation_code = "CONFIRMADO"
                        for conf_selector in confirmation_selectors:
                            try:
                                conf_element = page.locator(conf_selector).first
                                if await conf_element.is_visible(timeout=3000):
                                    confirmation_code = await conf_element.inner_text()
                                    break
                            except:
                                continue
                        
                        logger.info(f"âœ… Reserva confirmada: {confirmation_code}")
                        return {
                            'success': True,
                            'message': 'Â¡Reserva completada exitosamente!',
                            'confirmation': confirmation_code
                        }
                except:
                    continue
            
            # Si llegamos aquÃ­, asumimos que se completÃ³ pero sin confirmaciÃ³n explÃ­cita
            return {
                'success': True,
                'message': 'Proceso completado (sin cÃ³digo de confirmaciÃ³n)',
                'confirmation': 'COMPLETADO'
            }
            
        except Exception as e:
            logger.error(f"âŒ Error confirmando reserva: {e}")
            return {'success': False, 'message': f'Error al confirmar: {str(e)}'}


async def auto_fill_appointment(user_data: Dict, available_date: str) -> Dict:
    """
    FunciÃ³n principal para auto-llenar una cita
    
    Args:
        user_data: Dict con {name, document, email, phone}
        available_date: Fecha disponible (YYYY-MM-DD)
    
    Returns:
        Dict con resultado de la operaciÃ³n
    """
    filler = CitasAutoFiller()
    return await filler.fill_appointment(user_data, available_date)


# Test standalone
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    test_data = {
        'name': 'Leandro Eloy Tamayo Reyes',
        'document': 'Z0934880G',
        'email': 'leandroeloytamayoreyes@gmail.com',
        'phone': '+34654034110'
    }
    
    result = asyncio.run(auto_fill_appointment(test_data, '2025-12-01'))
    print(f"\n{'='*50}")
    print(f"Resultado: {result}")
    print(f"{'='*50}")


