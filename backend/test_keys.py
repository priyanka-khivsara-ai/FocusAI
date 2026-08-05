import asyncio
from database.connection import SessionLocal
from sqlalchemy import text

async def f():
    async with SessionLocal() as db:
        res = await db.execute(text("SELECT u.username, p.id as project_id FROM enrollments e JOIN users u ON e.user_id = u.id JOIN projects p ON e.project_id = p.id"))
        print("Enrollments:", res.fetchall())
        
if __name__ == "__main__":
    asyncio.run(f())
