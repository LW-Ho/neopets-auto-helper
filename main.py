import asyncio
from functools import partial
import json
from pathlib import Path
from os.path import exists
import time
import traceback
from playwright.async_api import Playwright, async_playwright
from playwright.async_api import Browser, BrowserContext, Page

from app.account import Account
from dailies import jelly as JELLY, \
    omelette as OMELETTE, \
    fishing as FISHING, \
    springs as SPRINGS, \
    fruit as FRUIT, \
    tvw_event as TVW_EVENT, \
    trudys as TRUDYS, \
    shrine as SHRINE, \
    tombola as TOMBOLA, \
    tdmbgpop as TDMBGPOP
from utility import quick_stock as QS, random_sleep, timestamp as TS, stocks, petlab
from utility.bank import Bank
from utility.training_school import SwashbucklingAcademy, MysteryIsland, SecretNinja
from app.env import NEOACCOUNT_DATA, NEOAccount

TIME_EXPIRY: dict = {}
SLEEP_INTERVAL = 3000

def create_task_if_needed(flag, key, task_function, tg, tasks, time_expiry_map):
    try:
        if flag:
            time_expiry = time_expiry_map.get(key)
            if time_expiry is None or time.time() > time_expiry:
                task = tg.create_task(task_function(), name=key)  # task_function now handles its own arguments
                tasks.append(task)
    except Exception as e:
        print(e)

