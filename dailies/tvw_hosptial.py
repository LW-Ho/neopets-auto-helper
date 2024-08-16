from playwright.async_api import Page, BrowserContext
import urls.neopets_urls as NEOPETS_URLS
from utility import random_sleep

async def _click_button_if_exists(page: Page, role: str, name: str):
    button = page.get_by_role(role, name=name).first
    if await button.count() > 0:
        await button.click()
        print(f"Clicked the button: {name}")
    else:
        raise Exception(f"Button not found: {name}")

async def get(context: BrowserContext, page: Page, pets_list: list) -> bool:
    await random_sleep()
    try:
        _page = await context.new_page()
        await _page.goto(NEOPETS_URLS.NEO_HOSPITAL_VOLUNTEER_HOME_PAGE)

        try:
            while True:
                await _click_button_if_exists(_page, "button", "Complete")
                await random_sleep(2,5)
                await _click_button_if_exists(_page, "button", "Back")
        except Exception as e:
            print(f"not found complete {e}")

        for pet_name in pets_list:
            try:
                await _click_button_if_exists(_page, "button", "Join Shift")
                await random_sleep(2,5)
                await _click_button_if_exists(_page, "button", "I'm Ready")
                await random_sleep(2,5)
                # check 
                await _page.locator("div").filter(has_text="Dr. G Welcome to the Neopian").nth(1).click()
                await _page.locator("#VolunteerPetList div").filter(has_text=pet_name).first.click()
                await _click_button_if_exists(_page, "button", "Join Volunteer Team")
                await random_sleep(2,5)
                await _click_button_if_exists(_page, "button", "Back")
                await random_sleep(2,5)
            except Exception as e:
                print(f"Join error")
                await _page.goto(NEOPETS_URLS.NEO_HOSPITAL_VOLUNTEER_HOME_PAGE)

            
        await random_sleep()
        return True
    except Exception as e:
        print("get_tvw_hospital complete")

    return False