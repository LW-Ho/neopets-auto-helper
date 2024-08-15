from random import randrange
from playwright.async_api import Page, BrowserContext
import urls.neopets_urls as NEOPETS_URLS
from utility import random_sleep

async def get(context: BrowserContext, page: Page) -> bool:
    await random_sleep()
    try:
        _page = await context.new_page()
        await _page.goto(NEOPETS_URLS.NEO_TRUDYS, wait_until="load", timeout=120000)
        await random_sleep(5,10)
        x = randrange(326, 447)
        y = randrange(470, 509)
        await _page.frame_locator("iframe[name=\"frameTest\"]").locator("canvas").click(position={"x":x,"y":y})
        await random_sleep(15,30)
        return True
    except Exception as e:
        print(f"get_trudys complete {e}")

    return False