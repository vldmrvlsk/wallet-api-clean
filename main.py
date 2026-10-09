
from decimal import Decimal
from enum import Enum
from uuid import UUID

from fastapi import Depends, FastAPI, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_session
from app.models import Wallet


app = FastAPI(title="Wallet API")


class OperationType(str, Enum):
    DEPOSIT = "DEPOSIT"
    WITHDRAW = "WITHDRAW"


class WalletOperation(BaseModel):
    operation_type: OperationType
    amount: Decimal = Field(
        gt=0,
        max_digits=12,
        decimal_places=2,
    )


@app.get("/")
async def root():
    return {"message": "Wallet API is running"}


@app.get("/api/v1/wallets/{wallet_uuid}")
async def get_wallet_balance(
    wallet_uuid: UUID,
    session: AsyncSession = Depends(get_session),
):
    result = await session.execute(
        select(Wallet).where(Wallet.id == wallet_uuid)
    )
    wallet = result.scalar_one_or_none()

    if wallet is None:
        raise HTTPException(
            status_code=404,
            detail="Wallet not found",
        )

    return {
        "wallet_uuid": str(wallet.id),
        "balance": str(wallet.balance),
    }


@app.post("/api/v1/wallets/{wallet_uuid}/operation")
async def wallet_operation(
    wallet_uuid: UUID,
    operation: WalletOperation,
    session: AsyncSession = Depends(get_session),
):
    async with session.begin():
        result = await session.execute(
            select(Wallet)
            .where(Wallet.id == wallet_uuid)
            .with_for_update()
        )
        wallet = result.scalar_one_or_none()

        if wallet is None:
            raise HTTPException(
                status_code=404,
                detail="Wallet not found",
            )

        if (
            operation.operation_type == OperationType.WITHDRAW
            and wallet.balance < operation.amount
        ):
            raise HTTPException(
                status_code=409,
                detail="Insufficient funds",
            )

        if operation.operation_type == OperationType.DEPOSIT:
            wallet.balance += operation.amount
        else:
            wallet.balance -= operation.amount

        new_balance = wallet.balance

    return {
        "wallet_uuid": str(wallet_uuid),
        "operation_type": operation.operation_type.value,
        "amount": str(operation.amount),
        "balance": str(new_balance),
    }
