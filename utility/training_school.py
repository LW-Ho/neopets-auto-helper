import re
import traceback
from typing import Union
from playwright.async_api import Page, BrowserContext
import urls.neopets_urls as NEOPETS_URLS
from utility import random_sleep, PlayWrightInstance, web, shop_wizard

# mapping = {
#     "Lvl": {"key": "level", "course_name": "Level"},
#     "Str": {"key": "strength", "course_name": "Strength"},
#     "Def": {"key": "defense", "course_name": "Defence"},
#     "Mov": {"key": "movement", "course_name": "Agility"},
#     "Hp": {"key": "hp", "course_name": "Endurance"}
# }


class TrainingSchool(PlayWrightInstance):
    def __init__(self, 
                 context: BrowserContext, 
                 page: Page, 
                 pet_name: str, 
                 course_name: str,
                 target_value: int) -> None:
        super().__init__(context, page)
        self._pet_name = pet_name
        self._course_name = course_name
        self._target_value = target_value
        self._now_value: int = 0
        self._pets: list = []
        self._active_pet:dict = {}
        self._buy_infos:list = []

    @property
    def pet_name(self) -> str:
        return self._pet_name
    
    @property
    def course_name(self) -> str:
        return self._course_name
    
    @property
    def target_value(self) -> int:
        return self._target_value

    @property
    def now_value(self) -> int:
        return self._now_value

    @now_value.setter
    def now_value(self, value: int) -> None:
        self._now_value = value

