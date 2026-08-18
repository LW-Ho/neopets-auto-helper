import asyncio
import json
import re
from playwright.async_api import Page, BrowserContext
import urls.neopets_urls as NEOPETS_URLS
from utility import random_sleep, web

# Safety bounds for the void-essence task so it can never hang when the TVW event
# is over (map pages then return no essence, or an HTML error page instead of JSON).
VOID_FETCH_TIMEOUT = 20      # seconds: per-map raw HTTP probe
VOID_OVERALL_TIMEOUT = 240   # seconds: hard cap for the whole void task
HOSPITAL_OVERALL_TIMEOUT = 240   # seconds: hard cap for the whole volunteer task

async def _wait_for_button(page: Page, name: str, timeout: int = 15000) -> None:
    '''
    The volunteer buttons ("Join Shift"/"Complete") are rendered by the page's JS
    AFTER it fetches shift data, so they are NOT present at domcontentloaded. Wait
    (bounded) for the button to render before reading it; if there are genuinely no
    shifts, this times out and the caller proceeds (and then stops). Never raises.
    '''
    try:
        await page.get_by_role("button", name=name).first.wait_for(state="attached", timeout=timeout)
    except Exception:
        pass

async def _click_complete_button_if_exists(page: Page, role: str, name: str) -> str | None:
    button = page.get_by_role(role, name=name).first

    if await button.count() > 0:
        button_id = await button.get_attribute("data-id")
        print(f"Clicked the button: {name}, data-id: {button_id}")
        return button_id
    else:
        print(f"[hospital] button not found: {name}")
        return None

async def _click_join_button_if_exists(page: Page, role: str, name: str) -> str | None:
    button = page.get_by_role(role, name=name).first

    if await button.count() > 0:
        button_id = await button.get_attribute("id")
        button_id = button_id.replace("VolunteerButton", "")
        print(f"Clicked the button: {name}, id: {button_id}")
        return button_id
    else:
        print(f"[hospital] button not found: {name}")
        return None

async def get_hosptial(context: BrowserContext, page: Page, active_pet_name: str = "") -> bool:
    await random_sleep()
    _page = None

    async def _run():
        nonlocal _page
        _page = await context.new_page()
        count = 0

        while True:
            await web.goto(_page, NEOPETS_URLS.NEO_HOSPITAL_VOLUNTEER_HOME_PAGE)
            await _wait_for_button(_page, "Join Shift")
            await random_sleep(1, 3)
            content = await _page.content()
            ck_match = re.search(r"function getCK\(\) \{\s*return '([^']+)';\s*\}", content)
            ck_value = ck_match.group(1) if ck_match else None
            print(f"[hospital] join loop #{count}: getCK={'ok' if ck_value else 'MISSING'}")

            fight_id = await _click_join_button_if_exists(_page, "button", "Join Shift")
            if not fight_id:
                if "VolunteerButton" in content or "Join Shift" in content:
                    print("[hospital] 'Join Shift' present in HTML but not matched as a button role -- markup/selector changed")
                else:
                    print("[hospital] no 'Join Shift' shift available (all joined, or event inactive)")
                break
            if fight_id:
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
                        if pet["name"] == active_pet_name:
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
                count += 1

            if count >= 10:
                # NEO_TVW_COLLECT_PRIZE_STORY
                # _ref_ck: 
                # mode: comicPrize
                # plot: tvw
                # ch: 5
                # pg: 2
                # read: 3
                break

        complete_count = 0
        while complete_count < 20:
            complete_count += 1
            await web.goto(_page, NEOPETS_URLS.NEO_HOSPITAL_VOLUNTEER_HOME_PAGE)
            await _wait_for_button(_page, "Complete")
            await random_sleep(1, 3)
            content = await _page.content()
            ck_match = re.search(r"function getCK\(\) \{\s*return '([^']+)';\s*\}", content)
            ck_value = ck_match.group(1) if ck_match else None
            print(f"[hospital] complete loop #{complete_count}: getCK={'ok' if ck_value else 'MISSING'}")

            button_id = await _click_complete_button_if_exists(_page, "button", "Complete")
            if not button_id:
                if "Complete" in content:
                    print("[hospital] 'Complete' present in HTML but not matched as a button role -- markup/selector changed")
                else:
                    print("[hospital] no 'Complete' shift ready yet; stopping complete loop")
                break
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
            else:
                break

    # Hard cap the whole task so the volunteer loops can never hang inside the
    # TaskGroup (e.g. if the event ends and the page state stops progressing).
    try:
        await asyncio.wait_for(_run(), timeout=HOSPITAL_OVERALL_TIMEOUT)
    except asyncio.TimeoutError:
        print(f"[hospital] overall timeout ({HOSPITAL_OVERALL_TIMEOUT}s) reached -- bailing out to avoid hanging")
    except Exception as e:
        print(f"get_tvw_hospital complete {e}")
    finally:
        if _page is not None:
            await random_sleep()
            try:
                await _page.close()
            except Exception:
                pass

    return True

