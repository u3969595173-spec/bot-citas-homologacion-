"""
Cliente HTTP multiplataforma con bypass SSL
Compatible con Windows (curl) y Linux (requests)
"""

import sys
import json
import logging

logger = logging.getLogger(__name__)

# Detectar plataforma
IS_WINDOWS = sys.platform.startswith('win')

if IS_WINDOWS:
    # Windows: usar curl.exe
    import subprocess
    
    class HTTPClient:
        """Cliente HTTP que usa curl.exe (Windows)"""
        
        @staticmethod
        def get(url):
            """Petición GET usando curl.exe"""
            try:
                result = subprocess.run(
                    [
                        'curl.exe',
                        '-k',  # Ignorar errores SSL
                        '--tlsv1.2',
                        '--ssl-no-revoke',
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
else:
    # Linux: usar requests con SSL bypass
    import requests
    from requests.adapters import HTTPAdapter
    from urllib3.util.retry import Retry
    import urllib3
    
    # Deshabilitar warnings de SSL
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    
    class HTTPClient:
        """Cliente HTTP que usa requests (Linux/Render)"""
        
        def __init__(self):
            self.session = requests.Session()
            
            # Configurar reintentos
            retry_strategy = Retry(
                total=3,
                backoff_factor=0.5,
                status_forcelist=[429, 500, 502, 503, 504]
            )
            
            adapter = HTTPAdapter(max_retries=retry_strategy)
            self.session.mount("http://", adapter)
            self.session.mount("https://", adapter)
            
            # Headers
            self.session.headers.update({
                'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36',
                'Accept': 'application/json, text/plain, */*',
                'Accept-Language': 'es-ES,es;q=0.9',
                'Referer': 'https://citaprevia.ciencia.gob.es/qmaticwebbooking/'
            })
        
        def get(self, url):
            """Petición GET usando requests con SSL bypass"""
            try:
                response = self.session.get(
                    url,
                    verify=False,  # BYPASS SSL
                    timeout=10
                )
                
                if response.status_code == 200:
                    try:
                        return response.json()
                    except json.JSONDecodeError:
                        logger.error(f"Respuesta no es JSON válido: {response.text[:100]}")
                        return None
                else:
                    logger.error(f"HTTP {response.status_code}: {response.text[:100]}")
                    return None
                    
            except requests.exceptions.SSLError as e:
                logger.error(f"Error SSL: {e}")
                return None
            except requests.exceptions.RequestException as e:
                logger.error(f"Error en petición: {e}")
                return None
            except Exception as e:
                logger.error(f"Error inesperado: {e}")
                return None
    
    # Crear instancia única
    _client_instance = HTTPClient()
    
    # Wrapper para mantener compatibilidad
    class HTTPClientWrapper:
        @staticmethod
        def get(url):
            return _client_instance.get(url)
    
    HTTPClient = HTTPClientWrapper

