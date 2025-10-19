USE atencion_clientes;

-- Deshabilitar restricciones de clave foránea temporalmente
SET FOREIGN_KEY_CHECKS = 0;

-- Borrar todos los datos de las tablas
DELETE FROM tnps;
DELETE FROM clientes;

-- Resetear los auto-incrementos para empezar desde 1
ALTER TABLE clientes AUTO_INCREMENT = 1;
ALTER TABLE tnps AUTO_INCREMENT = 1;

-- Rehabilitar restricciones de clave foránea
SET FOREIGN_KEY_CHECKS = 1;