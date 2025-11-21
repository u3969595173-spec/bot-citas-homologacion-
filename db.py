"""
Base de datos PostgreSQL para CitasBot
"""

import os
import psycopg2
from psycopg2.extras import RealDictCursor
import json
import logging

logger = logging.getLogger(__name__)

# URL de conexión desde variable de entorno
DATABASE_URL = os.getenv('DATABASE_URL', '')

class Database:
    def __init__(self):
        self.conn = None
        self.connect()
        self.init_tables()
    
    def connect(self):
        """Conectar a PostgreSQL"""
        try:
            if DATABASE_URL:
                self.conn = psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)
                logger.info(" Conectado a PostgreSQL")
            else:
                logger.warning(" DATABASE_URL no configurada, usando modo sin BD")
        except Exception as e:
            logger.error(f" Error conectando a BD: {e}")
            self.conn = None
    
    def init_tables(self):
        """Crear tablas si no existen"""
        if not self.conn:
            return
        
        try:
            cursor = self.conn.cursor()
            
            # Tabla de usuarios
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    user_id BIGINT PRIMARY KEY,
                    nombre TEXT,
                    apellido TEXT,
                    documento TEXT,
                    email TEXT,
                    telefono TEXT,
                    datos_completos BOOLEAN DEFAULT FALSE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Tabla de cola
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS queue (
                    id SERIAL PRIMARY KEY,
                    user_id BIGINT,
                    position INTEGER,
                    processed BOOLEAN DEFAULT FALSE,
                    appointment_date TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Tabla de usuarios activos (monitoreo)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS active_users (
                    user_id BIGINT PRIMARY KEY,
                    pausado BOOLEAN DEFAULT FALSE,
                    notified BOOLEAN DEFAULT FALSE,
                    last_update TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            self.conn.commit()
            cursor.close()
            logger.info(" Tablas creadas/verificadas")
        except Exception as e:
            logger.error(f" Error creando tablas: {e}")
    
    # ========== USUARIOS ==========
    
    def save_user(self, user_id, nombre, apellido, documento, email, telefono):
        """Guardar datos de usuario"""
        if not self.conn:
            return False
        
        try:
            cursor = self.conn.cursor()
            cursor.execute("""
                INSERT INTO users (user_id, nombre, apellido, documento, email, telefono, datos_completos)
                VALUES (%s, %s, %s, %s, %s, %s, TRUE)
                ON CONFLICT (user_id) 
                DO UPDATE SET 
                    nombre = EXCLUDED.nombre,
                    apellido = EXCLUDED.apellido,
                    documento = EXCLUDED.documento,
                    email = EXCLUDED.email,
                    telefono = EXCLUDED.telefono,
                    datos_completos = TRUE
            """, (user_id, nombre, apellido, documento, email, telefono))
            self.conn.commit()
            cursor.close()
            return True
        except Exception as e:
            logger.error(f"Error guardando usuario: {e}")
            return False
    
    def get_user(self, user_id):
        """Obtener datos de usuario"""
        if not self.conn:
            return None
        
        try:
            cursor = self.conn.cursor()
            cursor.execute("SELECT * FROM users WHERE user_id = %s", (user_id,))
            result = cursor.fetchone()
            cursor.close()
            return dict(result) if result else None
        except Exception as e:
            logger.error(f"Error obteniendo usuario: {e}")
            return None
    
    def delete_user(self, user_id):
        """Eliminar usuario"""
        if not self.conn:
            return False
        
        try:
            cursor = self.conn.cursor()
            cursor.execute("DELETE FROM users WHERE user_id = %s", (user_id,))
            self.conn.commit()
            cursor.close()
            return True
        except Exception as e:
            logger.error(f"Error eliminando usuario: {e}")
            return False
    
    # ========== COLA ==========
    
    def add_to_queue(self, user_id):
        """Agregar usuario a la cola"""
        if not self.conn:
            return 0
        
        try:
            cursor = self.conn.cursor()
            
            # Verificar si ya está en cola
            cursor.execute("""
                SELECT id FROM queue 
                WHERE user_id = %s AND processed = FALSE
            """, (user_id,))
            
            if cursor.fetchone():
                cursor.close()
                return self.get_queue_position(user_id)
            
            # Obtener siguiente posición
            cursor.execute("SELECT COALESCE(MAX(position), 0) + 1 FROM queue WHERE processed = FALSE")
            result = cursor.fetchone()
            position = result['coalesce'] if isinstance(result, dict) else result[0]
            
            cursor.execute("""
                INSERT INTO queue (user_id, position, processed)
                VALUES (%s, %s, FALSE)
            """, (user_id, position))
            
            self.conn.commit()
            cursor.close()
            return position
        except Exception as e:
            logger.error(f"Error agregando a cola: {e}")
            return 0
    
    def get_next_in_queue(self):
        """Obtener siguiente usuario en cola"""
        if not self.conn:
            return None
        
        try:
            cursor = self.conn.cursor()
            cursor.execute("""
                SELECT user_id FROM queue 
                WHERE processed = FALSE 
                ORDER BY position ASC 
                LIMIT 1
            """)
            result = cursor.fetchone()
            cursor.close()
            return result['user_id'] if result else None
        except Exception as e:
            logger.error(f"Error obteniendo siguiente en cola: {e}")
            return None
    
    def remove_from_queue(self, user_id):
        """Remover usuario de la cola"""
        if not self.conn:
            return False
        
        try:
            cursor = self.conn.cursor()
            cursor.execute("""
                DELETE FROM queue 
                WHERE user_id = %s AND processed = FALSE
            """, (user_id,))
            self.conn.commit()
            cursor.close()
            return True
        except Exception as e:
            logger.error(f"Error removiendo de cola: {e}")
            return False
    
    def mark_processed(self, user_id, appointment_date):
        """Marcar usuario como procesado"""
        if not self.conn:
            return False
        
        try:
            cursor = self.conn.cursor()
            cursor.execute("""
                UPDATE queue 
                SET processed = TRUE, appointment_date = %s
                WHERE user_id = %s AND processed = FALSE
            """, (appointment_date, user_id))
            self.conn.commit()
            cursor.close()
            return True
        except Exception as e:
            logger.error(f"Error marcando como procesado: {e}")
            return False
    
    def get_queue_position(self, user_id):
        """Obtener posición en cola"""
        if not self.conn:
            return 0
        
        try:
            cursor = self.conn.cursor()
            cursor.execute("""
                SELECT COUNT(*) as pos FROM queue 
                WHERE processed = FALSE AND position <= (
                    SELECT position FROM queue 
                    WHERE user_id = %s AND processed = FALSE
                )
            """, (user_id,))
            result = cursor.fetchone()
            cursor.close()
            return result['pos'] if result else 0
        except Exception as e:
            logger.error(f"Error obteniendo posición: {e}")
            return 0
    
    def get_queue_stats(self):
        """Obtener estadísticas de la cola"""
        if not self.conn:
            return {'en_espera': 0, 'procesados': 0}
        
        try:
            cursor = self.conn.cursor()
            cursor.execute("""
                SELECT 
                    COUNT(*) FILTER (WHERE processed = FALSE) as waiting,
                    COUNT(*) FILTER (WHERE processed = TRUE) as processed
                FROM queue
            """)
            result = cursor.fetchone()
            cursor.close()
            if result:

                return {'en_espera': result['waiting'], 'procesados': result['processed']}

            return {'en_espera': 0, 'procesados': 0}
        except Exception as e:
            logger.error(f"Error obteniendo stats: {e}")
            return {'en_espera': 0, 'procesados': 0}
    
    # ========== USUARIOS ACTIVOS ==========
    
    def set_user_active(self, user_id, pausado=False):
        """Activar monitoreo para usuario"""
        if not self.conn:
            return False
        
        try:
            cursor = self.conn.cursor()
            cursor.execute("""
                INSERT INTO active_users (user_id, pausado, notified)
                VALUES (%s, %s, FALSE)
                ON CONFLICT (user_id) 
                DO UPDATE SET pausado = EXCLUDED.pausado, last_update = CURRENT_TIMESTAMP
            """, (user_id, pausado))
            self.conn.commit()
            cursor.close()
            return True
        except Exception as e:
            logger.error(f"Error activando usuario: {e}")
            return False
    
    def get_active_user(self, user_id):
        """Obtener estado de usuario activo"""
        if not self.conn:
            return None
        
        try:
            cursor = self.conn.cursor()
            cursor.execute("SELECT * FROM active_users WHERE user_id = %s", (user_id,))
            result = cursor.fetchone()
            cursor.close()
            return dict(result) if result else None
        except Exception as e:
            logger.error(f"Error obteniendo usuario activo: {e}")
            return None
    
    def remove_active_user(self, user_id):
        """Desactivar monitoreo"""
        if not self.conn:
            return False
        
        try:
            cursor = self.conn.cursor()
            cursor.execute("DELETE FROM active_users WHERE user_id = %s", (user_id,))
            self.conn.commit()
            cursor.close()
            return True
        except Exception as e:
            logger.error(f"Error removiendo usuario activo: {e}")
            return False
    
    def close(self):
        """Cerrar conexión"""
        if self.conn:
            self.conn.close()
            logger.info(" Conexión a BD cerrada")

# Instancia global
db = Database()


