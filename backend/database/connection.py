from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy.orm import declarative_base

# Connect to SQLite instead of TimescaleDB
DATABASE_URL = "sqlite+aiosqlite:///focus_db.sqlite3"

# Create the asynchronous engine
engine = create_async_engine(DATABASE_URL, echo=False)

# Create a session factory
SessionLocal = async_sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for our database models
Base = declarative_base()

# Dependency for FastAPI to get DB sessions
async def get_db():
    async with SessionLocal() as session:
        yield session
