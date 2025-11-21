# -*- coding: utf-8 -*-
"""
Sistema de cola FIFO para asignación justa de citas
Ahora usa PostgreSQL para persistencia
"""

from db import db
import logging

logger = logging.getLogger(__name__)

class CitasQueue:
    def __init__(self):
        """Inicializar cola con PostgreSQL"""
        logger.info("CitasQueue usando PostgreSQL")
    
    def add_user(self, user_id):
        """Agregar usuario a la cola"""
        position = db.add_to_queue(user_id)
        logger.info(f"Usuario {user_id} agregado a cola en posición {position}")
        return position
    
    def get_next_user(self):
        """Obtener siguiente usuario en la cola (FIFO)"""
        user_id = db.get_next_in_queue()
        if user_id:
            logger.info(f"Siguiente en cola: {user_id}")
        return user_id
    
    def remove_user(self, user_id):
        """Remover usuario de la cola"""
        success = db.remove_from_queue(user_id)
        if success:
            logger.info(f"Usuario {user_id} removido de la cola")
        return success
    
    def mark_processed(self, user_id, appointment_date):
        """Marcar usuario como procesado (ya obtuvo cita)"""
        success = db.mark_processed(user_id, appointment_date)
        if success:
            logger.info(f"Usuario {user_id} marcado como procesado con cita: {appointment_date}")
        return success
    
    def get_position(self, user_id):
        """Obtener posición de un usuario en la cola"""
        return db.get_queue_position(user_id)
    
    def get_stats(self):
        """Obtener estadísticas de la cola"""
        return db.get_queue_stats()

    def get_queue_stats(self):
        """Alias para get_stats() - compatibilidad"""
        return self.get_stats()

