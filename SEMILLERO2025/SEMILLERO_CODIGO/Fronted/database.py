import sqlite3
import bcrypt

class Database:
    def __init__(self, db_path='usuarios.db'):
        self.db_path = db_path
        self.crear_tabla_usuarios()
    
    def get_connection(self):
        """Crea conexión a la base de datos"""
        return sqlite3.connect(self.db_path)
    
    def crear_tabla_usuarios(self):
        """Crea la tabla de usuarios si no existe"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS usuarios (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                email TEXT,
                fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                nombre_completo TEXT,
                documento TEXT
            )
        ''')
        
        #Tabla de historial de ejecuciones 
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS historial_ejecuciones (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                fecha_ejecucion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                usuario TEXT,
                pdfs_procesados INTEGER DEFAULT 0,
                correos_enviados INTEGER DEFAULT 0,
                estado TEXT,
                detalles TEXT
            )
        ''')
        
        conn.commit()
        conn.close()
        print("✓ Tablas creadas")
    
    def crear_usuario(self, username, password, email=None):
        """Crea un nuevo usuario con contraseña encriptada"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        #Encriptar contraseña
        password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
        
        try:
            cursor.execute(
                "INSERT INTO usuarios (username, password_hash, email) VALUES (?, ?, ?)",
                (username, password_hash, email)
            )
            conn.commit()
            conn.close()
            return True, "Usuario creado exitosamente"
        except sqlite3.IntegrityError:
            conn.close()
            return False, "El usuario ya existe"
        except Exception as e:
            conn.close()
            return False, f"Error: {str(e)}"
    
    def verificar_usuario(self, username, password):
        """Verifica las credenciales del usuario"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT password_hash FROM usuarios WHERE username = ?", (username,))
        result = cursor.fetchone()
        conn.close()
        
        if result:
            return bcrypt.checkpw(password.encode('utf-8'), result[0])
        return False
    
    def usuario_existe(self, username):
        """Verifica si un usuario ya existe"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT 1 FROM usuarios WHERE username = ?", (username,))
        result = cursor.fetchone()
        conn.close()
        
        return result is not None
    
    def guardar_ejecucion(self, usuario, correos_proc=0, pdfs_proc=0, correos_env=0, estado="Completado", detalles=""):
        """Guarda información de una ejecución del proceso"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO historial_ejecuciones 
            (usuario, pdfs_procesados, correos_enviados, estado, detalles)
            VALUES (?, ?, ?, ?, ?)
        ''', (usuario, pdfs_proc, correos_env, estado, detalles))
        
        conn.commit()
        conn.close()

    def obtener_historial(self, usuario, limite=50):
        """Obtiene el historial de ejecuciones filtrado por usuario"""
        conn = self.get_connection()
        cursor = conn.cursor()
    
        cursor.execute('''
        SELECT id, fecha_ejecucion, usuario, 
               pdfs_procesados, correos_enviados, estado, detalles
        FROM historial_ejecuciones
        WHERE usuario = ?
        ORDER BY fecha_ejecucion DESC 
        LIMIT ?
        ''', (usuario, limite))
    
        resultados = cursor.fetchall()
        conn.close()
        return resultados

    def guardar_info_usuario(self, username, nombre_completo, documento):
        """Guarda información adicional del usuario"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE usuarios 
            SET nombre_completo = ?, documento = ?
            WHERE username = ?
        ''', (nombre_completo, documento, username))
        
        conn.commit()
        conn.close()

    def obtener_info_usuario(self, username):
        """Obtiene información adicional del usuario"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT nombre_completo, documento 
            FROM usuarios 
            WHERE username = ?
        ''', (username,))
        
        result = cursor.fetchone()
        conn.close()
        
        if result:
            return result[0], result[1]
        return None, None

    def cambiar_contrasena(self, username, nueva_password):
        """Cambia la contraseña del usuario"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        password_hash = bcrypt.hashpw(nueva_password.encode('utf-8'), bcrypt.gensalt())
        
        cursor.execute('''
            UPDATE usuarios 
            SET password_hash = ?
            WHERE username = ?
        ''', (password_hash, username))
        
        rows_affected = cursor.rowcount
        conn.commit()
        conn.close()
        
        return rows_affected > 0


if __name__ == "__main__":
    db = Database()
    print("Base de datos inicializada correctamente")