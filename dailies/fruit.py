from playwright.async_api import Page, BrowserContext
import urls.neopets_urls as NEOPETS_URLS
from utility import random_sleep

async def get(context: BrowserContext, page: Page) -> bool:
    flag = False
    await random_sleep()
    _page = await context.new_page()
    try:
        await _page.goto(NEOPETS_URLS.NEO_FRUIT)
        _content = await _page.content()
        if "Please come back tomorrow and try again" not in _content:
            await _page.get_by_role("button", name="Spin, spin, spin!").click()
        
        await random_sleep()
        flag = True
    except Exception as e:
        print("get_friut complete")

    await _page.close()
    return flag