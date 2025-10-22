USE atencion_clientes;

-- Tabla para datos específicos de Retención
CREATE TABLE IF NOT EXISTS clientes_retencion (
    id INT AUTO_INCREMENT PRIMARY KEY,
    cliente_id INT,
    tipo_solicitud VARCHAR(255),
    motivo_solicitud TEXT,
    nombre_titular VARCHAR(255),
    dni VARCHAR(50),
    telefono_contacto VARCHAR(50),
    telefono_afectado VARCHAR(50),
    accion_ofrecida TEXT,
    otros_motivo TEXT,
    FOREIGN KEY (cliente_id) REFERENCES clientes(id) ON DELETE SET NULL
);

-- Tabla para datos específicos de Cuestionamiento
CREATE TABLE IF NOT EXISTS clientes_cuestionamiento (
    id INT AUTO_INCREMENT PRIMARY KEY,
    cliente_id INT,
    submotivo VARCHAR(255),
    servicios_facturados TEXT,
    informacion_entregada TEXT,
    sn VARCHAR(100),
    otros_observaciones TEXT,
    FOREIGN KEY (cliente_id) REFERENCES clientes(id) ON DELETE SET NULL
);

-- Tabla para datos específicos de Atención Técnica
CREATE TABLE IF NOT EXISTS clientes_tecnica (
    id INT AUTO_INCREMENT PRIMARY KEY,
    cliente_id INT,
    linea_afectada VARCHAR(50),
    linea_adicional VARCHAR(50),
    inconveniente_reportado TEXT,
    FOREIGN KEY (cliente_id) REFERENCES clientes(id) ON DELETE SET NULL
);
