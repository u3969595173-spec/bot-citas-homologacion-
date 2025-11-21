"""
Cliente HTTP multiplataforma con bypass SSL
Compatible con Windows y Linux usando curl
"""

import subprocess
import json
import logging
import os
import tempfile
import atexit

logger = logging.getLogger(__name__)

class HTTPClient:
    """Cliente HTTP que usa curl (Windows y Linux)"""
    
    # Configuración OpenSSL compartida (singleton)
    _openssl_conf = None
    _initialized = False
    
    @classmethod
    def _init_openssl_config(cls):
        """Crear configuración OpenSSL una sola vez"""
        if cls._initialized:
            return
            
        try:
            # Crear archivo de configuración temporal
            fd, cls._openssl_conf = tempfile.mkstemp(suffix='.cnf', text=True)
            
            config_content = """
openssl_conf = openssl_init

[openssl_init]
ssl_conf = ssl_sect

[ssl_sect]
system_default = system_default_sect

[system_default_sect]
Options = UnsafeLegacyRenegotiation
CipherString = DEFAULT@SECLEVEL=0
"""
            
            os.write(fd, config_content.encode('utf-8'))
            os.close(fd)
            
            logger.info(f" Configuración OpenSSL creada: {cls._openssl_conf}")
            cls._initialized = True
            
            # Registrar limpieza al salir
            atexit.register(cls._cleanup)
            
        except Exception as e:
            logger.warning(f"No se pudo crear config OpenSSL: {e}")
            cls._openssl_conf = None
    
    @classmethod
    def _cleanup(cls):
        """Limpiar archivo temporal al salir"""
        if cls._openssl_conf and os.path.exists(cls._openssl_conf):
            try:
                os.unlink(cls._openssl_conf)
                logger.debug("Config OpenSSL limpiada")
            except:
                pass
    
    @staticmethod
    def get(url):
        """Petición GET usando curl con SSL bypass"""
        # Inicializar configuración si es necesario
        HTTPClient._init_openssl_config()
        
        try:
            env = os.environ.copy()
            
            # Configurar variable de entorno para OpenSSL
            if HTTPClient._openssl_conf:
                env['OPENSSL_CONF'] = HTTPClient._openssl_conf
            
            result = subprocess.run(
                [
                    'curl',
                    '-s',  # Silent mode
                    '-k',  # Ignorar errores de certificado
                    '--tlsv1.2',
                    '--ssl-allow-beast',
                    '--ciphers', 'DEFAULT@SECLEVEL=0',
                    '-H', 'User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                    '-H', 'Accept: application/json, text/plain, */*',
                    '-H', 'Accept-Language: es-ES,es;q=0.9',
                    '-H', 'Referer: https://citaprevia.ciencia.gob.es/qmaticwebbooking/',
                    url
                ],
                capture_output=True,
                text=True,
                timeout=10,
                env=env
            )
            
            if result.returncode == 0 and result.stdout.strip():
                try:
                    return json.loads(result.stdout)
                except json.JSONDecodeError:
                    # No loguear como error si es respuesta esperada del servidor
                    if "Exception when fetching" not in result.stdout:
                        logger.error(f"Respuesta no es JSON válido: {result.stdout[:100]}")
                    return None
            else:
                if result.stderr:
                    logger.error(f"curl error: {result.stderr}")
                return None
                
        except Exception as e:
            logger.error(f"Error ejecutando curl: {e}")
            return None
