"""
Cliente HTTP multiplataforma con bypass SSL
Compatible con Windows y Linux usando curl
"""

import subprocess
import json
import logging

logger = logging.getLogger(__name__)

class HTTPClient:
    """Cliente HTTP que usa curl (Windows y Linux)"""
    
    @staticmethod
    def get(url):
        """Petición GET usando curl con SSL bypass"""
        try:
            # curl está disponible tanto en Windows como en Linux/Render
            result = subprocess.run(
                [
                    'curl',
                    '-k',  # Ignorar errores SSL
                    '--tlsv1.2',
                    '--ssl-allow-beast',  # Permitir SSL legacy
                    '--ciphers', 'DEFAULT@SECLEVEL=0',  # Permitir ciphers legacy
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
                
        except Exception as e:
            logger.error(f"Error ejecutando curl: {e}")
            return None
