
import asyncio

from sqlalchemy import text

from app.db import SessionLocal, engine


async def main():
    async with SessionLocal() as session:
        result = await session.execute(text("SELECT 1"))
        print("Результат проверки:", result.scalar_one())

    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
