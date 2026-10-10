
import asyncio
import os
import sys
from pathlib import Path

import asyncpg
import pytest
from alembic import command
from alembic.config import Config


PROJECT_ROOT = Path(__file__).resolve().parent.parent
os.chdir(PROJECT_ROOT)

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise RuntimeError(
        "DATABASE_URL environment variable is not set"
    )

TEST_DATABASE_NAME = "wallet_test_db"


def get_test_database_url(database_url: str) -> str:
    prefix, separator, database_name = database_url.rpartition("/")

    if not separator or not database_name:
        raise ValueError("Invalid DATABASE_URL")

    if "?" in database_name or "#" in database_name:
        raise ValueError(
            "DATABASE_URL query parameters are not supported "
            "by this test runner"
        )

    return f"{prefix}/{TEST_DATABASE_NAME}"


async def ensure_test_database() -> None:
    database_url = DATABASE_URL.replace(
        "postgresql+asyncpg://",
        "postgresql://",
        1,
    )
    test_database_url = get_test_database_url(database_url)

    connection = await asyncpg.connect(
        database_url.rsplit("/", 1)[0] + "/postgres"
    )

    try:
        exists = await connection.fetchval(
            "SELECT 1 FROM pg_database WHERE datname = $1",
            TEST_DATABASE_NAME,
        )

        if not exists:
            await connection.execute(
                f'CREATE DATABASE "{TEST_DATABASE_NAME}"'
            )
            print(f"Created database: {TEST_DATABASE_NAME}")
        else:
            print(f"Database already exists: {TEST_DATABASE_NAME}")
    finally:
        await connection.close()


def apply_test_migrations() -> None:
    test_database_url = get_test_database_url(DATABASE_URL)

    os.environ["DATABASE_URL"] = test_database_url

    config = Config(str(PROJECT_ROOT / "alembic.ini"))
    command.upgrade(config, "head")


def main() -> int:
    asyncio.run(ensure_test_database())
    apply_test_migrations()

    print("\nRunning tests...\n")
    return pytest.main(["-v", str(PROJECT_ROOT / "tests")])


if __name__ == "__main__":
    sys.exit(main())
