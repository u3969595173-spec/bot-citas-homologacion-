"""
Cliente HTTP multiplataforma con bypass SSL
Compatible con Windows y Linux usando curl
"""

import subprocess
import json
import logging
import os
import tempfile

logger = logging.getLogger(__name__)

class HTTPClient:
    """Cliente HTTP que usa curl (Windows y Linux)"""
    
    def __init__(self):
        # Crear config OpenSSL temporal para permitir legacy renegotiation
        self.openssl_conf = None
        self._create_openssl_config()
    
    def _create_openssl_config(self):
        """Crear configuración OpenSSL que permite legacy SSL"""
        try:
            # Crear archivo de configuración temporal
            fd, self.openssl_conf = tempfile.mkstemp(suffix='.cnf', text=True)
            
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
            
            logger.info(f"Configuración OpenSSL creada en: {self.openssl_conf}")
            
        except Exception as e:
            logger.warning(f"No se pudo crear config OpenSSL: {e}")
            self.openssl_conf = None
    
    @staticmethod
    def get(url):
        """Petición GET usando curl con SSL bypass"""
        client = HTTPClient()
        return client._do_get(url)
    
    def _do_get(self, url):
        """Petición GET interna"""
        try:
            env = os.environ.copy()
            
            # Configurar variable de entorno para OpenSSL
            if self.openssl_conf:
                env['OPENSSL_CONF'] = self.openssl_conf
            
            result = subprocess.run(
                [
                    'curl',
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
                env=env  # Usar environment modificado
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
        finally:
            # Limpiar archivo temporal
            if self.openssl_conf and os.path.exists(self.openssl_conf):
                try:
                    os.unlink(self.openssl_conf)
                except:
                    pass
