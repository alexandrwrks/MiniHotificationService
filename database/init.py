"""Create tables once before starting application containers."""

import asyncio

from database.config import engine, init_db


async def main():
    try:
        await init_db()
    finally:
        await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
