import asyncio
from sqlalchemy import text
from database import engine, Base
import models  # Important: Import models so Base.metadata knows about them

async def init_models():
    async with engine.begin() as conn:
        print("Dropping existing tables (if any)...")
        await conn.run_sync(Base.metadata.drop_all)
        
        print("Creating newly defined tables...")
        await conn.run_sync(Base.metadata.create_all)
        
        print("Executing TimescaleDB Hypertable conversion...")
        # The create_hypertable command tells TimescaleDB to partition this table
        # into chunks based on the 'timestamp' column, massively speeding up time-series queries.
        await conn.execute(
            text("SELECT create_hypertable('telemetry_records', 'timestamp', if_not_exists => TRUE);")
        )
        
    print("Database successfully initialized and optimized!")

if __name__ == "__main__":
    asyncio.run(init_models())
