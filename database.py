from sqlalchemy import create_engine, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv
from sqlalchemy.exc import OperationalError
import os, time

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
connect_args = {}  # Define connect_args as an empty dictionary

# Retry if DB not ready yet
for i in range(10):
    try:
        engine = create_engine(DATABASE_URL, connect_args=connect_args)
        with engine.connect() as conn:
            print("Database connection established.")
        break
    except OperationalError as e:
        print(f"Waiting for database... ({i+1}/10) {e}")
        time.sleep(3)
else:
    raise RuntimeError("Could not connect to the database after 10 attempts.")

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def create_tables():
    Base.metadata.create_all(bind=engine)


def run_bootstrap_migrations():
    # create_all creates missing tables, but does not alter existing ones.
    # This lightweight bootstrap patch keeps deployed sandbox databases compatible.
    statements = [
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS phonenumber_encrypted VARCHAR",
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS phonenumber_hash VARCHAR(64)",
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS email_encrypted VARCHAR",
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS email_hash VARCHAR(64)",
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS role VARCHAR(30) NOT NULL DEFAULT 'customer'",
        "ALTER TABLE users ALTER COLUMN phonenumber DROP NOT NULL",
        "ALTER TABLE accounts ADD COLUMN IF NOT EXISTS account_number_encrypted VARCHAR",
        "ALTER TABLE accounts ADD COLUMN IF NOT EXISTS account_number_hash VARCHAR(64)",
        "ALTER TABLE transactions ADD COLUMN IF NOT EXISTS category_purpose_code VARCHAR(4) NOT NULL DEFAULT 'OTHR'",
        "ALTER TABLE transactions ADD COLUMN IF NOT EXISTS mcc INTEGER NOT NULL DEFAULT 5999",
        "ALTER TABLE transactions ADD COLUMN IF NOT EXISTS proprietary_bank_code VARCHAR(20) NOT NULL DEFAULT 'GIBL-FT-01'",
        "ALTER TABLE transactions ADD COLUMN IF NOT EXISTS merchant_logo_url VARCHAR",
        "ALTER TABLE transactions ADD COLUMN IF NOT EXISTS merchant_verified_status BOOLEAN NOT NULL DEFAULT false",
        "CREATE TABLE IF NOT EXISTS idempotency_records (id UUID PRIMARY KEY, idempotency_key VARCHAR(128) NOT NULL UNIQUE, endpoint VARCHAR(128) NOT NULL, request_hash VARCHAR(64) NOT NULL, response_status_code INTEGER NOT NULL, response_body VARCHAR NOT NULL, created_at TIMESTAMPTZ NOT NULL DEFAULT NOW())",
        "CREATE INDEX IF NOT EXISTS ix_users_phonenumber_hash ON users (phonenumber_hash)",
        "CREATE UNIQUE INDEX IF NOT EXISTS uq_users_email_hash ON users (email_hash)",
        "CREATE UNIQUE INDEX IF NOT EXISTS uq_accounts_account_number_hash ON accounts (account_number_hash)",
        "CREATE INDEX IF NOT EXISTS ix_idempotency_records_idempotency_key ON idempotency_records (idempotency_key)",
    ]

    with engine.begin() as conn:
        for statement in statements:
            conn.execute(text(statement))


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
