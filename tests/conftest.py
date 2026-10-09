
import uuid
from decimal import Decimal

import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import delete

from app.db import SessionLocal
from app.models import Wallet
from main import app


@pytest_asyncio.fixture(loop_scope="session")
async def client():
    transport = ASGITransport(app=app)

    async with AsyncClient(
        transport=transport,
        base_url="http://test",
    ) as test_client:
        yield test_client


@pytest_asyncio.fixture(loop_scope="session")
async def test_wallet():
    wallet_uuid = uuid.uuid4()

    async with SessionLocal() as session:
        wallet = Wallet(
            id=wallet_uuid,
            balance=Decimal("100.00"),
        )
        session.add(wallet)
        await session.commit()

    yield wallet_uuid

    async with SessionLocal() as session:
        await session.execute(
            delete(Wallet).where(Wallet.id == wallet_uuid)
        )
        await session.commit()
