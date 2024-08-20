import re
from playwright.async_api import Page, BrowserContext
import urls.neopets_urls as NEOPETS_URLS
from utility import random_sleep, web

async def _click_button_if_exists(page: Page, role: str, name: str):
    button = page.get_by_role(role, name=name).first
    if await button.count() > 0:
        await button.click()
        print(f"Clicked the button: {name}")
    else:
        raise Exception(f"Button not found: {name}")

async def get_hosptial(context: BrowserContext, page: Page, pets_list: list) -> bool:
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

async def get_void_location(context: BrowserContext, page: Page) -> bool:
    await random_sleep()
    void_essence_location_map_link = [
        "http://neopets.com/faerieland/faeriecity.phtml"
        "http://neopets.com/space/index.phtml",
        "http://neopets.com/winter/terrormountain.phtml"
    ]
    # "http://neopets.com/halloween/neovia.phtml",
    # "http://neopets.com/desert/index.phtml",
    # "http://neopets.com/market_plaza.phtml"
    # "http://neopets.com/shenkuu/index.phtml"
    # "http://neopets.com/worlds/index_geraptiku.phtml"
    # "http://neopets.com/water/index_ruins.phtml"

    try:
        for _map in void_essence_location_map_link:
            _page = await context.new_page()
            await _page.goto(_map)
            await random_sleep()
            
            content = await _page.content()

            if 'placeEssenceOnMap' in content:
                ck_match = re.search(r"function getCK\(\) \{\s*return '([^']+)';\s*\}", content)
                ck_value = ck_match.group(1) if ck_match else None

                essence_match = re.search(r"placeEssenceOnMap\((\[.*?\])\);", content, re.DOTALL)
                essence_array = eval(essence_match.group(1)) if essence_match else None

                # collect data
                data = {
                    "ck": ck_value,
                    "essence": essence_array
                }

                print(data)

                for _essence in data["essence"]:
                    payload = {
                        "hash": str(_essence['hash']),
                        "id": str(_essence['id']),
                        "day": str(_essence['day']),
                        "_ref_ck": str(data['ck'])
                    }
                    print(payload)
                    rep = await web.post_form_data(
                        payload, NEOPETS_URLS.NEO_TVW_COLLECT_VOID, context, _page, _map
                    )
                    await random_sleep()

                    print(rep)

        return True
    except Exception as e:
        print("get_tvw_void_location complete")

    return False