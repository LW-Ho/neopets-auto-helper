import json
from random import randrange
from playwright.async_api import Page, BrowserContext
from os.path import exists
from pathlib import Path
import urls.neopets_urls as NEOPETS_URLS
from utility import random_sleep, web

class NotLoggedInException(Exception):
    pass

class Account:
    def __init__(
            self, 
            username, 
            password, 
            active_pet_name, 
            legacy: bool = True, 
            neopass_username: str = ""
    ) -> None:
        self._username = username
        self._password = password
        self._active_pet_name = active_pet_name
        self._legacy = legacy
        self._neopass_username = neopass_username
        self._cookie = {}

    async def logout(self, context: BrowserContext, page: Page) -> None:
        await page.goto(NEOPETS_URLS.NEO_LOGOUT_REQUEST)
        print(f'{self._username} logout...')
        await random_sleep(5, 10)

    async def login(self, context: BrowserContext, page: Page) -> None:
        """Login API.

        Raises
        ------
        RuntimeError
            If a login error occurs, RuntimeError will be raised.
        """
        count = 0
        while count < 3:
            try:
                await self._login_or_restore_cookie(context, page)
                return True
            except Exception as e:
                print(f"{self._username} Login error {e}")
                await self.logout(context, page)
            
            await random_sleep(10, 240)
            count += 1
        
        return False
        
    async def _login_or_restore_cookie(self, context: BrowserContext, page: Page):
        '''
        "Log in to the account. If cookies exist, use the cookies instead."
        '''
        _username_t = self._username if self._legacy else self._neopass_username
        cookie_path = f"sessions/{_username_t}.json"

        if exists(cookie_path):
            await context.add_cookies(json.loads(Path(cookie_path).read_text()))
            print(f"{_username_t} Loading cookie file.")
            await page.goto(NEOPETS_URLS.NEO_BANK, wait_until="load", timeout=60000)
            await random_sleep(5, 10)

            if not await  self._confirm_manual_login(page):
                self._remove_cookie()
                await self._login_account_portal(context, page)
                if await self._confirm_manual_login(page):
                    print(f"{_username_t} Login Success.")
                    await self._store_cookie(context, page)
                else:
                    raise NotLoggedInException("Raised when we cannot confirm we've logged in successfully.")
            print(f"{_username_t} Login Success using Cookie.")
        else:
            await self._login_account_portal(context, page)
            if await self._confirm_manual_login(page):
                print(f"{_username_t} Login Success.")
                await self._store_cookie(context, page)
            else:
                raise NotLoggedInException("Raised when we cannot confirm we've logged in successfully.")
            
    async def _login_account_portal(self, context: BrowserContext, page: Page):
        if self._legacy:
            await self._login_account_legacy(context, page)
        else:
            await self._login_account_neopass(context, page)
            
    async def _login_account_neopass(self, context: BrowserContext, page: Page):
        '''
        Login with the NeoPass account added in 2022.
        '''
        count = 0
        await page.goto(NEOPETS_URLS.NEO_NEOPASS_LOGIN)
        await random_sleep(10, 15)
        while count < 5:
            try:
                # Avoid reChatcha v3 
                email_field_box = await page.locator("input[name=\"email\"]").bounding_box()
                if email_field_box:
                    await page.mouse.click(email_field_box['x'] + randrange(1, 50), email_field_box['y'] + randrange(1,10))
                    await page.locator("input[name=\"email\"]").fill(self._username)
                    
                await random_sleep(2, 5)
                
                password_field_box = await page.locator("input[name=\"password\"]").bounding_box()
                if password_field_box:
                    await page.mouse.click(password_field_box['x'] + randrange(1, 50), password_field_box['y'] + randrange(1,10))
                    await page.locator("input[name=\"password\"]").fill(self._password)
                    
                await random_sleep(2, 5)
                await page.keyboard.press('Tab')
                await random_sleep(1,2)
                await page.keyboard.press('Tab')
                await random_sleep(1,2)
                await page.keyboard.press('Enter')

                await page.wait_for_load_state('networkidle')

            except Exception as e:
                print(f"{__name__}: {e}")
                pass
            await random_sleep(10, 15)
            await page.goto("https://account.neopets.com/classic/login")
            await random_sleep(10, 15)

            if NEOPETS_URLS.NEO_NEOPASS_LOGIN in page.url:
                count += 1
            else:
                break

        account_field_box = await page.locator(f"text={self._neopass_username}").bounding_box()
        if account_field_box:
            await page.mouse.click(account_field_box['x'] + randrange(1, 50), account_field_box['y'] + randrange(1,10))

        await page.get_by_role("button", name="Continue").click()
        await random_sleep(10, 15)

    async def _login_account_legacy(self, context: BrowserContext, page: Page):
        '''
        Login with the traditional Neopets account.
        '''
        await page.goto(NEOPETS_URLS.NEO_LOGIN)
        retry = 0
        while retry < 5:
            await random_sleep(30, 40)
            payload = {"destination": "", "username": self._username, "password": self._password, }
            rep = await web.post(payload, NEOPETS_URLS.NEO_LOGIN_REQUEST, context, page, NEOPETS_URLS.NEO_LOGIN)

            if web.check_for_announcement(rep):
                retry += 1
                print(f"{__name__} retry...")
            else:
                break
        await random_sleep(5, 10)

    async def _store_cookie(self, context: BrowserContext, page: Page):
        '''
        Store cookie
        '''
        cookies = await context.cookies()
        _username_t = self._username if self._legacy else self._neopass_username
        Path("sessions").mkdir(parents=True, exist_ok=True)
        Path(f"sessions/{_username_t}.json").write_text(json.dumps(cookies))
        print(f"Wrote cookies for account {_username_t}")

    def _remove_cookie(self):
        _username_t = self._username if self._legacy else self._neopass_username
        file_path = Path(f"sessions/{_username_t}.json")

        try:
            file_path.unlink()
            print(f"File {file_path} has been removed successfully.")
        except FileNotFoundError:
            print(f"File {file_path} not found.")
        except PermissionError:
            print(f"Permission denied to remove {file_path}.")
        except Exception as e:
            print(f"Error occurred: {e}")

    async def _confirm_manual_login(self, page: Page) -> bool:
        '''
        Check if logged in.
        '''
        await page.goto(NEOPETS_URLS.NEO_BANK, wait_until="load", timeout=60000)
        content = await page.content()
        if self._legacy:
            if f'userlookup.phtml?user={self._username}' in content:
                return True
        else:
            if f'userlookup.phtml?user={self._neopass_username}' in content:
                return True

        print('Not logging.')
        return False