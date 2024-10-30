from playwright.async_api import Page, BrowserContext
import urls.neopets_urls as NEOPETS_URLS
from utility import random_sleep

async def get(context: BrowserContext, page: Page) -> bool:
    await random_sleep()
    _flag = False
    _page = await context.new_page()
    try:
        await _page.goto(NEOPETS_URLS.NEO_TDMBGPOP)
        await _page.get_by_role("button", name="Talk to the Plushie").click()
        await random_sleep()
        _flag = True
    except Exception as e:
        print("get_tdmbgpop complete")

    await _page.close()
    return _flag