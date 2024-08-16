import asyncio
from playwright.async_api import Playwright, async_playwright, expect
from playwright.async_api import Browser

from app.account import Account
import dailies.jelly as JELLY
import dailies.omelette as OMELETTE
import dailies.fishing as FISHING
import dailies.springs as SPRINGS
import dailies.fruit as FRUIT
import dailies.tvw_hosptial as TVW_HOSPITAL
import dailies.trudys as TRUDYS
import utility.quick_stock as QS
from utility import random_sleep
from app.env import NEOACCOUNT_DATA, NEOAccount

async def run(playwright: Playwright, neoaccount: NEOAccount) -> None:
    all_result = {}
    try:
        browser: Browser = await playwright.chromium.launch(headless=False, slow_mo=100)
        context = await browser.new_context(viewport={"width":800,"height":600})
        page = await context.new_page()

        neopets: Account = Account(
            neoaccount.USERNAME, 
            neoaccount.PASSWORD, 
            neoaccount.ACTIVE_PET_NAME, 
            legacy=neoaccount.LEGACY,
            neopass_username=neoaccount.NEOPASS_USERNAME
            )
        print('Login...')
        r = await neopets.login(context, page)
        all_result['Login'] = r


        async with asyncio.TaskGroup() as tg:
            tasks = []

            if neoaccount.TRUDYS_FLAG:
                task = tg.create_task(TRUDYS.get(context, page), name="TRUDYS Task")
                tasks.append(task)

            if neoaccount.JELLY_FLAG:
                task = tg.create_task(JELLY.get(context, page), name="JELLY Task")
                tasks.append(task)

            if neoaccount.OMELETTE_FLAG:
                task = tg.create_task(OMELETTE.get(context, page), name="OMELETTE Task")
                tasks.append(task)

            if neoaccount.FISHING_FLAG:
                task = tg.create_task(FISHING.get(context, page), name="FISHING Task")
                tasks.append(task)

            if neoaccount.SPRINGS_FLAG:
                task = tg.create_task(SPRINGS.get(context, page), name="SPRINGS Task")
                tasks.append(task)

            if neoaccount.FRUIT_FLAG:
                task = tg.create_task(FRUIT.get(context, page), name="SPRINGS Task")
                tasks.append(task)

            if neoaccount.TVW_HOSPITAL_FLAG:
                task = tg.create_task(TVW_HOSPITAL.get(context, page, [neoaccount.TVW_HP_PET_NAME_1, neoaccount.TVW_HP_PET_NAME_2]), name="TVW_HOSPITAL Task")
                tasks.append(task)
            

            for task in tasks:
                result = await task  # waiting for task all done.
                print(f"Task {task.get_name()} completed with result: {result}")
                all_result[task.get_name()] = result

        if neoaccount.AUTO_SAVE_TO_SAFTY_BOX:
            result = await QS.run(context, page)
            all_result['safty box'] = result

        await context.close()
        await browser.close()
    except Exception as e:
        print(f"{e}")

    return {neoaccount.USERNAME: all_result}

async def main() -> None:
    _report = []
    async with async_playwright() as playwright:
        tasks = [run(playwright, account) for account in NEOACCOUNT_DATA.accounts]
        result = await asyncio.gather(*tasks)
        _report.append(result)

    _sleep_interval = 3600
    print(f'Work done, {_report} ')
    await random_sleep(_sleep_interval+200,_sleep_interval+1200)

if __name__ == "__main__":
    while True:
        asyncio.run(main())