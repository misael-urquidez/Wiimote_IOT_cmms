-- CMMS-Wii - inicializador MySQL/XAMPP
-- Uso recomendado:
--   1. Importa este archivo en phpMyAdmin o ejecuta:
--      mysql -u root < database/mysql_xampp_init.sql
--   2. Ejecuta las migraciones de Django con CMMS_DB=mysql.

CREATE DATABASE IF NOT EXISTS cmms_wii
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;

USE cmms_wii;

-- Datos de ejemplo opcionales.
-- Ejecutalos despues de correr: py manage.py migrate
--
-- INSERT INTO equipos_equipo
--   (nombre, ubicacion, icono, umbral_vibracion, umbral_inclinacion, activo)
-- VALUES
--   ('Solder Paste Printer', 'Linea SMT', '⚙️', 4.0, 15.0, 1),
--   ('Pick & Place', 'Linea SMT', '⚙️', 4.0, 15.0, 1),
--   ('Horno Reflow', 'Linea SMT', '⚙️', 4.0, 15.0, 1),
--   ('Cinta Transportadora', 'Linea SMT', '⚙️', 4.0, 15.0, 1),
--   ('AOI', 'Inspeccion', '⚙️', 4.0, 15.0, 1),
--   ('Flying Probe / ICT', 'Pruebas', '⚙️', 4.0, 15.0, 1),
--   ('Selective Soldering', 'Ensamble', '⚙️', 4.0, 15.0, 1);
