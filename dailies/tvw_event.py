import json
import re
from playwright.async_api import Page, BrowserContext
import urls.neopets_urls as NEOPETS_URLS
from utility import random_sleep, web

async def _click_button_if_exists(page: Page, role: str, name: str):
    # button = page.get_by_role(role, name=name).first
    # if await button.count() > 0:
    #     await button.click()
    #     print(f"Clicked the button: {name}")
    # else:
    #     raise Exception(f"Button not found: {name}")

    button = page.get_by_role(role, name=name).first

    if await button.count() > 0:
        button_id = await button.get_attribute("data-id") 
        # await button.click()
        print(f"Clicked the button: {name}")
        return button_id
    else:
        raise Exception(f"Button not found: {name}")
    

async def get_hosptial(context: BrowserContext, page: Page) -> bool:
    await random_sleep()
    try:
        _page = await context.new_page()

        while True:
            await _page.goto(NEOPETS_URLS.NEO_HOSPITAL_VOLUNTEER_HOME_PAGE, timeout=120000)
            await random_sleep()
            content = await _page.content()
            ck_match = re.search(r"function getCK\(\) \{\s*return '([^']+)';\s*\}", content)
            ck_value = ck_match.group(1) if ck_match else None

            button_id = await _click_button_if_exists(_page, "button", "Complete")
            payload = {
                "_ref_ck": ck_value,
                "id": button_id
            }
            rep = await web.post_form_data(
                payload, NEOPETS_URLS.NEO_HOSPITAL_VOLUNTEER_COMPLETE,
                context, _page, NEOPETS_URLS.NEO_HOSPITAL_VOLUNTEER_HOME_PAGE
            )
            rep_json: dict = json.loads(rep)
            fight_id = 3
            if rep_json.get("success"):
                fight_id = rep_json["fight"]
                payload = {
                    "_ref_ck": ck_value,
                    "fight_id": fight_id
                }
                rep = await web.post_form_data(
                    payload, NEOPETS_URLS.NEO_HOSPITAL_VOLUNTEER_GET_PETS, context, _page, NEOPETS_URLS.NEO_HOSPITAL_VOLUNTEER_HOME_PAGE
                )

                rep_json: dict = json.loads(rep)
                pet_name = ""
                if rep_json.get("success"):
                    
                    for pet in rep_json["pets"]:
                        if pet.get("disabled"):
                            continue
                        pet_name = pet["name"]
                        break

                if pet_name:
                    payload = {
                        "_ref_ck": ck_value,
                        "fight_id": fight_id,
                        "pet_name": pet_name
                    }
                    rep = await web.post_form_data(
                        payload, NEOPETS_URLS.NEO_HOSPITAL_VOLUNTEER_JOIN, context, _page, NEOPETS_URLS.NEO_HOSPITAL_VOLUNTEER_HOME_PAGE
                    )

                    print(rep)

    except Exception as e:
        print(f"get_tvw_hospital complete {e}")

    await random_sleep()
    await _page.close()

    return True

async def get_void_location(context: BrowserContext, page: Page) -> bool:
    await random_sleep()
    void_essence_location_map_link = [
        "https://www.neopets.com/desert/qasala.phtml",
        "https://www.neopets.com/winter/terrormountain.phtml",
        "https://www.neopets.com/medieval/index_farm.phtml",
        "https://www.neopets.com/altador/index.phtml",
        "https://www.neopets.com/worlds/index_kikolake.phtml",
        "https://www.neopets.com/shenkuu/index.phtml",
        "https://www.neopets.com/medieval/brightvale.phtml",
        "https://www.neopets.com/objects.phtml",
        "https://www.neopets.com/market_map.phtml",
        "https://www.neopets.com/pirates/warfwharf.phtml",
        "https://www.neopets.com/desert/sakhmet.phtml",
        "https://www.neopets.com/medieval/index_castle.phtml",
        "https://www.neopets.com/tropical/index.phtml",
        "https://www.neopets.com/desert/index.phtml",
        "https://www.neopets.com/space/recreation.phtml",
        "https://www.neopets.com/winter/icecaves.phtml",
        "https://www.neopets.com/faerieland/index.phtml",
        "https://www.neopets.com/magma/index.phtml",
        "https://www.neopets.com/medieval/index_evil.phtml",
        "https://www.neopets.com/water/index.phtml",
        "https://www.neopets.com/faerieland/faeriecity.phtml",
        "https://www.neopets.com/prehistoric/index.phtml",
        "https://www.neopets.com/water/index_ruins.phtml",
        "https://www.neopets.com/market_bazaar.phtml",
        "https://www.neopets.com/worlds/index_roo.phtml",
        "https://www.neopets.com/market_plaza.phtml",
        "https://www.neopets.com/pirates/index.phtml",
        "https://www.neopets.com/magma/caves.phtml",
        "https://www.neopets.com/worlds/index_geraptiku.phtml",
        "https://www.neopets.com/island/index.phtml",
        "https://www.neopets.com/medieval/index.phtml",
        "https://www.neopets.com/halloween/index.phtml",
        "https://www.neopets.com/halloween/index_fair.phtml",
        "https://www.neopets.com/space/hangar.phtml",
        "https://www.neopets.com/space/index.phtml",
        "https://www.neopets.com/winter/index.phtml",
        "https://www.neopets.com/halloween/neovia.phtml",
        "https://www.neopets.com/moon/index.phtml"
    ]

    try:
        for _map in void_essence_location_map_link:
            _page = await context.new_page()
            await _page.goto(_map, timeout=120000)
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
                for _essence in data["essence"]:
                    payload = {
                        "hash": str(_essence['hash']),
                        "id": str(_essence['id']),
                        "day": str(_essence['day']),
                        "_ref_ck": str(data['ck'])
                    }
                    rep = await web.post_form_data(
                        payload, NEOPETS_URLS.NEO_TVW_COLLECT_VOID, context, _page, _map
                    )
                    await random_sleep()
                    
                    rep_json = json.loads(rep)
                    print(rep_json)
                    if rep_json.get('showComplete'):
                        await _page.close()
                        return True

            await _page.close()

        return True
    except Exception as e:
        print(f"get_tvw_void_location complete {e}")

    return False