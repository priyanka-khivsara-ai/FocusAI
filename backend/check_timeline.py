
import asyncio
from database.connection import SessionLocal
from sqlalchemy import text

async def f():
    async with SessionLocal() as db:
        res = await db.execute(text("SELECT a.session_id, a.user_id, a.timestamp, r.name FROM attention_timeline a LEFT JOIN users u ON a.user_id=u.username LEFT JOIN roles r ON u.role_id=r.id ORDER BY a.timestamp DESC LIMIT 10"))
        print(res.fetchall())

if __name__ == "__main__":
    asyncio.run(f())

