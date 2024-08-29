from playwright.async_api import Page, BrowserContext
import urls.neopets_urls as NEOPETS_URLS
from utility import random_sleep
from typing import Tuple
from utility import web, bank as Bank


class Stock():
    def __init__(self, context: BrowserContext, page: Page, pin_code: str = "") -> None:
        self._context = context
        self._page = page
        self._pin_code = pin_code


    async def _get_cheapest_stock(self) -> Tuple[str, int]:
        ticker = ""
        min_price = 15
        lowest_price = 20

        # content = await web.get(NEOPETS_URLS.STOCK_MARKET_LIST, self._context, self._page)
        await self._page.goto(NEOPETS_URLS.STOCK_MARKET_LIST)
        stock_params = await self._page.locator('td[align="center"][bgcolor="#eeeeff"]').all()
        for index in range(0, len(stock_params), 5):
            _stock_price = await stock_params[index+3].inner_text()
            _sotck_ticker = await stock_params[index].inner_text()
            if int(_stock_price) < lowest_price and \
                int(_stock_price) > min_price:
                lowest_price = int(_stock_price)
                ticker = _sotck_ticker
                break

        return ticker, lowest_price

    async def buy_stock(self) -> bool:
        try:
            shares = 1000
            ticker, price = await self._get_cheapest_stock()

            # check on hand np
            bank = Bank.Bank(self._context, self._page, pin_code=self._pin_code)
            npanchor = await bank.get_on_hand_npanchor()

            print(f"On hand {npanchor}")

            if ticker:
                
                await self._page.goto(NEOPETS_URLS.NEO_STOCK_BUY+ticker)
                await random_sleep()

                if npanchor < shares * price:
                    bank.withdraw((shares * price) - npanchor)

                ref = await self._page.locator('input[name="_ref_ck"]').get_attribute("value")
                payload = {"_ref_ck": ref, "type": "buy", "ticker_symbol": ticker, "amount_shares": shares}
                rep = await web.post(payload, NEOPETS_URLS.NEO_STOCK_BUY_PROCESS, self._context, self._page, NEOPETS_URLS.NEO_STOCK_BUY+ticker)

                return True

        except Exception as e:
            print(f"{__name__} error {e}")

        return False