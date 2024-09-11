import traceback
from playwright.async_api import Page, BrowserContext
import urls.neopets_urls as NEOPETS_URLS
from utility import random_sleep, PlayWrightInstance
from typing import Tuple
from utility import web, bank as Bank


class Stock(PlayWrightInstance):
    def __init__(self, context: BrowserContext, page: Page, pin_code: str = "", sell_target_value=60) -> None:
        super().__init__(context, page)
        self._pin_code = pin_code
        self._sell_target_value = sell_target_value
        self._portfolio = []

    async def _get_cheapest_stock(self) -> Tuple[str, int]:
        ticker = ""
        min_price = 15
        lowest_price = 20

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
    
    async def sell_stock(self) -> Tuple[bool, dict]:
        try:
            await self._page.goto(NEOPETS_URLS.NEO_STOCK_PORTFOILO, timeout=120000)
            await random_sleep()

            ref_value = ''

            ref_element = await self._page.query_selector('input[name="_ref_ck"]')
            if ref_element:
                ref_value = await ref_element.get_attribute('value')

            tables = await self._page.query_selector_all('table[align="center"][cellpadding="3"] table')
            result = []
            for table in tables:
                rows = await table.query_selector_all('tr')
                for row in rows:
                    raw_text = await row.text_content()
                    headers = ["Shares", "Paid NP", "Total NP", "Current", "Mkt Value", "% Change"]
                    temp = {}
                    if raw_text:
                        lines = [line.strip() for line in raw_text.splitlines() if line.strip()]
                        lines = [line.replace(",", "") for line in lines]
                        temp = dict(zip(headers, lines))
                    
                    sellname_element = await row.query_selector('input[name*="sell"]')
                    if sellname_element:
                        value = await sellname_element.get_attribute('name')
                        temp["sell"] = value

                    result.append(temp)

            sell_list = []

            for index in result:
                try:
                    if int(index['Current']):
                        _current = int(index['Current'])
                        if _current > 1000:
                            _current = _current/1000

                        if _current >= self._sell_target_value:
                            sell_list.append({"Shares": int(index['Shares']), "Sell": index['sell']})

                except:
                    pass
   
            payload = {"_ref_ck": ref_value, "type": "sell"}

            if self._pin_code:
                payload['pin'] = self._pin_code

            for index in sell_list:
                payload[index['Sell']] = index['Shares']

            response = await web.post(
                payload, 
                NEOPETS_URLS.NEO_STOCK_BUY_PROCESS, 
                self._context, 
                self._page,
                referer=NEOPETS_URLS.NEO_STOCK_PORTFOILO)
            
            if "Summary" in response:
                return True, payload

        except Exception as e:
            print(f"{__name__} error {e}")

        return False, {}