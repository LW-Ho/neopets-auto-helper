import time
from playwright.async_api import Page, BrowserContext
import urls.neopets_urls as NEOPETS_URLS
from utility import random_sleep, web

DECEMBER = 12

async def get(context: BrowserContext, page: Page) -> bool:
    if int(time.strftime("%m")) == DECEMBER:
        await random_sleep()
        _flag = False
        _page = await context.new_page()
        try:
            await _page.goto(NEOPETS_URLS.NEO_ADVENT_CALENDAR)
            rep = await web.post(
                {}, NEOPETS_URLS.NEO_PROCESS_ADVENT, 
                context, _page, 
                NEOPETS_URLS.NEO_ADVENT_CALENDAR
            )

            await random_sleep()
            _flag = True
        except Exception as e:
            print("get_advent_calendar complete")

        await _page.close()
        return _flag