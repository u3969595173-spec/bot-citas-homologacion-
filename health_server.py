"""
Servidor HTTP mínimo para health checks de Render
"""
from http.server import HTTPServer, BaseHTTPRequestHandler
import threading
import logging
import os

logger = logging.getLogger(__name__)

class HealthCheckHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/plain')
        self.end_headers()
        self.wfile.write(b'Bot OK - Monitoring active')
    
    def log_message(self, format, *args):
        pass  # Silenciar logs HTTP

def start_health_server():
    """Iniciar servidor HTTP en puerto para Render"""
    port = int(os.getenv('PORT', 10000))
    
    def run():
        try:
            server = HTTPServer(('0.0.0.0', port), HealthCheckHandler)
            logger.info(f' Health server en puerto {port}')
            server.serve_forever()
        except Exception as e:
            logger.error(f'Error en health server: {e}')
    
    thread = threading.Thread(target=run, daemon=True)
    thread.start()
