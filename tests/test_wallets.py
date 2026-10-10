
import asyncio
import uuid
from decimal import Decimal

import pytest
from sqlalchemy import select, update
from sqlalchemy.exc import IntegrityError

from app.db import SessionLocal
from app.models import Wallet


@pytest.mark.asyncio(loop_scope="session")
async def test_get_existing_wallet(client, test_wallet):
    response = await client.get(
        f"/api/v1/wallets/{test_wallet}"
    )

    assert response.status_code == 200
    assert response.json()["wallet_uuid"] == str(test_wallet)
    assert Decimal(response.json()["balance"]) == Decimal("100.00")


@pytest.mark.asyncio(loop_scope="session")
async def test_get_nonexistent_wallet(client):
    wallet_uuid = uuid.uuid4()

    response = await client.get(
        f"/api/v1/wallets/{wallet_uuid}"
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Wallet not found"


@pytest.mark.asyncio(loop_scope="session")
async def test_deposit(client, test_wallet):
    response = await client.post(
        f"/api/v1/wallets/{test_wallet}/operation",
        json={
            "operation_type": "DEPOSIT",
            "amount": "25.00",
        },
    )

    assert response.status_code == 200
    assert Decimal(response.json()["balance"]) == Decimal("125.00")


@pytest.mark.asyncio(loop_scope="session")
async def test_withdraw(client, test_wallet):
    response = await client.post(
        f"/api/v1/wallets/{test_wallet}/operation",
        json={
            "operation_type": "WITHDRAW",
            "amount": "30.00",
        },
    )

    assert response.status_code == 200
    assert Decimal(response.json()["balance"]) == Decimal("70.00")


@pytest.mark.asyncio(loop_scope="session")
async def test_withdraw_insufficient_funds(client, test_wallet):
    response = await client.post(
        f"/api/v1/wallets/{test_wallet}/operation",
        json={
            "operation_type": "WITHDRAW",
            "amount": "150.00",
        },
    )

    assert response.status_code == 409
    assert response.json()["detail"] == "Insufficient funds"

    # Неудачная операция не должна менять баланс.
    balance_response = await client.get(
        f"/api/v1/wallets/{test_wallet}"
    )

    assert balance_response.status_code == 200
    assert Decimal(balance_response.json()["balance"]) == Decimal("100.00")


@pytest.mark.asyncio(loop_scope="session")
async def test_concurrent_withdrawals(client, test_wallet):
    async def withdraw():
        return await client.post(
            f"/api/v1/wallets/{test_wallet}/operation",
            json={
                "operation_type": "WITHDRAW",
                "amount": "80.00",
            },
        )

    responses = await asyncio.gather(
        withdraw(),
        withdraw(),
    )

    statuses = sorted(
        response.status_code for response in responses
    )

    assert statuses == [200, 409]

    balance_response = await client.get(
        f"/api/v1/wallets/{test_wallet}"
    )

    assert balance_response.status_code == 200
    assert Decimal(balance_response.json()["balance"]) == Decimal("20.00")


@pytest.mark.asyncio(loop_scope="session")
@pytest.mark.parametrize(
    "amount",
    ["0", "-10.00", "10.123"],
)
async def test_invalid_amount(client, test_wallet, amount):
    response = await client.post(
        f"/api/v1/wallets/{test_wallet}/operation",
        json={
            "operation_type": "DEPOSIT",
            "amount": amount,
        },
    )

    assert response.status_code == 422

    balance_response = await client.get(
        f"/api/v1/wallets/{test_wallet}"
    )

    assert balance_response.status_code == 200
    assert Decimal(balance_response.json()["balance"]) == Decimal("100.00")


@pytest.mark.asyncio(loop_scope="session")
async def test_database_rejects_negative_balance(test_wallet):
    async with SessionLocal() as session:
        result = await session.execute(
            select(Wallet.balance).where(Wallet.id == test_wallet)
        )
        original_balance = result.scalar_one()

        statement = (
            update(Wallet)
            .where(Wallet.id == test_wallet)
            .values(balance=Decimal("-1.00"))
        )

        with pytest.raises(IntegrityError):
            await session.execute(statement)

        # После нарушения ограничения транзакцию необходимо откатить.
        await session.rollback()

        result = await session.execute(
            select(Wallet.balance).where(Wallet.id == test_wallet)
        )
        actual_balance = result.scalar_one()

        assert actual_balance == original_balance
        assert actual_balance == Decimal("100.00")


@pytest.mark.asyncio(loop_scope="session")
async def test_transaction_rolls_back_on_error(test_wallet):
    async with SessionLocal() as session:
        with pytest.raises(RuntimeError, match="Simulated failure"):
            async with session.begin():
                result = await session.execute(
                    select(Wallet.balance).where(
                        Wallet.id == test_wallet
                    )
                )
                original_balance = result.scalar_one()

                result = await session.execute(
                    select(Wallet)
                    .where(Wallet.id == test_wallet)
                    .with_for_update()
                )
                wallet = result.scalar_one()

                wallet.balance += Decimal("50.00")

                # Имитируем ошибку до фиксации транзакции.
                raise RuntimeError("Simulated failure")

        # Контекст транзакции выполнил rollback.
        # Проверяем баланс в новой транзакции.
        result = await session.execute(
            select(Wallet.balance).where(Wallet.id == test_wallet)
        )
        actual_balance = result.scalar_one()

        assert actual_balance == original_balance
        assert actual_balance == Decimal("100.00")
