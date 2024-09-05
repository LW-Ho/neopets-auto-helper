import traceback
from playwright.async_api import Page, BrowserContext, Locator
import urls.neopets_urls as NEOPETS_URLS
from utility import random_sleep, PlayWrightInstance, web
from utility.shop import Shop

class ShopWizard(PlayWrightInstance):
    def __init__(self, context: BrowserContext, page: Page) -> None:
        super().__init__(context, page)
        self.searches = 0
        self._search_ban_status = False
        self._search_ban_time = None
        self.__shopwizard_ban = False

    def __check_shopwizard_ban(self, source):
        if "too many searches!" in source:
            self.__shopwizard_ban = True

    async def __search(self, item, max_searches, criteria="exact", min_price = 0, max_price = 999999):
        new_search = ItemSearch(item)
        for i in range(max_searches):
            self.searches += 1
            referer = "https://www.neopets.com/market.phtml?type=wizard"
            payload = {"type": "process_wizard",
                        "feedset": 0,
                        "shopwizard": item,
                        "table": "shop",
                        "criteria": criteria,
                        "min_price": min_price,
                        "max_price": max_price}

            search_results_page_source = await web.post(payload, NEOPETS_URLS.NEO_SHOP_WIZARD, self._context, self._page, referer=referer)
            self.__check_shopwizard_ban(search_results_page_source)
            await self._page.set_content(search_results_page_source)
            await random_sleep(1,3)
            if self.__shopwizard_ban == False:
                new_search.add_shops(await self.__parse_search())

        return new_search

    async def __parse_search(self) -> list["SearchResult"]:
        search_results: list[SearchResult] = []
        table_index = 2

        try:
            table_of_shops: Locator = self._page.locator("table").nth(table_index)
            prices_F6 = await table_of_shops.locator('td[align="right"][bgcolor="#F6F6F6"]').all_inner_texts()
            quantities_F6 = await table_of_shops.locator('td[align="center"][bgcolor="#F6F6F6"]').all_inner_texts()
            prices_FF = await table_of_shops.locator('td[align="right"][bgcolor="#FFFFFF"]').all_inner_texts()
            quantities_FF = await table_of_shops.locator('td[align="center"][bgcolor="#FFFFFF"]').all_inner_texts()
            shop_owners = await table_of_shops.locator('a[href^="/browseshop.phtml?"]').all_inner_texts()
            shop_links = await table_of_shops.locator('a[href^="/browseshop.phtml?"]').evaluate_all("elements => elements.map(el => el.getAttribute('href'))")

            min_length = min(len(prices_F6), len(prices_FF))
            price = []

            for i in range(min_length):
                price.append(prices_F6[i].replace(' NP', ''))
                price.append(prices_FF[i].replace(' NP', ''))

            if len(prices_F6) > len(prices_FF):
                price.extend([item.replace(' NP', '') for item in prices_F6[min_length:]])

            if len(prices_FF) > len(prices_F6):
                price.extend([item.replace(' NP', '') for item in prices_FF[min_length:]])

            min_length = min(len(quantities_F6), len(quantities_FF))
            quantities = []

            for i in range(min_length):
                quantities.append(quantities_F6[i])
                quantities.append(quantities_FF[i])

            if len(quantities_F6) > len(quantities_FF):
                quantities.extend(quantities_F6[min_length:])

            if len(quantities_FF) > len(quantities_F6):
                quantities.extend(quantities_FF[min_length:])

            if shop_owners:
                for index in range(len(shop_owners)):
                    search_results.append(
                        SearchResult(
                            shop_owners[index],
                            int(quantities[index]),
                            int(price[index]),
                            shop_links[index]
                        )
                    )
        
        except Exception as e:
            print(f"{__name__} error: {e}, {traceback.format_exc()}")

        return search_results
    
    async def __open_shop(self, Item_Search: "ItemSearch"):
        if Item_Search.cheapest_result() is not None:

            await self._page.goto(NEOPETS_URLS.NEO_SHOP_REFFER_HOME_PAGE + Item_Search.cheapest_result().shop_link, timeout=120000)
            await random_sleep()

            content = await self._page.content()
            while "Sorry - The owner of this shop has been frozen!" in content:
                Item_Search.remove_shop()
                await self._page.goto(NEOPETS_URLS.NEO_SHOP_REFFER_HOME_PAGE + Item_Search.cheapest_result().shop_link, timeout=120000)
                await random_sleep()

            await Item_Search.cheapest_result().add_shop_details(self._context, self._page)

    async def __send_purchase_request(self, Item_Search: "ItemSearch"):
        referer = Item_Search.cheapest_result().shop.url
        buy_link = NEOPETS_URLS.NEO_HOMEPAGE + Item_Search.cheapest_result().shop.items.buy_link
        response = await web.get(buy_link, self._context, self._page, referer=referer)

        Item_Search.decrease_shop_quantity()

    async def buy(self, item: str, quantity = 1, max_searches = 10, max_price=99999) -> list:
        prices_paid = []

        self._page = await self._context.new_page()

        Item_Search = await self.__search(item, max_searches, max_price=max_price)

        if Item_Search.cheapest_result() != None and self.__shopwizard_ban != True:
            for i in range(quantity):
                try:
                    await self.__open_shop(Item_Search)
                    price = Item_Search.cheapest_result().shop.items.price
                    await self.__send_purchase_request(Item_Search)
                    prices_paid.append(price)
                except Exception as e:
                    print(f"{__name__} error {e} {traceback.format_exc()}")
                    prices_paid.append(0)

        return prices_paid
    
