import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# Get database URL from environment variable (set by Render)
DATABASE_URL = os.environ.get("DATABASE_URL")

if not DATABASE_URL:  # Fallback for local development
    from configparser import ConfigParser
    config = ConfigParser()
    config.read('config.ini')
    
    user = config.get('DATABASE', 'USERNAME')
    password = config.get('DATABASE', 'PASSWORD')
    host = config.get('DATABASE', 'SERVER')
    db = config.get('DATABASE', 'DATABASE')
    DATABASE_URL = f"postgresql://{user}:{password}@{host}/{db}"

# Handle different PostgreSQL URL formats
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

# Create engine with better connection settings
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    pool_recycle=3600
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()