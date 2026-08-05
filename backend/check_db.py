import asyncio
from database.connection import SessionLocal
from sqlalchemy import text

async def check():
    async with SessionLocal() as db:
        res = await db.execute(text("SELECT username, industry FROM users LIMIT 10"))
        print("Users:", res.fetchall())
        res_ws = await db.execute(text("SELECT name, industry FROM workspaces LIMIT 10"))
        print("Workspaces:", res_ws.fetchall())

if __name__ == "__main__":
    asyncio.run(check())
