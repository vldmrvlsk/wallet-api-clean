
import uuid
from decimal import Decimal
from sqlalchemy import Numeric
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class Wallet(Base):
    __tablename__ = "wallets"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    balance: Mapped[Decimal] = mapped_column(
            Numeric(12, 2),
            nullable=False,
            default=Decimal("0.00"),
    
    )

