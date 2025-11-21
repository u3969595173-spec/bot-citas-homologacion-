"""
Cliente HTTP multiplataforma con bypass SSL - OPTIMIZADO PARA VELOCIDAD
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
    """Cliente HTTP que usa curl (Windows y Linux) - ULTRA RÁPIDO"""
    
    # Configuración OpenSSL compartida (singleton)
    _openssl_conf = None
    _initialized = False
    
    @classmethod
    def _init_openssl_config(cls):
        """Crear configuración OpenSSL una sola vez"""
        if cls._initialized:
            return
            
        try:
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
            
            logger.info(f" Config SSL creada: {cls._openssl_conf}")
            cls._initialized = True
            atexit.register(cls._cleanup)
            
        except Exception as e:
            logger.warning(f"No se pudo crear config OpenSSL: {e}")
            cls._openssl_conf = None
    
    @classmethod
    def _cleanup(cls):
        """Limpiar archivo temporal"""
        if cls._openssl_conf and os.path.exists(cls._openssl_conf):
            try:
                os.unlink(cls._openssl_conf)
            except:
                pass
    
    @staticmethod
    def get(url):
        """Petición GET ultra rápida"""
        HTTPClient._init_openssl_config()
        
        try:
            env = os.environ.copy()
            if HTTPClient._openssl_conf:
                env['OPENSSL_CONF'] = HTTPClient._openssl_conf
            
            result = subprocess.run(
                [
                    'curl',
                    '-s',  # Silent
                    '-k',  # Ignorar SSL
                    '--max-time', '3',  # Timeout 3s (antes 10s)
                    '--connect-timeout', '2',  # Conexión 2s
                    '--keepalive-time', '10',  # Mantener conexión viva
                    '--no-buffer',  # Sin buffering
                    '--compressed',  # Aceptar compresión
                    '--tlsv1.2',
                    '--ciphers', 'DEFAULT@SECLEVEL=0',
                    '-H', 'User-Agent: Mozilla/5.0',
                    '-H', 'Accept: application/json',
                    url
                ],
                capture_output=True,
                text=True,
                timeout=5,  # Timeout Python 5s
                env=env
            )
            
            if result.returncode == 0 and result.stdout.strip():
                try:
                    return json.loads(result.stdout)
                except json.JSONDecodeError:
                    if "Exception when fetching" not in result.stdout:
                        logger.debug(f"Respuesta no JSON: {result.stdout[:50]}")
                    return None
            else:
                if result.stderr and len(result.stderr) > 10:
                    logger.debug(f"curl: {result.stderr[:100]}")
                return None
                
        except subprocess.TimeoutExpired:
            logger.warning("Timeout en petición HTTP")
            return None
        except Exception as e:
            logger.error(f"Error curl: {e}")
            return None
