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

def save_client(nombre, numero, sn, motivo, **kwargs):
    conn = connect_db()
    with conn.cursor() as cursor:
        sql = """INSERT INTO clientes (nombre, numero, sn, motivo_llamada, tipo_solicitud, motivo_solicitud, nombre_titular, dni, telefono_contacto, telefono_afectado, accion_ofrecida, otros_motivo, notas) \
                 VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"""
        cursor.execute(sql, (nombre, numero, sn, motivo, 
                             kwargs.get('tipo_solicitud'), kwargs.get('motivo_solicitud'), 
                             kwargs.get('nombre_titular'), kwargs.get('dni'), 
                             kwargs.get('telefono_contacto'), kwargs.get('telefono_afectado'), 
                             kwargs.get('accion_ofrecida'), kwargs.get('otros_motivo'), kwargs.get('notas')))
        client_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return client_id

def save_tnps(tnps_score, calculated):
    conn = connect_db()
    with conn.cursor() as cursor:
        sql = "INSERT INTO tnps (tnps_score, tnps_calculated) VALUES (%s, %s)"
        cursor.execute(sql, (tnps_score, calculated))
    conn.commit()
    conn.close()
    return calculated
