import asyncio
from database import engine, Base, SessionLocal
from models import TelemetryRecord, UserAccount
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

    print("Seeding default accounts...")
    async with SessionLocal() as db:
        super_admin = UserAccount(user_id="admin", password="password123", role="Super Admin")
        admin_acc = UserAccount(user_id="priyanka", password="priyanka123", role="Admin")
        user_acc = UserAccount(user_id="user", password="user123", role="User")
        
        db.add_all([super_admin, admin_acc, user_acc])
        await db.commit()
        print("Default accounts created!")
        print("- Super Admin: admin / password123")
        print("- Admin: priyanka / priyanka123")
        print("- User: user / user123")

if __name__ == "__main__":
    asyncio.run(reset_db())
