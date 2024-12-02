import re
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

            content = await _page.content()

            if "Collect My Prize!!!" in content:
                ck_match = re.search(r"function getCK\(\) \{\s*return '([^']+)';\s*\}", content)
                ck_value = ck_match.group(1) if ck_match else None

                rep = await web.post_form_data(
                    {"_ref_ck": ck_value}, NEOPETS_URLS.NEO_PROCESS_ADVENT_CALENDAR, context, _page, NEOPETS_URLS.NEO_ADVENT_CALENDAR
                )

            await random_sleep()
            _flag = True
        except Exception as e:
            print("get_advent_calendar complete")

        await _page.close()
        return _flag