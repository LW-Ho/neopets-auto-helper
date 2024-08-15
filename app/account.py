import asyncio
import json
from playwright.async_api import Page, BrowserContext
from os.path import exists
from pathlib import Path
import urls.neopets_urls as NEOPETS_URLS

class NotLoggedInException(Exception):
    "Raised when we cannot confirm we've logged in successfully."
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
        await asyncio.sleep(5)

    async def login(self, context: BrowserContext, page: Page) -> None:
        """Login API.

        Raises
        ------
        RuntimeError
            If a login error occurs, RuntimeError will be raised.
        """
        try:
            await self._login_or_restore_cookie(context, page)
            return True
        except Exception as e:
            raise Exception(f"Login error {e}")
        
        return False
        
    async def _login_or_restore_cookie(self, context: BrowserContext, page: Page):
        '''
        登入帳號，如果Cookie 存在，就以Cookie 操作。
        '''
        _username_t = self._username if self._legacy else self._neopass_username
        cookie_path = f"sessions/{_username_t}.json"

        if exists(cookie_path):
            await context.add_cookies(json.loads(Path(cookie_path).read_text()))
            print("Loading cookie file.")
            await page.goto(NEOPETS_URLS.NEO_INVENTORY_R)
            await asyncio.sleep(5)

            if not await  self._confirm_manual_login(page):
                await self._login_account_portal(context, page)
                if await self._confirm_manual_login(page):
                    print("Login Success.")
                    await self._store_cookie(context, page)
                else:
                    raise NotLoggedInException
        else:
            await self._login_account_portal(context, page)
            if await self._confirm_manual_login(page):
                print("Login Success.")
                await self._store_cookie(context, page)
            else:
                raise NotLoggedInException
            
    async def _login_account_portal(self, context: BrowserContext, page: Page):
        if self._legacy:
            await self._login_account_legacy(context, page)
        else:
            await self._login_account_neopass(context, page)
            
    async def _login_account_neopass(self, context: BrowserContext, page: Page):
        '''
        2022加入的NeoPass 帳戶登入
        '''
        await page.goto(NEOPETS_URLS.NEO_NEOPASS_LOGIN)
        await asyncio.sleep(10)
        try:
            await page.locator("input[name=\"email\"]").click()
            await page.locator("input[name=\"email\"]").fill(self._username)
            await asyncio.sleep(2)
            await page.locator("input[name=\"password\"]").click()
            await page.locator("input[name=\"password\"]").fill(self._password)
            await asyncio.sleep(2)
            await page.get_by_role("button", name="Sign In").click()
        except:
            # cache with cookie.
            pass
        await asyncio.sleep(10)
        await page.goto("https://account.neopets.com/classic/login")
        await page.locator(f"text={self._neopass_username}").click()
        await page.get_by_role("button", name="Continue").click()
        await asyncio.sleep(10)

    async def _login_account_legacy(self, context: BrowserContext, page: Page):
        '''
        傳統的Neopets 帳戶登入
        '''
        await page.goto(NEOPETS_URLS.NEO_LOGIN)
        await asyncio.sleep(5)
        await page.locator("#loginUsername").click()
        await page.locator("#loginUsername").fill(self._username)
        await page.locator("#loginPassword").click()
        await page.locator("#loginPassword").fill(self._password)
        await page.get_by_role("button", name="Log In").click()
        await asyncio.sleep(10)

    async def _store_cookie(self, context: BrowserContext, page: Page):
        '''
        儲存Cookie
        '''
        cookies = await context.cookies()
        _username_t = self._username if self._legacy else self._neopass_username
        Path("sessions").mkdir(parents=True, exist_ok=True)
        Path(f"sessions/{_username_t}.json").write_text(json.dumps(cookies))
        print(f"Wrote cookies for account {_username_t}")
        
    async def _confirm_manual_login(self, page: Page) -> bool:
        '''
        確認是否登入中
        '''
        content = await page.content()
        if self._legacy:
            if f'userlookup.phtml?user={self._username}' in content:
                return True
            else:
                False
        else:
            if f'userlookup.phtml?user={self._neopass_username}' in content:
                return True
            else:
                False