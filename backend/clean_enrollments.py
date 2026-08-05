import asyncio
from database.connection import SessionLocal
from sqlalchemy import text

async def f():
    async with SessionLocal() as db:
        await db.execute(text("""
            DELETE FROM enrollments e1 USING enrollments e2
            WHERE e1.id > e2.id 
            AND e1.user_id = e2.user_id 
            AND e1.workspace_id = e2.workspace_id 
            AND (e1.project_id = e2.project_id OR (e1.project_id IS NULL AND e2.project_id IS NULL));
        """))
        await db.commit()
        print("Duplicates removed.")

if __name__ == "__main__":
    asyncio.run(f())
