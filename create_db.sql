CREATE DATABASE IF NOT EXISTS atencion_clientes;

USE atencion_clientes;

CREATE TABLE IF NOT EXISTS clientes (
    id INT AUTO_INCREMENT PRIMARY KEY,
    nombre VARCHAR(255) NOT NULL,
    numero VARCHAR(50),
    sn VARCHAR(100),
    motivo_llamada TEXT,
    notas TEXT,
    tipo_solicitud VARCHAR(255),
    motivo_solicitud TEXT,
    nombre_titular VARCHAR(255),
    dni VARCHAR(50),
    telefono_contacto VARCHAR(50),
    telefono_afectado VARCHAR(50),
    accion_ofrecida TEXT,
    otros_motivo TEXT,
    fecha_llamada TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    session_id VARCHAR(64)
);

CREATE TABLE IF NOT EXISTS tnps (
    id INT AUTO_INCREMENT PRIMARY KEY,
    tnps_score INT CHECK (tnps_score >= 0 AND tnps_score <= 9),
    tnps_calculated INT,
    fecha_tnps TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);