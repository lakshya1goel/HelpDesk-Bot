from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import Base
from config import config

if not config.validate_database_config():
    raise ValueError("DATABASE_URL environment variable is required!")

engine = create_engine(
    config.DATABASE_URL, 
    connect_args={"check_same_thread": False} if "sqlite" in config.DATABASE_URL else {}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create tables
Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()