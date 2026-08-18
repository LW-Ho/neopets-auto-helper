from playwright.async_api import Page, BrowserContext
import urls.neopets_urls as NEOPETS_URLS
from utility import random_sleep, web

async def run(context: BrowserContext, page: Page) -> bool:
    await random_sleep()
    _page = await context.new_page()
    try:
        await web.goto(_page, NEOPETS_URLS.NEO_INVENTORY_QS, ready_selector="input[name='checkall']")
        await _page.locator("input[name='checkall']").nth(1).click()
        await _page.get_by_role("button", name="Submit").click()
        await random_sleep()
        return True
    except Exception as e:
        print("quick_stock complete")
    finally:
        await _page.close()
    return False