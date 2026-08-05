import asyncio
from database.connection import SessionLocal
from sqlalchemy import text

async def f():
    async with SessionLocal() as db:
        res = await db.execute(text('SELECT * FROM roles'))
        print("Roles:", res.fetchall())
        res2 = await db.execute(text('SELECT username, industry FROM users WHERE role_id = 3'))
        print("Users with role 3:", res2.fetchall())
        res3 = await db.execute(text('SELECT * FROM attention_timeline LIMIT 5'))
        print("Attention:", res3.fetchall())

if __name__ == "__main__":
    asyncio.run(f())
