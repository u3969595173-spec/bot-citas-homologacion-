"""
Adaptador SSL personalizado para conexiones legacy
"""

import ssl
import urllib3
from urllib3.util.ssl_ import create_urllib3_context


class CustomHTTPSAdapter(urllib3.poolmanager.PoolManager):
    """Adaptador HTTPS personalizado que permite renegociación legacy"""
    
    def __init__(self, *args, **kwargs):
        ctx = create_urllib3_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        # Forzar protocolo TLS 1.2
        ctx.minimum_version = ssl.TLSVersion.TLSv1_2
        ctx.maximum_version = ssl.TLSVersion.TLSv1_2
        # Cifrados compatibles con servidores legacy
        ctx.set_ciphers('DEFAULT@SECLEVEL=1')
        
        kwargs['ssl_context'] = ctx
        super().__init__(*args, **kwargs)
