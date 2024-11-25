from playwright.async_api import Page, BrowserContext
from typing import Optional
import urls.neopets_urls as NEOPETS_URLS
from utility import random_sleep, PlayWrightInstance, web

class Bank(PlayWrightInstance):
    def __init__(self, context: BrowserContext, page: Page, pin_code: Optional[str] = None) -> None:
        super().__init__(context, page)
        self._pin_code = pin_code
    
    async def get_on_hand_npanchor(self) -> int:
        _page = await self._context.new_page()
        await _page.goto(NEOPETS_URLS.NEO_BANK)
        await random_sleep(5,10)
        try:
            tag = await _page.locator('span#npanchor').inner_text()
            value = int(tag.replace(",", ""))

            return value
        except Exception as e:
            print(f"{__name__} error {e}")    
            
        return 0

    def set_pin_code(self, pin_code="") -> bool:
        if pin_code:
            self._pin_code = pin_code
            return True

        return False

    async def collect_interest(self) -> bool:
        await random_sleep()
        try:
            await self._page.goto(NEOPETS_URLS.NEO_BANK, wait_until="load", timeout=120000)
            await random_sleep()
            post_payload = {"type": "approach"}
            rep = await web.post(post_payload, NEOPETS_URLS.NEO_BANK_INTEREST, self._context, self._page, NEOPETS_URLS.NEO_BANK)
            await random_sleep(11,15)
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
