import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy import text
from connection import Base, DATABASE_URL

# Import all models so Base knows about them
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models.relational import *
from models.timescale import *

engine = create_async_engine(DATABASE_URL, echo=True)

async def init_models():
    async with engine.begin() as conn:
        print("Dropping existing tables...")
        await conn.run_sync(Base.metadata.drop_all)
        
        print("Creating all tables...")
        await conn.run_sync(Base.metadata.create_all)

        print("Seeding initial roles and users...")
        await conn.execute(text("INSERT INTO roles (id, name, description) VALUES (1, 'Super Admin', 'Full system access'), (2, 'Admin', 'Dashboard access'), (3, 'User', 'Student tracking')"))
        
        users = [
            ("FocusAI", "FocusAI", "focusai@example.com", 1),
            ("Priyanka", "Priyanka", "priyanka@example.com", 2),
            ("Shubham", "Shubham", "shubham@example.com", 2),
            ("Pranali", "Pranali", "pranali@example.com", 2),
            ("user1", "user1", "user1@example.com", 3),
            ("user2", "user2", "user2@example.com", 3)
        ]
        
        for u in users:
            await conn.execute(text(
                "INSERT INTO users (username, password, email, role_id) VALUES (:u, :p, :e, :r)"
            ), {"u": u[0], "p": u[1], "e": u[2], "r": u[3]})

if __name__ == "__main__":
    asyncio.run(init_models())
    print("Database initialization complete.")
