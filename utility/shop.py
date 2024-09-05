import re
from typing import Optional
from playwright.async_api import Page, BrowserContext
import urls.neopets_urls as NEOPETS_URLS
from utility import random_sleep, PlayWrightInstance, web

class Shop(PlayWrightInstance):
    def __init__(self, context: BrowserContext, page: Page):
        super().__init__(context, page)
        self.url = ""
        self.owner = ""
        self.items: ShopItem = Optional[ShopItem|None]

    async def scrape_shop_items(self) -> "ShopItem":
        self.url = self._page.url

        # First td element
        td_element = self._page.locator('td[width="120"][align="center"][valign="top"]').nth(0)

        td_html = await td_element.inner_html()
        
        href_match = re.search(r'href="([^"]+)"', td_html)
        href = href_match.group(1) if href_match else None
        href = href.replace('amp;', '')

        owner_match = re.search(r'owner=([^&]+)', href) if href else None
        owner = owner_match.group(1) if owner_match else None

        obj_id_match = re.search(r'obj_info_id=([^&]+)', href) if href else None
        obj_id = obj_id_match.group(1) if obj_id_match else None

        img_src_match = re.search(r'<img src="([^"]+)"', td_html)
        item_name_match = re.search(r'<b>([^<]+)</b>', td_html)
        stock_match = re.search(r'(\d+) in stock', td_html)
        price_match = re.search(r'Cost : (\d+) NP', td_html)

        # 生成字典
        item_details = {
            "image_url": img_src_match.group(1) if img_src_match else None,
            "item_name": item_name_match.group(1) if item_name_match else None,
            "obj_id": obj_id,
            "stock": int(stock_match.group(1)) if stock_match else None,
            "price": int(price_match.group(1)) if price_match else None,
            "owner": owner,
            "buy_link": href
        }

        self.owner = owner

        shop_items = ShopItem(
            item_details["item_name"], 
            item_details['price'], 
            item_details['stock'],
            item_details['obj_id'],
            item_details["buy_link"]
            )

        self.items = shop_items

    def print_items(self):
        if self.items:
            print(f"name: {self.items.name}, quantity: {self.items.quantity}, price: {self.items.price}")
        else:
            print(f"name: not found")

class ShopItem():
    def __init__(self, name, price, quantity, obj_id, buy_link):
        self.name = name
        self.price = price
        self.quantity = quantity
        self.obj_id = obj_id
        self.buy_link = buy_link

    def __str__(self):
        return self.name
