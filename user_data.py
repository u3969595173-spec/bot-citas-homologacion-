"""
Gestión de datos de usuarios para reservas automáticas
"""

import json
import os
from pathlib import Path

USERS_FILE = Path(__file__).parent / 'users_data.json'


class UserDataManager:
    def __init__(self):
        self.users = self.load_users()
    
    def load_users(self):
        """Cargar datos de usuarios desde archivo"""
        if USERS_FILE.exists():
            with open(USERS_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {}
    
    def save_users(self):
        """Guardar datos de usuarios a archivo"""
        with open(USERS_FILE, 'w', encoding='utf-8') as f:
            json.dump(self.users, f, indent=2, ensure_ascii=False)
    
    def set_user_data(self, user_id, nombre, apellido, documento, email, telefono):
        """Guardar datos de un usuario"""
        self.users[str(user_id)] = {
            'nombre': nombre,
            'apellido': apellido,
            'documento': documento,
            'email': email,
            'telefono': telefono,
            'datos_completos': True
        }
        self.save_users()
    
    def get_user_data(self, user_id):
        """Obtener datos de un usuario"""
        return self.users.get(str(user_id))
    
    def has_complete_data(self, user_id):
        """Verificar si usuario tiene datos completos"""
        data = self.get_user_data(user_id)
        return data and data.get('datos_completos', False)
    
    def delete_user_data(self, user_id):
        """Eliminar datos de un usuario"""
        if str(user_id) in self.users:
            del self.users[str(user_id)]
            self.save_users()
            return True
        return False