async def run(playwright: Playwright, neoaccount: NEOAccount) -> None:
    global TIME_EXPIRY
    all_result = {}
    neopets: Account = None
    try:
        browser: Browser = await playwright.chromium.launch(
            headless=False,
            slow_mo=100
            )
        context: BrowserContext = await browser.new_context(
            viewport={"width":800,"height":600}
            )
        page: Page = await context.new_page()

        neopets: Account = Account(
            neoaccount.USERNAME, 
            neoaccount.PASSWORD, 
            neoaccount.ACTIVE_PET_NAME, 
            legacy=neoaccount.LEGACY,
            neopass_username=neoaccount.NEOPASS_USERNAME
            )
        print(f'{neopets._username} / {neopets._neopass_username} Login...')
        r = await neopets.login(context, page)
        all_result['Login'] = r

        if TIME_EXPIRY.get(neoaccount.ACTIVE_PET_NAME) is None:
            TIME_EXPIRY[neoaccount.ACTIVE_PET_NAME] = {}

        try:
            async with asyncio.TaskGroup() as tg:
                tasks = []
                training_tasks = []

                if neoaccount.BANK_INTEREST_FLAG:
                    key = "bank_collect_interest"
                    time_expiry = TIME_EXPIRY[neoaccount.ACTIVE_PET_NAME].get(key)
                    if time_expiry is None or time.time() > time_expiry:
                        bank = Bank(context, page)
                        if neoaccount.PIN_CODE:
                            bank.set_pin_code(neoaccount.PIN_CODE)

                        result = await bank.collect_interest()
                        all_result[key] = result

                        TIME_EXPIRY[neoaccount.ACTIVE_PET_NAME][key] = TS.get_timestamp(8)
                
                if neoaccount.BUY_STOCK_FLAG:
                    key = "but_stocks"
                    time_expiry = TIME_EXPIRY[neoaccount.ACTIVE_PET_NAME].get(key)
                    if time_expiry is None or time.time() > time_expiry:

                        stock = stocks.Stock(context, page, neoaccount.PIN_CODE)
                        result = await stock.buy_stock()

                        all_result[key] = result
                        TIME_EXPIRY[neoaccount.ACTIVE_PET_NAME][key] = TS.get_timestamp(8)

                if neoaccount.PETLAB_FLAG and neoaccount.PETLAB_NAME:
                    key = "petlab2"
                    time_expiry = TIME_EXPIRY[neoaccount.ACTIVE_PET_NAME].get(key)
                    if time_expiry is None or time.time() > time_expiry:

                        petlabobj = petlab.PetLab(context, page, neoaccount.PETLAB_NAME)
                        result = await petlabobj.run()

                        all_result[key] = result
                        TIME_EXPIRY[neoaccount.ACTIVE_PET_NAME][key] = TS.get_timestamp(10)

                if neoaccount.PETPETLAB_FLAG and neoaccount.PETPETLAB_NAME:
                    key = "petpetlab"
                    time_expiry = TIME_EXPIRY[neoaccount.ACTIVE_PET_NAME].get(key)
                    if time_expiry is None or time.time() > time_expiry:

                        petpetlabobj = petlab.PetpetLab(context, page, neoaccount.PETPETLAB_NAME)
                        result = await petpetlabobj.run()

                        all_result[key] = result
                        TIME_EXPIRY[neoaccount.ACTIVE_PET_NAME][key] = TS.get_timestamp(10)

                create_task_if_needed(
                    neoaccount.TRAINING_SWASHBUCKLING_ACADEMY["PET_NAME"], "SwashbucklingAcademy", 
                    lambda: SwashbucklingAcademy(context,
                                                page,
                                                neoaccount.TRAINING_SWASHBUCKLING_ACADEMY["PET_NAME"],
                                                neoaccount.TRAINING_SWASHBUCKLING_ACADEMY["PET_COURSE_NAME"],
                                                neoaccount.TRAINING_SWASHBUCKLING_ACADEMY["TARGET_VALUE"]
                                                ).start(),
                                                tg, training_tasks, TIME_EXPIRY[neoaccount.ACTIVE_PET_NAME]
                )

                create_task_if_needed(
                    neoaccount.TRAINING_MYSTERY_ISLAND["PET_NAME"], "MysteryIsland", 
                    lambda: MysteryIsland(context,
                                                page,
                                                neoaccount.TRAINING_MYSTERY_ISLAND["PET_NAME"],
                                                neoaccount.TRAINING_MYSTERY_ISLAND["PET_COURSE_NAME"],
                                                neoaccount.TRAINING_MYSTERY_ISLAND["TARGET_VALUE"]
                                                ).start(),
                                                tg, training_tasks, TIME_EXPIRY[neoaccount.ACTIVE_PET_NAME]
                )

                create_task_if_needed(
                    neoaccount.TRAINING_SECRET_NINJA["PET_NAME"], "SecretNinja", 
                    lambda: SecretNinja(context,
                                                page,
                                                neoaccount.TRAINING_SECRET_NINJA["PET_NAME"],
                                                neoaccount.TRAINING_SECRET_NINJA["PET_COURSE_NAME"],
                                                neoaccount.TRAINING_SECRET_NINJA["TARGET_VALUE"]
                                                ).start(),
                                                tg, training_tasks, TIME_EXPIRY[neoaccount.ACTIVE_PET_NAME]
                )

                create_task_if_needed(
                    neoaccount.TRUDYS_FLAG, "TRUDYS", lambda: TRUDYS.get(context, page), tg, tasks, TIME_EXPIRY[neoaccount.ACTIVE_PET_NAME]
                )
                create_task_if_needed(
                    neoaccount.JELLY_FLAG, "JELLY", lambda: JELLY.get(context, page), tg, tasks, TIME_EXPIRY[neoaccount.ACTIVE_PET_NAME]
                )
                create_task_if_needed(
                    neoaccount.OMELETTE_FLAG, "OMELETTE", lambda: OMELETTE.get(context, page), tg, tasks, TIME_EXPIRY[neoaccount.ACTIVE_PET_NAME]
                )
                create_task_if_needed(
                    neoaccount.FISHING_FLAG, "FISHING", lambda: FISHING.get(context, page), tg, tasks, TIME_EXPIRY[neoaccount.ACTIVE_PET_NAME]
                )
                create_task_if_needed(
                    neoaccount.SPRINGS_FLAG, "SPRINGS", lambda: SPRINGS.get(context, page), tg, tasks, TIME_EXPIRY[neoaccount.ACTIVE_PET_NAME]
                )
                create_task_if_needed(
                    neoaccount.FRUIT_FLAG, "FRUIT", lambda: FRUIT.get(context, page), tg, tasks, TIME_EXPIRY[neoaccount.ACTIVE_PET_NAME]
                )
                create_task_if_needed(
                    neoaccount.SHRINE_FLAG, "SHRINE", lambda: SHRINE.get(context, page), tg, tasks, TIME_EXPIRY[neoaccount.ACTIVE_PET_NAME]
                )
                create_task_if_needed(
                    neoaccount.TOMBOLA_FLAG, "TOMBOLA", lambda: TOMBOLA.get(context, page), tg, tasks, TIME_EXPIRY[neoaccount.ACTIVE_PET_NAME]
                )
                create_task_if_needed(
                    neoaccount.TDMBGPOP_FLAG, "TDMBGPOP", lambda: TDMBGPOP.get(context, page), tg, tasks, TIME_EXPIRY[neoaccount.ACTIVE_PET_NAME]
                )
                
                if neoaccount.TVW_EVENT_FLAG:
                    create_task_if_needed(
                        True, "TVW_HOSPITAL", partial(TVW_EVENT.get_hosptial, context, page), 
                        tg, tasks, TIME_EXPIRY[neoaccount.ACTIVE_PET_NAME]
                    )
                    create_task_if_needed(
                        True, "TVW_VOID_LOCATION", lambda: TVW_EVENT.get_void_location(context, page), tg, tasks, TIME_EXPIRY[neoaccount.ACTIVE_PET_NAME]
                    )
                

                try:
                    for task in tasks:
                        result = await task  # waiting for task all done.
                        print(f"Task {task.get_name()} completed with result: {result}")
                        # Update time_expiry
                        if result:
                            _time_expiry = TIME_EXPIRY[neoaccount.ACTIVE_PET_NAME].get(task.get_name())
                            if _time_expiry is None or time.time() > _time_expiry:
                                _time_hours = 23
                                if task.get_name() == "TRUDYS":
                                    _time_hours = 4
                                elif task.get_name() == "JELLY":
                                    _time_hours = 23
                                elif task.get_name() == "OMELETTE":
                                    _time_hours = 23
                                elif task.get_name() == "FISHING":
                                    _time_hours = 12
                                elif task.get_name() == "SPRINGS":
                                    _time_hours = 1
                                elif task.get_name() == "FRUIT":
                                    _time_hours = 4
                                elif task.get_name() == "TVW_HOSPITAL":
                                    _time_hours = 2
                                elif task.get_name() == "TVW_VOID_LOCATION":
                                    _time_hours = 9

                                TIME_EXPIRY[neoaccount.ACTIVE_PET_NAME][task.get_name()] = TS.get_timestamp(_time_hours)

                        all_result[task.get_name()] = result
                except Exception as e:
                    print(f"task error {e}  Traceback: {traceback.format_exc()}")

                try:
                    for task in training_tasks:
                        result, pet, buy = await task  # waiting for task all done.
                        print(f"Training task {task.get_name()} completed with result: {result} , {pet}, {buy}")
                        # Update time_expiry
                        if result:
                            _time_expiry = TIME_EXPIRY[neoaccount.ACTIVE_PET_NAME].get(task.get_name())
                            if _time_expiry is None or time.time() > _time_expiry:
                                _time_hours = 1
                                TIME_EXPIRY[neoaccount.ACTIVE_PET_NAME][task.get_name()] = TS.get_timestamp(_time_hours)

                        all_result[task.get_name()] = result
                except Exception as e:
                    print(f"Training task error {e}  Traceback: {traceback.format_exc()}")
                

        except Exception as e:
            print(f"task group error {e}  Traceback: {traceback.format_exc()}")

        if neoaccount.AUTO_SAVE_TO_SAFTY_BOX:
            result = await QS.run(context, page)
            all_result['safty box'] = result

        await context.close()
        await browser.close()
    except Exception as e:
        print(f"{e}")

    return {neoaccount.USERNAME: all_result}

async def main() -> None:
    global TIME_EXPIRY
    _report = []
    time_path = f"time/time_expiry.json"
    if exists(time_path):
        TIME_EXPIRY = json.loads(Path(time_path).read_text())
    else:
        for account in NEOACCOUNT_DATA.accounts:
            TIME_EXPIRY[account.ACTIVE_PET_NAME] = {}

    async with async_playwright() as playwright:
        tasks = [run(playwright, account) for account in NEOACCOUNT_DATA.accounts]
        result = await asyncio.gather(*tasks)
        _report.append(result)

    print(f'Work done, {json.dumps(_report, indent=4)} ')
    
    Path("time").mkdir(parents=True, exist_ok=True)
    Path(f"time/time_expiry.json").write_text(json.dumps(TIME_EXPIRY, indent=4))

    await random_sleep(SLEEP_INTERVAL+200,SLEEP_INTERVAL+600)

if __name__ == "__main__":
    while True:
        asyncio.run(main())