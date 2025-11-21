"""
Cliente HTTP que usa curl.exe para bypass SSL
"""

import subprocess
import json
import logging

logger = logging.getLogger(__name__)


class PowerShellHTTPClient:
    """Cliente HTTP que usa curl.exe para evitar problemas SSL de Python"""
    
    @staticmethod
    def get(url):
        """Hacer petición GET usando curl.exe (viene con Windows 10/11)"""
        try:
            result = subprocess.run(
                [
                    'curl.exe',
                    '-k',  # Ignorar errores SSL
                    '--tlsv1.2',  # Usar TLS 1.2
                    '--ssl-no-revoke',  # No revisar revocación de certificados
                    '-H', 'User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                    '-H', 'Accept: application/json, text/plain, */*',
                    '-H', 'Accept-Language: es-ES,es;q=0.9',
                    '-H', 'Referer: https://citaprevia.ciencia.gob.es/qmaticwebbooking/',
                    url
                ],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0 and result.stdout.strip():
                try:
                    return json.loads(result.stdout)
                except json.JSONDecodeError:
                    logger.error(f"Respuesta no es JSON válido: {result.stdout[:100]}")
                    return None
            else:
                if result.stderr:
                    logger.error(f"curl error: {result.stderr}")
                return None
                
        except FileNotFoundError:
            logger.error("curl.exe no encontrado. Debe estar instalado en Windows 10/11")
            return None
        except Exception as e:
            logger.error(f"Error ejecutando curl: {e}")
            return None
