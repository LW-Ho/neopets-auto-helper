import asyncio
from random import randrange
import re
from playwright.async_api import Playwright, async_playwright, expect
from playwright.async_api import Browser

import logging

from app.account import Account
import urls.neopets_urls as NEOPETS_URLS

_LOGGER = logging.getLogger(__name__)

USERNAME = ""
PASSWORD = ""
ACTIVE_PET_NAME = ""
OMELETTE = True
FISHING = True
SPRINGS = True
FRUIT = True

logging.getLogger().setLevel(logging.INFO)

async def run(playwright: Playwright) -> None:
    browser: Browser = await playwright.chromium.launch(headless=False, slow_mo=1000)
    context = await browser.new_context(viewport={"width":800,"height":600})
    page = await context.new_page()

    neopets: Account = Account(USERNAME, PASSWORD, ACTIVE_PET_NAME)
    print('Goto Login')
    await neopets.login(context, page)

    if OMELETTE:
        await page.goto(NEOPETS_URLS.NEO_OMELETTE)
        await page.get_by_role("button", name="Grab some Omelette").click()
        await asyncio.sleep(15)

    if FISHING:
        await page.goto(NEOPETS_URLS.NEO_FISHING)
        await page.get_by_role("button", name="Reel In Your Line").click()
        await asyncio.sleep(15)

    if SPRINGS:
        await page.goto(NEOPETS_URLS.NEO_SPRINGS)
        await page.get_by_role("button", name="Heal my Pets").click()
        await asyncio.sleep(15)

    if FRUIT:
        try:
            await page.goto(NEOPETS_URLS.NEO_FRUIT)
            await page.get_by_role('button', name='Spin, spin, spin!').click()
            await asyncio.sleep(15)
        except Exception as e:
            print(f"FRUIT Complete.")

    await context.close()
    await browser.close()

async def main() -> None:
    async with async_playwright() as playwright:
        await run(playwright)

    mins = randrange(200,1200)

    print('Work done, sleeping time '+str(mins)+' ... ')
    await asyncio.sleep(mins)

if __name__ == "__main__":
    while True:
        asyncio.run(main())