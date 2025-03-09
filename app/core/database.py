from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import redis
import os
from dotenv import load_dotenv
import logging

# Load environment variables
load_dotenv()

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Database URL - Use SQLite for testing if PostgreSQL is not available
POSTGRES_URL = os.getenv(
    "DATABASE_URL", 
    "postgresql://neondb_owner:npg_1GlSCKuYVBZ5@ep-autumn-poetry-a1nqtaqp-pooler.ap-southeast-1.aws.neon.tech/neondb?sslmode=require"
)

# Use SQLite for local testing
SQLITE_URL = "sqlite:///./test.db"

# Try PostgreSQL first, fall back to SQLite
try:
    # Test PostgreSQL connection
    test_engine = create_engine(POSTGRES_URL, connect_args={"connect_timeout": 3})
    with test_engine.connect() as conn:
        pass
    # If connection successful, use PostgreSQL
    DATABASE_URL = POSTGRES_URL
    logger.info("Using PostgreSQL database")
except Exception as e:
    # If connection fails, use SQLite
    DATABASE_URL = SQLITE_URL
    logger.warning(f"PostgreSQL connection failed: {str(e)}. Using SQLite database instead.")

# Redis Configuration
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))
REDIS_DB = int(os.getenv("REDIS_DB", "0"))
REDIS_PASSWORD = os.getenv("REDIS_PASSWORD", None)

# Create SQLAlchemy engine
if DATABASE_URL.startswith('sqlite'):
    engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
else:
    engine = create_engine(DATABASE_URL)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create base class for models
Base = declarative_base()

# Create Redis connection
try:
    redis_client = redis.Redis(
        host=REDIS_HOST,
        port=REDIS_PORT,
        db=REDIS_DB,
        password=REDIS_PASSWORD,
        decode_responses=True,
        socket_connect_timeout=1,  # Short timeout for connection
        socket_timeout=1  # Short timeout for operations
    )
    # Test connection
    redis_client.ping()
    logger.info("Redis connection successful")
except redis.ConnectionError:
    logger.warning("Redis connection failed. Using mock Redis client.")
    # Create a mock Redis client
    class MockRedis:
        def __init__(self):
            self.data = {}
            
        def get(self, key):
            return self.data.get(key)
            
        def set(self, key, value):
            self.data[key] = value
            return True
            
        def setex(self, key, time, value):
            self.data[key] = value
            return True
            
        def exists(self, key):
            return key in self.data
            
        def delete(self, key):
            if key in self.data:
                del self.data[key]
                return 1
            return 0
            
        def ping(self):
            return True
    
    redis_client = MockRedis()

# Dependency to get DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Dependency to get Redis client
def get_redis():
    try:
        yield redis_client
    finally:
        # Redis connections are returned to the connection pool automatically
        pass 