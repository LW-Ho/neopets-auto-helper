from playwright.async_api import Page, BrowserContext
import urls.neopets_urls as NEOPETS_URLS
from utility import random_sleep, PlayWrightInstance, web


class PetLab(PlayWrightInstance):
    def __init__(self, context: BrowserContext, page: Page, pet_name: str) -> None:
        super().__init__(context, page)
        self._pet_name = pet_name

    async def run(self) -> bool:
        _page = await self._context.new_page()
        try:
            await web.goto(_page, NEOPETS_URLS.NEO_PET_LAB2)
            await random_sleep()

            payload = {"chosen": self._pet_name}
            rep = await web.post(
                payload, NEOPETS_URLS.NEO_PET_LAB2_PROCESS,
                self._context, self._page, referer=NEOPETS_URLS.NEO_PET_LAB2
            )
            await random_sleep()
            return True
        except Exception as e:
            print(f"{__name__} error {e}")
        finally:
            await _page.close()
        return False
    
class PetpetLab(PlayWrightInstance):
    def __init__(self, context: BrowserContext, page: Page, pet_name: str) -> None:
        super().__init__(context, page)
        self.pet_name = pet_name # chosen pet name not petpet name

    async def run(self) -> bool:
        _page = await self._context.new_page()
        try:
            await web.goto(_page, NEOPETS_URLS.NEO_PETPET_LAB)
            await random_sleep()

            payload = {"chosen": self.pet_name}
            rep = await web.post(
                payload, NEOPETS_URLS.NEO_PETPET_LAB2_PROCESS,
                self._context, self._page, referer=NEOPETS_URLS.NEO_PETPET_LAB
            )
            await random_sleep()
            return True
        except Exception as e:
            print(f"{__name__} error {e}")
        finally:
            await _page.close()
        return False