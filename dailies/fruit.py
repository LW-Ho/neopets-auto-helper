import re
from playwright.async_api import Page, BrowserContext
import urls.neopets_urls as NEOPETS_URLS
from utility import random_sleep, web

async def get(context: BrowserContext, page: Page) -> bool:
    flag = False
    await random_sleep()
    _page = await context.new_page()
    try:
        await _page.goto(NEOPETS_URLS.NEO_FRUIT, wait_until="load", timeout=120000)
        _content = await _page.content()
        if "Please come back tomorrow and try again" not in _content:
            ck_match = re.search(r"function getCK\(\) \{\s*return '([^']+)';\s*\}", _content)
            ck_value = ck_match.group(1) if ck_match else None
            post_payload = {"spin": "1", "ck": ck_value}
            rep = await web.post(post_payload, NEOPETS_URLS.NEO_FRUIT_PROCESS, context, _page, NEOPETS_URLS.NEO_FRUIT)
        
        await random_sleep()
        flag = True
    except Exception as e:
        print("get_friut complete")

    await _page.close()
    return flag