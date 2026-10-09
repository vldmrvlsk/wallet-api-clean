
import asyncio
import uuid
from decimal import Decimal

import pytest


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

    # Проверяем, что неудачная операция не изменила баланс.
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
