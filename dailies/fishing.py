from playwright.async_api import Page, BrowserContext
import urls.neopets_urls as NEOPETS_URLS
from utility import random_sleep

async def get(context: BrowserContext, page: Page) -> bool:
    await random_sleep()
    _flag = False
    _page = await context.new_page()
    try:
        await _page.goto(NEOPETS_URLS.NEO_FISHING)
        await _page.get_by_role("button", name="Reel In Your Line").click()
        await random_sleep()
        _flag = True
    except Exception as e:
        print("get_fishing complete")

    await _page.close()
    return _flag