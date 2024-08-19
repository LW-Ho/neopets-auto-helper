from playwright.async_api import Page, BrowserContext
from typing import Optional
import urls.neopets_urls as NEOPETS_URLS
from utility import random_sleep

class Bank():
    def __init__(self, context: BrowserContext, page: Page, pin_code: Optional[str] = None) -> None:
        self._context = context
        self._page = page
        self._pin_code = pin_code
    
    def set_pin_code(self, pin_code="") -> bool:
        if pin_code:
            self._pin_code = pin_code
            return True

        return False

    async def collect_interest(self) -> bool:
        await random_sleep()
        try:
            await self._page.goto(NEOPETS_URLS.NEO_BANK)
            await random_sleep()
            await self._page.get_by_role("button", name="Collect Interest").click()
            await random_sleep()
            return True

        except Exception as e:
            print("bank.collect_interest complete")

        return False

    async def withdraw(self, price: int = 1) -> bool:
        await random_sleep()
        try:
            await self._page.goto(NEOPETS_URLS.NEO_BANK)
            await random_sleep()
            if self._pin_code:
                await self._page.locator("#pin_field").click()
                await self._page.locator("#pin_field").fill(self._pin_code)
                await random_sleep()
            await self._page.locator("#frmWithdraw input[name=\"amount\"]").click()
            await self._page.locator("#frmWithdraw input[name=\"amount\"]").fill(str(price))
            await random_sleep()
            self._page.on("dialog", lambda dialog: dialog.accept())
            await self._page.get_by_role("button", name="Withdraw").click()
            await random_sleep()
            return True
        except Exception as e:
            print("bank.withdraw complete")

        return False

    async def deposit(self, price: int = 1) -> bool:
        await random_sleep()
        try:
            await self._page.goto(NEOPETS_URLS.NEO_BANK)
            await random_sleep()
            await self._page.locator("#frmDeposit").get_by_role("textbox").click()
            await self._page.locator("#frmDeposit").get_by_role("textbox").fill(str(price))
            await random_sleep()
            self._page.on("dialog", lambda dialog: dialog.accept())
            await self._page.get_by_role("button", name="Deposit").click()
            await random_sleep()
            return True
        except Exception as e:
            print("bank.deposit complete")

        return False
