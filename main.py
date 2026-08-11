import asyncio
from functools import partial
import json
import sys
import time
import traceback
from playwright.async_api import Browser, BrowserContext, Page
from camoufox.async_api import AsyncCamoufox

from app.account import Account
from app.notify import build_notifier
from dailies import jelly as JELLY, \
    omelette as OMELETTE, \
    fishing as FISHING, \
    springs as SPRINGS, \
    fruit as FRUIT, \
    tvw_event as TVW_EVENT, \
    trudys as TRUDYS, \
    shrine as SHRINE, \
    tombola as TOMBOLA, \
    tdmbgpop as TDMBGPOP, \
    advent_calendar as ADVENTCALENDAR
from utility import quick_stock as QS, timestamp as TS, stocks, petlab
from utility.bank import Bank
from utility.training_school import SwashbucklingAcademy, MysteryIsland, SecretNinja
from app.env import load_account, NEOAccount

TIME_EXPIRY: dict = {}

def create_task_if_needed(flag, key, task_function, tg, tasks, time_expiry_map):
    try:
        if flag:
            time_expiry = time_expiry_map.get(key)
            if time_expiry is None or time.time() > time_expiry:
                task = tg.create_task(task_function(), name=key)  # task_function now handles its own arguments
                tasks.append(task)
    except Exception as e:
        print(e)

async def run(neoaccount: NEOAccount) -> None:
    global TIME_EXPIRY
    all_result = {}
    browser: Browser = None
    context: BrowserContext = None
    try:
        if TIME_EXPIRY.get(neoaccount.ACTIVE_PET_NAME) is None:
            TIME_EXPIRY[neoaccount.ACTIVE_PET_NAME] = {}

        time_expiry = TIME_EXPIRY[neoaccount.ACTIVE_PET_NAME].get('Login')
        if time_expiry is not None and time.time() < time_expiry:
            return {neoaccount.USERNAME: all_result}

        camoufox = AsyncCamoufox(headless=False)
        browser = await camoufox.start()
        context = await browser.new_context(viewport={"width":800,"height":600})
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
        all_result['UserInfo'] = [neoaccount.USERNAME, neoaccount.ACTIVE_PET_NAME]

        notifier = build_notifier(neoaccount)

        if r == False:
            # Login failed: skip every daily task. Running them while logged out
            # only makes each one navigate and fail, which wastes minutes and can
            # look like the process is "stuck". Record the cooldown, alert, and bail.
            TIME_EXPIRY[neoaccount.ACTIVE_PET_NAME]['Login'] = TS.get_timestamp(10)
            print(f"{neoaccount.USERNAME} login failed; skipping all tasks.")
            notifier.notify('error', all_result)
            return {neoaccount.USERNAME: all_result}

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
                    key = "buy_stocks"
                    time_expiry = TIME_EXPIRY[neoaccount.ACTIVE_PET_NAME].get(key)
                    if time_expiry is None or time.time() > time_expiry:

                        stock = stocks.Stock(context, page, neoaccount.PIN_CODE)
                        result = await stock.buy_stock()

                        all_result[key] = result
                        TIME_EXPIRY[neoaccount.ACTIVE_PET_NAME][key] = TS.get_timestamp(8)

                if neoaccount.SELL_STOCK_FLAG:
                    key = "sell_stocks"
                    time_expiry = TIME_EXPIRY[neoaccount.ACTIVE_PET_NAME].get(key)
                    if time_expiry is None or time.time() > time_expiry:

                        stock = stocks.Stock(context, page, neoaccount.PIN_CODE)
                        flag, result = await stock.sell_stock()

                        all_result[key] = [flag, result]
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
                create_task_if_needed(
                    neoaccount.ADVENTCALENDAR_FLAG, "ADVENTCALENDAR", lambda: ADVENTCALENDAR.get(context, page), tg, tasks, TIME_EXPIRY[neoaccount.ACTIVE_PET_NAME]
                )
                if neoaccount.TVW_EVENT_FLAG:
                    create_task_if_needed(
                        True, "TVW_HOSPITAL", partial(TVW_EVENT.get_hosptial, context, page, active_pet_name=neoaccount.ACTIVE_PET_NAME), 
                        tg, tasks, TIME_EXPIRY[neoaccount.ACTIVE_PET_NAME]
                    )
                    create_task_if_needed(
                        True, "TVW_VOID_LOCATION", lambda: TVW_EVENT.get_void_location(context, page), tg, tasks, TIME_EXPIRY[neoaccount.ACTIVE_PET_NAME]
                    )
                

                try:
                    for task in tasks:
                        result = await task  # waiting for task all done.
                        print(f"{neoaccount.USERNAME}, Task {task.get_name()} completed with result: {result}")
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
                        print(f"{neoaccount.USERNAME}, Training task {task.get_name()} completed with result: {result} , {pet}, {buy}")
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
            notifier.notify('error', all_result)

        if neoaccount.AUTO_SAVE_TO_SAFTY_BOX:
            result = await QS.run(context, page)
            all_result['safty box'] = result

        notifier.notify('ok', all_result)

    except Exception as e:
        print(f"{e}")
    finally:
        if context is not None:
            await context.close()
        if browser is not None:
            await browser.close()

    return {neoaccount.USERNAME: all_result}

async def main() -> int:
    global TIME_EXPIRY
    account = load_account()

    # Stateless run: no cooldown records are read or written, so every container starts
    # clean and attempts all enabled tasks. Timing is controlled externally (by whatever
    # schedules the `docker run`). Cookies still persist per-account via sessions/.
    TIME_EXPIRY = {account.ACTIVE_PET_NAME: {}}

    try:
        result = await run(account)
    except Exception as e:
        print(f"{account.USERNAME} run error: {e}  Traceback: {traceback.format_exc()}")
        result = {account.USERNAME: {"Login": False}}

    print(f'Work done, {json.dumps(result, indent=4, ensure_ascii=False)} ')

    # Exit code lets a scheduler detect a failed run. Exit 0 ONLY on a confirmed login;
    # an empty result (browser/setup crash) means nothing ran, so it must be non-zero.
    all_result = result.get(account.USERNAME, {}) if isinstance(result, dict) else {}
    return 0 if all_result.get("Login") else 1

if __name__ == "__main__":
    try:
        exit_code = asyncio.run(main())
    except Exception as e:
        print(f"Fatal error: {e}  Traceback: {traceback.format_exc()}")
        exit_code = 1
    sys.exit(exit_code)
