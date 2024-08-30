import asyncio
from playwright.async_api import Page, BrowserContext
from random import randrange

class PlayWrightInstance():
    def __init__(self, context: BrowserContext, page: Page) -> None:
        self._context = context
        self._page = page

async def random_sleep(min=5, max=10):
    await asyncio.sleep(randrange(min, max))