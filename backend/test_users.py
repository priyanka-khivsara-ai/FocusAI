
import asyncio
from database.connection import SessionLocal
from sqlalchemy import text

async def f():
    async with SessionLocal() as db:
        res = await db.execute(text("SELECT username, role_id FROM users WHERE role_id=3"))
        print(res.fetchall())

if __name__ == "__main__":
    asyncio.run(f())

