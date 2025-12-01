"""
Módulo de base de datos usando SQLite.
Gestiona clientes, TNPS y credenciales.
"""
import sqlite3
import os
from contextlib import contextmanager

# Ruta de la base de datos SQLite (en la raíz del proyecto)
DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'data', 'atencion_clientes.db')


def _ensure_data_dir():
    """Asegura que el directorio data existe."""
    data_dir = os.path.dirname(DB_PATH)
    if not os.path.exists(data_dir):
        os.makedirs(data_dir)


@contextmanager
def get_connection():
    """Context manager para conexiones a SQLite."""
    _ensure_data_dir()
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()


def init_db():
    """Inicializa la base de datos creando todas las tablas necesarias."""
    with get_connection() as conn:
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS clientes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nombre TEXT NOT NULL,
                numero TEXT,
                sn TEXT,
                motivo_llamada TEXT,
                notas TEXT,
                tipo_solicitud TEXT,
                motivo_solicitud TEXT,
                nombre_titular TEXT,
                dni TEXT,
                telefono_contacto TEXT,
                telefono_afectado TEXT,
                accion_ofrecida TEXT,
                otros_motivo TEXT,
                fecha_llamada TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                session_id TEXT
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS tnps (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                tnps_score INTEGER CHECK (tnps_score >= 0 AND tnps_score <= 9),
                tnps_calculated INTEGER,
                fecha_tnps TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS credentials (
                key TEXT PRIMARY KEY,
                value TEXT
            )
        ''')
        
        conn.commit()


def ensure_credentials_table():
    """Alias para compatibilidad."""
    init_db()


def get_credential(key):
    """Obtiene una credencial por su clave."""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT value FROM credentials WHERE key = ?", (key,))
        row = cursor.fetchone()
        return row['value'] if row else None


def set_credential(key, value):
    """Guarda o actualiza una credencial."""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT OR REPLACE INTO credentials (key, value) VALUES (?, ?)",
            (key, value)
        )
        conn.commit()


def save_client(nombre, numero, sn, motivo, **kwargs):
    """Guarda un cliente en la base de datos."""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO clientes (
                nombre, numero, sn, motivo_llamada, tipo_solicitud, 
                motivo_solicitud, nombre_titular, dni, telefono_contacto, 
                telefono_afectado, accion_ofrecida, otros_motivo, notas, session_id
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            nombre, numero, sn, motivo,
            kwargs.get('tipo_solicitud'),
            kwargs.get('motivo_solicitud'),
            kwargs.get('nombre_titular'),
            kwargs.get('dni'),
            kwargs.get('telefono_contacto'),
            kwargs.get('telefono_afectado'),
            kwargs.get('accion_ofrecida'),
            kwargs.get('otros_motivo'),
            kwargs.get('notas'),
            kwargs.get('session_id')
        ))
        conn.commit()
        return cursor.lastrowid


def save_tnps(tnps_score, calculated=None):
    """Guarda un registro TNPS."""
    from src.utils.helpers import calculate_tnps_point
    
    try:
        score = int(tnps_score)
    except (ValueError, TypeError):
        score = 0
    
    if calculated is None:
        calculated = calculate_tnps_point(score)
    
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO tnps (tnps_score, tnps_calculated) VALUES (?, ?)",
            (score, calculated)
        )
        conn.commit()
        return calculated


def get_clients_grouped_by_day(limit=500):
    """Obtiene clientes ordenados por fecha (más recientes primero)."""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT id, nombre, numero, sn, dni, motivo_llamada, 
                   fecha_llamada, COALESCE(notas, '') as notas 
            FROM clientes 
            ORDER BY fecha_llamada DESC 
            LIMIT ?
        ''', (limit,))
        return [dict(row) for row in cursor.fetchall()]


def get_tnps_today():
    """Obtiene los puntajes TNPS del día actual."""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT tnps_score FROM tnps 
            WHERE DATE(fecha_tnps) = DATE('now', 'localtime')
        ''')
        return [row['tnps_score'] for row in cursor.fetchall()]


# Inicializar la base de datos al importar el módulo
init_db()
