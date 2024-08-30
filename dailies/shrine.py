from playwright.async_api import Page, BrowserContext
import urls.neopets_urls as NEOPETS_URLS
from utility import random_sleep

async def get(context: BrowserContext, page: Page) -> bool:
    await random_sleep()
    try:
        _page = await context.new_page()
        await _page.goto(NEOPETS_URLS.NEO_SHRINE)
        await _page.get_by_role("button", name="Approach the Shrine").click()
        await random_sleep()
        await _page.close()
        return True
    except Exception as e:
        print("get_shrine complete")

    return False