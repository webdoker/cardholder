import asyncio

from db import create_all
import models  # noqa: F401 — register models with metadata


async def init_models():
    await create_all()


if __name__ == "__main__":
    asyncio.run(init_models())
