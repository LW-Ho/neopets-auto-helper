from playwright.async_api import Page, BrowserContext
import urls.neopets_urls as NEOPETS_URLS
from utility import random_sleep, web

async def get(context: BrowserContext, page: Page) -> bool:
    await random_sleep()
    _flag = False
    _page = await context.new_page()
    try:
        await _page.goto(NEOPETS_URLS.NEO_JELLY, wait_until="load", timeout=120000)
        post_payload = {"type": "get_jelly"}
        rep = await web.post(post_payload, NEOPETS_URLS.NEO_JELLY_PROCESS, context, _page, NEOPETS_URLS.NEO_JELLY)
        await random_sleep(11,15)
        _flag = True
    except Exception as e:
        print("get_jelly complete")

    await _page.close()
    return _flag