class SecretNinja(TrainingSchool):
    def __init__(self, 
                 context: BrowserContext, 
                 page: Page, 
                 pet_name: str, 
                 course_name: str, 
                 target_value: int) -> None:
        super().__init__(context, page, pet_name, course_name, target_value)
        self._level_limit = 2500

    async def complete(self) -> bool:
        try:
            payload = {"type" : "complete", "pet_name": self._pet_name}
            rep = await web.post(
                    payload, 
                    NEOPETS_URLS.NEO_SECRET_NINJA_TRAINING_SCHOOL_COMPLETE, 
                    self._context, self._page, 
                    NEOPETS_URLS.NEO_SECRET_NINJA_TRAINING_SCHOOL_STATUS
                    )
            
            return True
        
        except Exception as e:
            print(f"{__name__} error {e} Traceback: {traceback.format_exc()}")    


        return False

    async def study(self) -> bool:
        try:
            payload = {"type" : "start", "course_type": self._course_name, "pet_name": self._pet_name}
            await web.post(payload,
                           NEOPETS_URLS.NEO_SECRET_NINJA_TRAINING_SCHOOL_START,
                           self._context, self._page,
                           NEOPETS_URLS.NEO_SECRET_NINJA_TRAINING_SCHOOL_COURSES)
            

        except Exception as e:
            print(f"{__name__} error {e} Traceback: {traceback.format_exc()}")    

        return False

    async def buy(self) -> bool:
        try:
            await self._page.goto(NEOPETS_URLS.NEO_SECRET_NINJA_TRAINING_SCHOOL_STATUS, timeout=120000)
            await self.collect()

            shopWizard = shop_wizard.ShopWizard(self._context, self._page)
            for item in self._active_pet["pay_items"]:
                try:
                    result = await shopWizard.buy(item, quantity=1, max_searches=5, max_price=20000)
                    self._buy_infos.append({result["item_name"]: result["price"]})
                except Exception as e:
                    print(f"{__name__} error : {e} Traceback: {traceback.format_exc()}")

            return True
        except Exception as e:
            print(f"{__name__} error : {e} Traceback: {traceback.format_exc()}")

        return False
    
    async def pay(self) -> bool:
        try:
            await web.get(NEOPETS_URLS.NEO_SECRET_NINJA_TRAINING_SCHOOL_PAY_STONE+self._pet_name,
                          self._context, self._page)
            
            return True
        except Exception as e:
            print(f"{__name__} error {e} Traceback: {traceback.format_exc()}")
            
        return False

    async def collect(self) -> list[str]:
        try:
            await self._page.goto(NEOPETS_URLS.NEO_SECRET_NINJA_TRAINING_SCHOOL_STATUS, timeout=120000)
            await random_sleep()

            rows = await self._page.query_selector_all('table[width="500"] tr')

            current_pet = None
            for row in rows:
                # Get pet information
                pet_info_element = await row.query_selector('td[colspan="2"]')
                if pet_info_element:
                    pet_info_text = await pet_info_element.inner_text()
                    pet_name = pet_info_text.split(" (Level ")[0]
                    level = int(pet_info_text.split(" (Level ")[1].split(")")[0])
                    is_on_course = "is currently studying" in pet_info_text
                    current_pet = {
                        "name": pet_name,
                        "level": level,
                        "is_on_course": is_on_course,
                        "pay_items": [],
                        "attributes": {}
                    }

                # Get attributes
                attribute_element = await row.query_selector('td[align="center"][width="250"]')
                if attribute_element and current_pet:
                    attributes = {}
                    stats_text = await attribute_element.text_content()
                    stats_lines = stats_text.split("\n")

                    pattern = re.compile(r"Lvl\s*:\s*(\d+)\s*Str\s*:\s*(\d+)\s*Def\s*:\s*(\d+)\s*Mov\s*:\s*(\d+)\s*Hp\s*:\s*(\d+) / (\d+)")
                    for index in stats_lines:
                        if index:
                            match = pattern.search(index)
                            if match:
                                attributes["Level"] = int(match.group(1))
                                attributes["Strength"] = int(match.group(2))
                                attributes["Defence"] = int(match.group(3))
                                attributes["Agility"] = int(match.group(4))
                                attributes["Endurance"] = int(match.group(6))

                                if self._course_name == "Level":
                                    self.now_value = attributes["Level"]
                                if self._course_name == "Strength":
                                    self.now_value = attributes["Strength"]
                                if self._course_name == "Defence":
                                    self.now_value = attributes["Defence"]
                                if self._course_name == "Agility":
                                    self.now_value = attributes["Agility"]
                                if self._course_name == "Endurance":
                                    self.now_value = attributes["Endurance"]
                                
                        current_pet["attributes"] = attributes

                pay_item_element = await row.query_selector('td[align="center"][width="250"]:not([bgcolor])')
                if pay_item_element and current_pet:
                    text = await pay_item_element.inner_text()
                    text = text.split("\n")

                    for index in text:
                        if index and "Codestone" in index:
                            current_pet["pay_items"].append(index.replace("\t", ""))
                            
                if current_pet["name"] == self._pet_name:
                    self._active_pet = current_pet

                self._pets.append(current_pet)
                           
        except Exception as e:
            print(f"{__name__} error {e} Traceback: {traceback.format_exc()}")

    async def start(self) -> Union[bool, dict, list]:
        try:
            await self.complete()
            await self.collect()

            for pet in self._pets:
                result = True
                if pet["name"] == self._pet_name:
                    if self._course_name == "Endurance":
                        result = pet["attributes"][self._course_name] < self._level_limit*2
                    else:
                        result = pet["attributes"][self._course_name] < self._level_limit

                    if result == False:
                        return False, {"pet_name": False}, []
                    
                    break

            await self.study()
            await self.buy()
            result = await self.pay()

            return result, self._active_pet, self._buy_infos

        except Exception as e:
            print(f"{__name__} error {e} Traceback: {traceback.format_exc()}")

        return False, self._active_pet, self._buy_infos

