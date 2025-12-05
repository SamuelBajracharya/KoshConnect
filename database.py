from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv
from sqlalchemy.exc import OperationalError
import os, time

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

# Disable SSL for internal Railway connections
connect_args = {}
if DATABASE_URL and "railway.internal" not in DATABASE_URL:
    connect_args["sslmode"] = "require"

# Retry if DB not ready yet
for i in range(10):
    try:
        engine = create_engine(DATABASE_URL, connect_args=connect_args)
        with engine.connect() as conn:
            print("✅ Database connection established.")
        break
    except OperationalError as e:
        print(f"⏳ Waiting for database... ({i+1}/10) {e}")
        time.sleep(3)
else:
    raise RuntimeError("❌ Could not connect to the database after 10 attempts.")

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def create_tables():
    Base.metadata.create_all(bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
