# -*- coding: utf-8 -*-
"""
Gestión de datos de usuarios para reservas automáticas
Ahora usa PostgreSQL para persistencia
"""

from db import db
import logging

logger = logging.getLogger(__name__)

class UserDataManager:
    def __init__(self):
        """Inicializar con base de datos"""
        logger.info("UserDataManager usando PostgreSQL")
    
    def set_user_data(self, user_id, nombre, apellido, documento, email, telefono):
        """Guardar datos de un usuario"""
        return db.save_user(user_id, nombre, apellido, documento, email, telefono)
    
    def get_user_data(self, user_id):
        """Obtener datos de un usuario"""
        return db.get_user(user_id)
    
    def has_complete_data(self, user_id):
        """Verificar si usuario tiene datos completos"""
        data = self.get_user_data(user_id)
        return data and data.get('datos_completos', False)
    
    def delete_user_data(self, user_id):
        """Eliminar datos de un usuario"""
        return db.delete_user(user_id)