class MysteryIsland(TrainingSchool):
    def __init__(self, 
                 context: BrowserContext, 
                 page: Page, 
                 pet_name: str, 
                 course_name: str, 
                 target_value: int) -> None:
        super().__init__(context, page, pet_name, course_name, target_value)
        self._level_limit = 250

    async def complete(self) -> bool:
        try:
            payload = {"type" : "complete", "pet_name": self._pet_name}
            rep = await web.post(
                    payload, 
                    NEOPETS_URLS.NEO_MYSTERY_ISLAND_TRAINING_SCHOOL_END, 
                    self._context, self._page, 
                    NEOPETS_URLS.NEO_MYSTERY_ISLAND_TRAINING_SCHOOL_STATUS
                    )
            
            return True
        
        except Exception as e:
            print(f"{__name__} error {e} Traceback: {traceback.format_exc()}")    


        return False

    async def study(self) -> bool:
        try:
            payload = {"type" : "start", "course_type": self._course_name, "pet_name": self._pet_name}
            await web.post(payload,
                           NEOPETS_URLS.NEO_MYSTERY_ISLAND_TRAINING_SCHOOL_START,
                           self._context, self._page,
                           NEOPETS_URLS.NEO_MYSTERY_ISLAND_TRAINING_SCHOOL_COURSES)
            

        except Exception as e:
            print(f"{__name__} error {e} Traceback: {traceback.format_exc()}")    

        return False

    async def buy(self) -> bool:
        try:
            await self._page.goto(NEOPETS_URLS.NEO_MYSTERY_ISLAND_TRAINING_SCHOOL_STATUS, timeout=120000)
            await self.collect()

            shopWizard = shop_wizard.ShopWizard(self._context, self._page)
            for item in self._active_pet["pay_items"]:
                try:
                    result = await shopWizard.buy(item, quantity=1, max_searches=5, max_price=20000)
                    self._buy_infos.append({result["item_name"]: result["price"]})
                except Exception as e:
                    print(f"{__name__} error : {e} Traceback: {traceback.format_exc()}")

            return True
        except Exception as e:
            print(f"{__name__} error : {e} Traceback: {traceback.format_exc()}")

        return False
    
    async def pay(self) -> bool:
        try:
            await web.get(NEOPETS_URLS.NEO_MYSTERY_ISLAND_TRAINING_SCHOOL_PAY_STONE+self._pet_name,
                          self._context, self._page)
            
            return True
        except Exception as e:
            print(f"{__name__} error {e} Traceback: {traceback.format_exc()}")
            
        return False

    async def collect(self) -> list[str]:
        try:
            await self._page.goto(NEOPETS_URLS.NEO_MYSTERY_ISLAND_TRAINING_SCHOOL_STATUS, timeout=120000)
            await random_sleep()

            rows = await self._page.query_selector_all('table[width="500"] tr')

            current_pet = None
            for row in rows:
                # Get pet information
                pet_info_element = await row.query_selector('td[colspan="2"]')
                if pet_info_element:
                    pet_info_text = await pet_info_element.inner_text()
                    pet_name = pet_info_text.split(" (Level ")[0]
                    level = int(pet_info_text.split(" (Level ")[1].split(")")[0])
                    is_on_course = "is currently studying" in pet_info_text
                    current_pet = {
                        "name": pet_name,
                        "level": level,
                        "is_on_course": is_on_course,
                        "pay_items": [],
                        "attributes": {}
                    }

                # Get attributes
                attribute_element = await row.query_selector('td[align="center"][width="250"]')
                if attribute_element and current_pet:
                    attributes = {}
                    stats_text = await attribute_element.text_content()
                    stats_lines = stats_text.split("\n")

                    pattern = re.compile(r"Lvl\s*:\s*(\d+)\s*Str\s*:\s*(\d+)\s*Def\s*:\s*(\d+)\s*Mov\s*:\s*(\d+)\s*Hp\s*:\s*(\d+) / (\d+)")
                    for index in stats_lines:
                        if index:
                            match = pattern.search(index)
                            if match:
                                attributes["Level"] = int(match.group(1))
                                attributes["Strength"] = int(match.group(2))
                                attributes["Defence"] = int(match.group(3))
                                attributes["Agility"] = int(match.group(4))
                                attributes["Endurance"] = int(match.group(6))

                                if self._course_name == "Level":
                                    self.now_value = attributes["Level"]
                                if self._course_name == "Strength":
                                    self.now_value = attributes["Strength"]
                                if self._course_name == "Defence":
                                    self.now_value = attributes["Defence"]
                                if self._course_name == "Agility":
                                    self.now_value = attributes["Agility"]
                                if self._course_name == "Endurance":
                                    self.now_value = attributes["Endurance"]
                                
                        current_pet["attributes"] = attributes

                pay_item_element = await row.query_selector('td[align="center"][width="250"]:not([bgcolor])')
                if pay_item_element and current_pet:
                    text = await pay_item_element.inner_text()
                    text = text.split("\n")

                    for index in text:
                        if index and "Codestone" in index:
                            current_pet["pay_items"].append(index.replace("\t", ""))
                            
                if current_pet["name"] == self._pet_name:
                    self._active_pet = current_pet

                self._pets.append(current_pet)
                           
        except Exception as e:
            print(f"{__name__} error {e} Traceback: {traceback.format_exc()}")
    
    async def start(self) -> Union[bool, dict, list]:
        try:
            await self.complete()
            await self.collect()

            for pet in self._pets:
                result = True
                if pet["name"] == self._pet_name:
                    if self._course_name == "Endurance":
                        result = pet["attributes"][self._course_name] < self._level_limit*2
                    else:
                        result = pet["attributes"][self._course_name] < self._level_limit

                    if result == False:
                        return False, {"pet_name": False}, []
                    
                    break

            await self.study()
            await self.buy()
            result = await self.pay()

            return result, self._active_pet, self._buy_infos

        except Exception as e:
            print(f"{__name__} error {e} Traceback: {traceback.format_exc()}")

        return False, self._active_pet, self._buy_infos

