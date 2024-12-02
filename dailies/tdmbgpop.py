from playwright.async_api import Page, BrowserContext
import urls.neopets_urls as NEOPETS_URLS
from utility import random_sleep, web

async def get(context: BrowserContext, page: Page) -> bool:
    await random_sleep()
    _flag = False
    _page = await context.new_page()
    try:
        await _page.goto(NEOPETS_URLS.NEO_TDMBGPOP, wait_until="load", timeout=120000)
        await random_sleep()
        post_payload = {"talkto": "1"}
        rep = await web.post(post_payload, NEOPETS_URLS.NEO_TDMBGPOP_PROCESS, context, _page, NEOPETS_URLS.NEO_TDMBGPOP)
        await random_sleep(11,15)
        _flag = True
    except Exception as e:
        print("get_tdmbgpop complete")

    await _page.close()
    return _flag