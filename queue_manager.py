"""
Sistema de cola de usuarios para reserva automática de citas
Cuando hay cita disponible, se asigna al primero de la cola
"""
import logging
from datetime import datetime
from collections import deque
import json
import os

logger = logging.getLogger(__name__)

class CitasQueue:
    """Gestiona la cola de usuarios esperando cita"""
    
    def __init__(self, file_path='queue_data.json'):
        self.file_path = file_path
        self.queue = deque()  # Cola FIFO (First In, First Out)
        self.processed = {}  # {user_id: {'fecha_cita': ..., 'timestamp': ...}}
        self.load_queue()
    
    def load_queue(self):
        """Cargar cola desde archivo"""
        try:
            if os.path.exists(self.file_path):
                with open(self.file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.queue = deque(data.get('queue', []))
                    self.processed = data.get('processed', {})
                    logger.info(f' Cola cargada: {len(self.queue)} usuarios esperando')
        except Exception as e:
            logger.error(f'Error cargando cola: {e}')
    
    def save_queue(self):
        """Guardar cola en archivo"""
        try:
            data = {
                'queue': list(self.queue),
                'processed': self.processed,
                'last_updated': datetime.now().isoformat()
            }
            with open(self.file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f'Error guardando cola: {e}')
    
    def add_user(self, user_id, user_data):
        """Agregar usuario a la cola"""
        # Verificar que no esté ya en la cola
        if user_id in self.queue:
            position = list(self.queue).index(user_id) + 1
            return False, position
        
        # Verificar que no haya sido procesado ya
        if str(user_id) in self.processed:
            return False, -1  # Ya tiene cita asignada
        
        # Agregar al final de la cola
        self.queue.append(user_id)
        self.save_queue()
        
        position = len(self.queue)
        logger.info(f' Usuario {user_id} agregado a cola. Posición: {position}')
        return True, position
    
    def get_next_user(self):
        """Obtener siguiente usuario de la cola"""
        if not self.queue:
            return None
        
        user_id = self.queue.popleft()  # Sacar el primero
        logger.info(f' Usuario {user_id} sale de la cola para asignación')
        return user_id
    
    def mark_processed(self, user_id, fecha_cita):
        """Marcar usuario como procesado (cita asignada)"""
        self.processed[str(user_id)] = {
            'fecha_cita': fecha_cita,
            'timestamp': datetime.now().isoformat(),
            'status': 'cita_asignada'
        }
        self.save_queue()
        logger.info(f' Usuario {user_id} marcado como procesado con cita: {fecha_cita}')
    
    def get_position(self, user_id):
        """Obtener posición del usuario en la cola"""
        try:
            position = list(self.queue).index(user_id) + 1
            return position
        except ValueError:
            # No está en la cola
            if str(user_id) in self.processed:
                return -1  # Ya procesado
            return 0  # No está en cola ni procesado
    
    def remove_user(self, user_id):
        """Remover usuario de la cola"""
        try:
            self.queue.remove(user_id)
            self.save_queue()
            logger.info(f'Usuario {user_id} removido de la cola')
            return True
        except ValueError:
            return False
    
    def get_queue_stats(self):
        """Estadísticas de la cola"""
        return {
            'en_espera': len(self.queue),
            'procesados': len(self.processed),
            'lista_espera': list(self.queue)[:10],  # Primeros 10
            'total_historico': len(self.queue) + len(self.processed)
        }
