import asyncio
from database.connection import SessionLocal
from sqlalchemy import text

async def upgrade_schema():
    print("Adding industry column to users...")
    async with SessionLocal() as db:
        try:
            await db.execute(text("ALTER TABLE users ADD COLUMN industry VARCHAR DEFAULT 'Education'"))
            await db.commit()
            print("Successfully added industry column to users.")
        except Exception as e:
            print(f"Error adding to users (might already exist): {e}")

    print("Adding industry column to workspaces...")
    async with SessionLocal() as db:
        try:
            await db.execute(text("ALTER TABLE workspaces ADD COLUMN industry VARCHAR DEFAULT 'Education'"))
            await db.commit()
            print("Successfully added industry column to workspaces.")
        except Exception as e:
            print(f"Error adding to workspaces (might already exist): {e}")

if __name__ == "__main__":
    asyncio.run(upgrade_schema())
