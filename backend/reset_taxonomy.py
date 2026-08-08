import asyncio
from database.connection import SessionLocal
from sqlalchemy import text
async def reset_db():
    async with SessionLocal() as db:
        await db.execute(text("TRUNCATE TABLE enrollments CASCADE"))
        await db.execute(text("TRUNCATE TABLE projects CASCADE"))
        await db.execute(text("TRUNCATE TABLE workspaces CASCADE"))
        await db.execute(text("DELETE FROM users WHERE role_id != 1"))
        await db.commit()
if __name__ == "__main__": asyncio.run(reset_db())
