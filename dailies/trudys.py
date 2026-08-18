from random import randrange
from playwright.async_api import Page, BrowserContext
import urls.neopets_urls as NEOPETS_URLS
from utility import random_sleep, web

async def get(context: BrowserContext, page: Page) -> bool:
    await random_sleep()
    _flag = False
    _page = await context.new_page()
    try:
        await web.goto(_page, NEOPETS_URLS.NEO_TRUDYS)
        await random_sleep(5,10)
        await web.get(NEOPETS_URLS.NEO_TRUDYS, context, _page, "")
        await random_sleep(5,10)
        post_payload = {"action": "beginroll"}
        rep = await web.post(post_payload, NEOPETS_URLS.NEO_TRUDYS_SPIN, context, _page, NEOPETS_URLS.NEO_TRUDYS)
        await random_sleep(11,15)
        post_payload = {"action": "prizeclaimed"}
        rep = await web.post(post_payload, NEOPETS_URLS.NEO_TRUDYS_SPIN, context, _page, NEOPETS_URLS.NEO_TRUDYS)
        await random_sleep(5,10)
        _flag = True
    except Exception as e:
        print(f"get_trudys complete {e}")

    await _page.close()
    return _flag