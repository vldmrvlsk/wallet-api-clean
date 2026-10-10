
"""add nonnegative wallet balance constraint

Revision ID: a50e1e65ec76
Revises: d34b267b34e1
"""

from typing import Sequence, Union

from alembic import op


revision: str = "a50e1e65ec76"
down_revision: Union[str, Sequence[str], None] = "d34b267b34e1"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_check_constraint(
        "ck_wallets_balance_nonnegative",
        "wallets",
        "balance >= 0",
    )


def downgrade() -> None:
    op.drop_constraint(
        "ck_wallets_balance_nonnegative",
        "wallets",
        type_="check",
    )
