import asyncio
from random import randrange
async def random_sleep(min=5, max=10):
    await asyncio.sleep(randrange(min, max))