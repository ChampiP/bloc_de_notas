import pymysql

def connect_db():
    return pymysql.connect(
        host='localhost',
        user='root',
        password='',
        database='atencion_clientes',
        charset='utf8mb4',
        cursorclass=pymysql.cursors.DictCursor
    )


def ensure_credentials_table():
    # Crea una pequeña tabla clave/valor para guardar credenciales si no existe.
    conn = connect_db()
    with conn.cursor() as cursor:
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS credentials (
            `key` VARCHAR(64) PRIMARY KEY,
            `value` TEXT
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
        """)
    conn.commit()
    conn.close()


def get_credential(key):
    conn = connect_db()
    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT `value` FROM credentials WHERE `key` = %s", (key,))
            row = cursor.fetchone()
            return row['value'] if row else None
    finally:
        conn.close()


def set_credential(key, value):
    conn = connect_db()
    try:
        with conn.cursor() as cursor:
            # upsert
            cursor.execute("INSERT INTO credentials (`key`, `value`) VALUES (%s, %s) ON DUPLICATE KEY UPDATE `value` = VALUES(`value`)", (key, value))
        conn.commit()
    finally:
        conn.close()

def save_client(nombre, numero, sn, motivo, **kwargs):
    conn = connect_db()
    try:
        with conn.cursor() as cursor:
            # Intentamos insertar todas las columnas esperadas
            sql = ("INSERT INTO clientes (nombre, numero, sn, motivo_llamada, tipo_solicitud, motivo_solicitud, "
                   "nombre_titular, dni, telefono_contacto, telefono_afectado, accion_ofrecida, otros_motivo, notas) "
                   "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)")
            params = (
                nombre, numero, sn, motivo,
                kwargs.get('tipo_solicitud'), kwargs.get('motivo_solicitud'),
                kwargs.get('nombre_titular'), kwargs.get('dni'),
                kwargs.get('telefono_contacto'), kwargs.get('telefono_afectado'),
                kwargs.get('accion_ofrecida'), kwargs.get('otros_motivo'), kwargs.get('notas')
            )
            try:
                cursor.execute(sql, params)
            except Exception as e:
                # Si falla (p. ej. columna notas no existe), intentamos un INSERT más pequeño que no incluya notas
                try:
                    sql2 = ("INSERT INTO clientes (nombre, numero, sn, motivo_llamada, tipo_solicitud, motivo_solicitud, "
                            "nombre_titular, dni, telefono_contacto, telefono_afectado, accion_ofrecida, otros_motivo) "
                            "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)")
                    params2 = (
                        nombre, numero, sn, motivo,
                        kwargs.get('tipo_solicitud'), kwargs.get('motivo_solicitud'),
                        kwargs.get('nombre_titular'), kwargs.get('dni'),
                        kwargs.get('telefono_contacto'), kwargs.get('telefono_afectado'),
                        kwargs.get('accion_ofrecida'), kwargs.get('otros_motivo')
                    )
                    cursor.execute(sql2, params2)
                except Exception as e2:
                    # Re-raise the original or new exception for the caller to handle/log
                    raise
            client_id = cursor.lastrowid
        conn.commit()
        return client_id
    finally:
        try:
            conn.close()
        except Exception:
            pass

def save_tnps(tnps_score, calculated=None):
    # Usa la función utilitaria compartida si está disponible
    try:
        from utils import calculate_tnps_point
    except Exception:
        calculate_tnps_point = None

    try:
        score = int(tnps_score)
    except Exception:
        score = 0

    if calculated is None:
        if calculate_tnps_point:
            calculated = calculate_tnps_point(score)
        else:
            # fallback
            if score >= 8:
                calculated = 100
            elif score >= 6:
                calculated = 50
            else:
                calculated = 0

    conn = connect_db()
    try:
        with conn.cursor() as cursor:
            sql = "INSERT INTO tnps (tnps_score, tnps_calculated) VALUES (%s, %s)"
            cursor.execute(sql, (score, calculated))
        conn.commit()
        return calculated
    finally:
        try:
            conn.close()
        except Exception:
            pass

def get_clients_grouped_by_day(limit=500):
    """Devuelve una lista de filas de clientes ordenadas por fecha (más recientes primero).
    El modal puede agrupar por fecha. Limit por seguridad para no cargar demasiadas filas.
    Cada fila es un dict con columnas: id, nombre, numero, sn, dni, motivo_llamada, fecha_llamada, notas
    """
    conn = connect_db()
    try:
        with conn.cursor() as cursor:
            sql = ("SELECT id, nombre, numero, sn, dni, motivo_llamada, fecha_llamada, COALESCE(notas, '') as notas "
                   "FROM clientes ORDER BY fecha_llamada DESC LIMIT %s")
            cursor.execute(sql, (limit,))
            rows = cursor.fetchall()
        return rows
    finally:
        try:
            conn.close()
        except Exception:
            pass