class ItemSearch:
    def __init__(self, search_item):
        self.search_item = search_item
        self.search_results: list["SearchResult"] = [] #List of search result objects (shop owners) selling the search_item
        self.search_groups = [0,0,0,0,0,0,0,0,0,0,0,0,0]
        self.users_group_index = 5 #Need this update dynamically

    def __sort(self):
        self.search_results.sort(key=lambda x: x.price, reverse=False)
        return 0

    def average_price(self):
        average = 0
        count = 0
        for i in range(len(self.search_groups)):
            count+= self.search_groups[i]
        for n in range(count):
            average += self.search_results[n].price

        return average/count

    def search_completed(self):
        count = 0
        for i in range(len(self.search_groups)):
            count+= self.search_groups[i]
        return count

    def cheapest_result_in_group(self):
        if self.search_groups[self.users_group_index] == 0:
            return None
        else:
            for shop in self.search_results:
                if self.get_shop_group(shop.owner) == self.users_group_index:
                    return shop

    def get_object_id(self):
        if len(self.search_results) > 0:
            return self.cheapest_result().obj_id
        else:
            return -1

    def cheapest_result(self) -> "SearchResult":
        try:
            if len(self.search_results) != 0:
                return self.search_results[0]
            
        except Exception as e:
            print(f"{__name__} error : {e}")

        return SearchResult("", 0, 0, "")

    def remove_shop(self, index = 0):
        if len(self.search_results) > 0:
            self.search_results.pop(index)

    def add_shops(self, shops):
        #Check shop group has been added already
        if len(shops) > 0:
            _group = self.get_shop_group(shops[0].owner)

            if self.search_groups[_group] == 0:
                self.search_results.extend(shops)
                self.search_groups[_group] = 1
                self.__sort()
                return True

        return False

    def decrease_shop_quantity(self):
        self.search_results[0].stock-= 1

        if self.search_results[0].stock <= 0:
            self.search_results.pop(0)

    def get_shop_group(self, owner):
        _group = ord(owner[0])

        if _group == 95:
            _group = 10
        elif _group < 58:
            _group = _group % 48
        else:
            _group = (_group % 97) % 13
        return _group

    def __str__(self):
        s = str(self.search_groups)
        for shop in self.search_results:
            s = s + "\n" + str(shop)

        return s
    
class SearchResult:
    def __init__(self, owner: str, stock: int, price: int, shop_link: str):
        self.owner = owner
        self.stock = stock
        self.price = price
        self.shop_link = shop_link
        self.obj_id = int(self.shop_link[self.shop_link.find("&buy_obj_info_id=") + len("&buy_obj_info_id=") : self.shop_link.find("&buy_cost_neopoints=")])
        self.shop: Shop = None

    async def add_shop_details(self, context: BrowserContext, page: Page):
        self.shop = Shop(context, page)
        await self.shop.scrape_shop_items()

    def __str__(self):
        return self.owner + " " + str(self.stock) + " " + str(self.price)