async def get_void_location(context: BrowserContext, page: Page) -> bool:
    await random_sleep(1, 3)
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
        "https://www.neopets.com/moon/index.phtml",
        "https://www.neopets.com/prehistoric/plateau.phtml"
    ]

    total = len(void_essence_location_map_link)
    _sem = asyncio.Semaphore(6)

    async def _scan(index: int, _map: str):
        # Read-only probe via page.request (raw HTML, NO browser render): the
        # placeEssenceOnMap(...) call and getCK() live in inline <script> in the
        # server HTML, so opening/rendering a tab per map is unnecessary. This is
        # the change that turns a ~5-10 min sequential tab-by-tab scan into a
        # bounded-concurrency HTTP sweep of a few seconds. Each probe is time-boxed
        # so a single slow/hanging map cannot stall the whole sweep.
        async with _sem:
            try:
                html = await asyncio.wait_for(
                    web.get(_map, context, page, referer=NEOPETS_URLS.NEO_HOMEPAGE),
                    timeout=VOID_FETCH_TIMEOUT,
                )
            except Exception as e:
                print(f"[void] {index}/{total} fetch error/timeout: {_map} ({type(e).__name__})")
                return _map, None
        hit = html if (html and 'placeEssenceOnMap' in html) else None
        print(f"[void] {index}/{total} {'FOUND essence' if hit else 'none'} - {_map}")
        return _map, hit

    async def _run() -> bool:
        results = await asyncio.gather(
            *[_scan(i + 1, m) for i, m in enumerate(void_essence_location_map_link)],
            return_exceptions=True,
        )
        hits = [r for r in results if isinstance(r, tuple) and r[1]]

        if not hits:
            print("[void] no essence on any map (event inactive or already collected today)")
            return True

        for _map, content in hits:
            # Parse the token + essence list. An event-ended page can be malformed,
            # so a parse failure just skips that map instead of aborting everything.
            try:
                ck_match = re.search(r"function getCK\(\) \{\s*return '([^']+)';\s*\}", content)
                ck_value = ck_match.group(1) if ck_match else None

                essence_match = re.search(r"placeEssenceOnMap\((\[.*?\])\);", content, re.DOTALL)
                essence_array = eval(essence_match.group(1)) if essence_match else None
            except Exception as e:
                print(f"[void] parse error on {_map} ({e}) -- skipping (event may have ended)")
                continue

            if not ck_value or not essence_array:
                print(f"[void] {_map}: no usable ck/essence -- skipping (event may have ended)")
                continue

            for _essence in essence_array:
                # Collect one essence. Guarded per-essence so one bad response
                # neither crashes the task nor leaves it spinning.
                try:
                    payload = {
                        "hash": str(_essence.get('hash')),
                        "id": str(_essence.get('id')),
                        "day": str(_essence.get('day')),
                        "_ref_ck": str(ck_value),
                    }
                    rep = await web.post_form_data(
                        payload, NEOPETS_URLS.NEO_TVW_COLLECT_VOID, context, page, _map
                    )
                    await random_sleep(1, 3)
                except Exception as e:
                    print(f"[void] collect request error on {_map} ({e}) -- continuing")
                    continue

                # When the event is over (or we are not logged in) the endpoint
                # returns an HTML error page, not JSON -> stop gracefully.
                try:
                    rep_json = json.loads(rep)
                except (json.JSONDecodeError, TypeError):
                    snippet = (rep or "").strip().replace("\n", " ")[:120]
                    print(f"[void] non-JSON collect response -- event likely ended. snippet: {snippet!r}")
                    return True

                print(rep_json)
                if rep_json.get('showComplete'):
                    return True
                if rep_json.get('error') or rep_json.get('success') is False:
                    print(f"[void] collect did not succeed (event may have ended): {rep_json}")

        return True

    # Hard cap the whole task: no matter what the event's state is, this returns
    # within VOID_OVERALL_TIMEOUT instead of hanging inside the TaskGroup.
    try:
        return await asyncio.wait_for(_run(), timeout=VOID_OVERALL_TIMEOUT)
    except asyncio.TimeoutError:
        print(f"[void] overall timeout ({VOID_OVERALL_TIMEOUT}s) reached -- bailing out to avoid hanging")
        return False
    except Exception as e:
        print(f"get_tvw_void_location complete {e}")
        return False