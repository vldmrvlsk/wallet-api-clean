
import asyncio
import uuid

from app.db import SessionLocal, engine
from app.models import Wallet


async def main():
    wallet_uuid = uuid.uuid4()

    async with SessionLocal() as session:
        wallet = Wallet(
            id=wallet_uuid,
            balance=0,
        )
        session.add(wallet)
        await session.commit()

    print(f"Created wallet: {wallet_uuid}")
    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