class SwashbucklingAcademy(TrainingSchool):
    def __init__(self, 
                 context: BrowserContext, 
                 page: Page, 
                 pet_name: str, 
                 course_name: str, 
                 target_value: int) -> None:
        super().__init__(context, page, pet_name, course_name, target_value)
        self._level_limit = 40
    
    async def complete(self) -> bool:
        try:
            payload = {"type" : "complete", "pet_name": self._pet_name}
            rep = await web.post(
                    payload, 
                    NEOPETS_URLS.NEO_SWASHBUCKLING_ACADEMY_END, 
                    self._context, self._page, 
                    NEOPETS_URLS.NEO_SWASHBUCKLING_ACADEMY_STATUS
                    )
            
            return True
        
        except Exception as e:
            print(f"{__name__} error {e} Traceback: {traceback.format_exc()}")    


        return False

    async def study(self) -> bool:
        try:
            payload = {"type" : "start", "course_type": self._course_name, "pet_name": self._pet_name}
            await web.post(payload,
                           NEOPETS_URLS.NEO_SWASHBUCKLING_ACADEMY_START,
                           self._context, self._page,
                           NEOPETS_URLS.NEO_SWASHBUCKLING_ACADEMY_COURSES)
            

        except Exception as e:
            print(f"{__name__} error {e} Traceback: {traceback.format_exc()}")    

        return False

    async def buy(self) -> bool:
        try:
            await self._page.goto(NEOPETS_URLS.NEO_SWASHBUCKLING_ACADEMY_STATUS, timeout=120000)
            await self.collect()

            shopWizard = shop_wizard.ShopWizard(self._context, self._page)
            for item in self._active_pet["pay_items"]:
                try:
                    result = await shopWizard.buy(item, quantity=1, max_searches=5, max_price=20000)
                    self._buy_infos.append({result["item_name"]: result["price"]})
                except Exception as e:
                    print(f"{__name__} error : {e} Traceback: {traceback.format_exc()}")

            return True
        except Exception as e:
            print(f"{__name__} error : {e} Traceback: {traceback.format_exc()}")

        return False
    
    async def pay(self) -> bool:
        try:
            payload = {"pet_name": self._pet_name, "type": "pay"}
            await web.post(
                payload,
                NEOPETS_URLS.NEO_SWASHBUCKLING_ACADEMY_PAY,
                self._context, self._page,
                NEOPETS_URLS.NEO_SWASHBUCKLING_ACADEMY_STATUS
                )

            return True
        except Exception as e:
            print(f"{__name__} error {e} Traceback: {traceback.format_exc()}")
            
        return False

    async def collect(self) -> None:
        try:
            await self._page.goto(NEOPETS_URLS.NEO_SWASHBUCKLING_ACADEMY_STATUS, timeout=120000)
            await random_sleep()

            rows = await self._page.query_selector_all('table[width="500"] tr')

            current_pet = None
            for row in rows:
                # Get pet information
                pet_info_element = await row.query_selector('td[colspan="2"]')
                if pet_info_element:
                    pet_info_text = await pet_info_element.inner_text()
                    pet_name = pet_info_text.split(" (Level ")[0]
                    level = int(pet_info_text.split(" (Level ")[1].split(")")[0])
                    is_on_course = "is currently studying" in pet_info_text
                    current_pet = {
                        "name": pet_name,
                        "level": level,
                        "is_on_course": is_on_course,
                        "pay_items": [],
                        "attributes": {}
                    }

                # Get attributes
                attribute_element = await row.query_selector('td[align="center"][width="250"]')
                if attribute_element and current_pet:
                    attributes = {}
                    text = await attribute_element.inner_text()
                    text = text.split("\n")

                    for index in text:
                        if index and "Lvl" in index:
                            attributes["Level"] = int(index.split("Lvl : ")[1].split("\n")[0])
                            if self._course_name == "Level":
                                self.now_value = attributes["Level"]
                        elif index and "Str" in index:
                           attributes["Strength"] = int(index.split("Str : ")[1].split("\n")[0])
                           if self._course_name == "Strength":
                               self.now_value = attributes["Strength"]
                        elif index and "Def" in index:
                            attributes["Defence"] = int(index.split("Def : ")[1].split("\n")[0])
                            if self._course_name == "Defence":
                                self.now_value = attributes["Defence"]
                        elif index and "Mov" in index:
                            attributes["Agility"] = int(index.split("Mov : ")[1].split("\n")[0])
                            if self._course_name == "Agility":
                                self.now_value = attributes["Agility"]
                        elif index and "Hp" in index:
                            hp_text = int(index.replace(" ","").split("Hp:")[1].split("/")[1])
                            attributes["Endurance"] = hp_text
                            if self._course_name == "Endurance":
                                self.now_value = attributes["Endurance"]
                                
                        current_pet["attributes"] = attributes


                pay_item_element = await row.query_selector('table[align="center"][cellpadding="3"]')
                if pay_item_element and current_pet:
                    text = await pay_item_element.inner_text()
                    text = text.split("\n")

                    for index in text:
                        if index and "Dubloon" in index:
                            current_pet["pay_items"].append(index.replace("\t", ""))
                            
                if current_pet["name"] == self._pet_name:
                    self._active_pet = current_pet

                self._pets.append(current_pet)
                           
        except Exception as e:
            print(f"{__name__} error {e} Traceback: {traceback.format_exc()}")
    
    async def start(self) -> Union[bool, dict, list]:
        try:
            await self.complete()
            await self.collect()

            for pet in self._pets:
                result = True
                if pet["name"] == self._pet_name:
                    if self._course_name == "Endurance":
                        result = pet["attributes"][self._course_name] < self._level_limit*2
                    else:
                        result = pet["attributes"][self._course_name] < self._level_limit

                    if result == False:
                        return False, {"pet_name": False}, []
                    
                    break

            await self.study()
            await self.buy()
            result = await self.pay()

            return result, self._active_pet, self._buy_infos

        except Exception as e:
            print(f"{__name__} error {e} Traceback: {traceback.format_exc()}")

        return False, self._active_pet, self._buy_infos