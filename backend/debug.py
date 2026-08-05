import asyncio
from database.connection import SessionLocal
from api.users import list_users

async def run():
    async with SessionLocal() as db:
        try:
            res = await list_users("Education", db)
            print(res)
        except Exception as e:
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(run())
