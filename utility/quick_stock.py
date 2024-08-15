import asyncio
from playwright.async_api import Page, BrowserContext
import urls.neopets_urls as NEOPETS_URLS
from utility import random_sleep

async def run(context: BrowserContext, page: Page) -> bool:
    await random_sleep()
    try:
        _page = await context.new_page()
        await _page.goto(NEOPETS_URLS.NEO_INVENTORY_QS)
        await _page.locator("input[name='checkall']").nth(1).click()
        await _page.get_by_role("button", name="Submit").click()
        await random_sleep()
        return True
    except Exception as e:
        print("quick_stock complete")

    return False