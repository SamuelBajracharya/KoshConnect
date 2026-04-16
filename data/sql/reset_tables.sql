-- WARNING: destructive reset for sandbox only.
-- Drops all app tables so fresh schema/data can be reapplied.

DROP TABLE IF EXISTS idempotency_records CASCADE;
DROP TABLE IF EXISTS stock_instruments CASCADE;
DROP TABLE IF EXISTS transactions CASCADE;
DROP TABLE IF EXISTS accounts CASCADE;
DROP TABLE IF EXISTS users CASCADE;
