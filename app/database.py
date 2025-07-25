from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from configparser import ConfigParser
from urllib.parse import quote_plus

# Load config from ini file
config = ConfigParser()
config.read('config.ini')

# Get database configuration
DB_SERVER = config.get('DATABASE', 'SERVER')
DB_NAME = config.get('DATABASE', 'DATABASE')
DB_USER = config.get('DATABASE', 'USERNAME')
DB_PASSWORD = quote_plus(config.get('DATABASE', 'PASSWORD'))

# Construct SQLAlchemy connection string
SQLALCHEMY_DATABASE_URL = (
    f"mssql+pyodbc://{DB_USER}:{DB_PASSWORD}@{DB_SERVER}/{DB_NAME}"
    "?driver=ODBC+Driver+17+for+SQL+Server"
)

# Create engine with better debugging and connection settings
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    echo=True,  # Set to False in production
    pool_pre_ping=True,  # Enables connection testing before usage
    pool_recycle=3600  # Recycle connections after an hour
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()