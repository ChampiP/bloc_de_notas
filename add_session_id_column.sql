-- Migration: add session_id column to clientes table
ALTER TABLE clientes ADD COLUMN IF NOT EXISTS session_id VARCHAR(64);

-- Optional: create an index for faster queries by session
CREATE INDEX IF NOT EXISTS idx_clientes_session_id ON clientes(session_id);
