import asyncio
from database.connection import Base, engine
from models.relational import Workspace, Project, Enrollment, Session, Calibration, User, Role
from models.timescale import AttentionTimeline, EmotionTimeline, FacialMetrics

async def reset():
    async with engine.begin() as conn:
        print("Dropping tables...")
        await conn.run_sync(Base.metadata.drop_all)
        print("Creating tables...")
        await conn.run_sync(Base.metadata.create_all)
        
    # Seed roles
    from database.connection import SessionLocal
    async with SessionLocal() as db:
        for r_name in ["Admin", "Host", "User"]:
            db.add(Role(name=r_name))
        await db.commit()
        
        # Seed an admin
        # Just plain text for local demo as per previous implementation
        db.add(User(username="admin", email="admin@focusai.com", password="password", role_id=1))
        await db.commit()
    print("Done!")

if __name__ == "__main__":
    asyncio.run(reset())
