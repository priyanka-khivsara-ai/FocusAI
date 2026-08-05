import asyncio
from database import engine, Base
from models import TelemetryRecord
from sqlalchemy import text

async def reset_db():
    print("Dropping all existing tables...")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        print("Existing tables dropped.")

    print("Recreating tables with new Multi-Tenant schema...")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        print("Schema successfully applied!")

    print("Configuring TimescaleDB Hypertable...")
    async with engine.begin() as conn:
        try:
            await conn.execute(text("SELECT create_hypertable('telemetry_records', 'timestamp', if_not_exists => TRUE);"))
            print("Hypertable enabled!")
        except Exception as e:
            print(f"Hypertable configuration error (might already exist): {e}")

if __name__ == "__main__":
    asyncio.run(reset_db())
