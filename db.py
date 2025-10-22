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
                   "nombre_titular, dni, telefono_contacto, telefono_afectado, accion_ofrecida, otros_motivo, notas, session_id) "
                   "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)")
            params = (
                nombre, numero, sn, motivo,
                kwargs.get('tipo_solicitud'), kwargs.get('motivo_solicitud'),
                kwargs.get('nombre_titular'), kwargs.get('dni'),
                kwargs.get('telefono_contacto'), kwargs.get('telefono_afectado'),
                kwargs.get('accion_ofrecida'), kwargs.get('otros_motivo'), kwargs.get('notas'), kwargs.get('session_id')
            )
            try:
                cursor.execute(sql, params)
            except Exception as e:
                # Si falla (p. ej. columna notas o session_id no existe), intentamos un INSERT de compatibilidad
                try:
                    # Versión más pequeña: sin 'notas' ni 'session_id' para compatibilidad con esquemas antiguos
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
                except Exception:
                    # Re-raise para que el caller vea el error original
                    raise
            client_id = cursor.lastrowid
            # Intentar insertar detalles específicos por motivo en tablas auxiliares si existen
            try:
                if motivo and motivo.lower().startswith('retenci'):
                    # campos: tipo_solicitud, motivo_solicitud, nombre_titular, dni, telefono_contacto, telefono_afectado, accion_ofrecida, otros_motivo
                    try:
                        cursor.execute(
                            "INSERT INTO clientes_retencion (cliente_id, tipo_solicitud, motivo_solicitud, nombre_titular, dni, telefono_contacto, telefono_afectado, accion_ofrecida, otros_motivo) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)",
                            (client_id, kwargs.get('tipo_solicitud'), kwargs.get('motivo_solicitud'), kwargs.get('nombre_titular'), kwargs.get('dni'), kwargs.get('telefono_contacto'), kwargs.get('telefono_afectado'), kwargs.get('accion_ofrecida'), kwargs.get('otros_motivo'))
                        )
                    except Exception:
                        # ignorar si tabla no existe o falla
                        pass
                elif 'cuestionamiento' in (motivo or '').lower():
                    try:
                        cursor.execute(
                            "INSERT INTO clientes_cuestionamiento (cliente_id, submotivo, servicios_facturados, informacion_entregada, sn, otros_observaciones) VALUES (%s,%s,%s,%s,%s,%s)",
                            (client_id, kwargs.get('submotivo'), kwargs.get('servicios_facturados'), kwargs.get('informacion_entregada'), sn, kwargs.get('otros_observaciones'))
                        )
                    except Exception:
                        pass
                elif 'técnica' in (motivo or '').lower() or 'tecnica' in (motivo or '').lower():
                    try:
                        cursor.execute(
                            "INSERT INTO clientes_tecnica (cliente_id, linea_afectada, linea_adicional, inconveniente_reportado) VALUES (%s,%s,%s,%s)",
                            (client_id, kwargs.get('linea_afectada') or numero, kwargs.get('linea_adicional'), kwargs.get('inconveniente_reportado'))
                        )
                    except Exception:
                        pass
            except Exception:
                # no bloquear por detalles
                pass
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
