import asyncio
import logging
import json
from playwright.async_api import Page, BrowserContext
from os.path import exists
from pathlib import Path
import urls.neopets_urls as NEOPETS_URLS

_LOGGER = logging.getLogger(__name__)

class NotLoggedInException(Exception):
    "Raised when we cannot confirm we've logged in successfully."
    pass

class Account:
    def __init__(self, username, password, active_pet_name):
        self._username = username
        self._password = password
        self._active_pet_name = active_pet_name
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
        except Exception as e:
            raise Exception(f"Login error {e}")
        
    async def _login_or_restore_cookie(self, context: BrowserContext, page: Page):
        '''
        登入帳號，如果Cookie 存在，就以Cookie 操作。
        '''
        cookie_path = f"sessions/{self._username}.json"

        if exists(cookie_path):
            await context.add_cookies(json.loads(Path(cookie_path).read_text()))
            print("Loading cookie file.")
            await page.goto(NEOPETS_URLS.NEO_INVENTORY_R)
            await asyncio.sleep(5)

            if not await  self._confirm_manual_login(page):
                await self._login_account_legacy(context, page)
                if await self._confirm_manual_login(page):
                    print("Login Success.")
                    await self._store_cookie(context, page)
                else:
                    raise NotLoggedInException
        else:
            await self._login_account_legacy(context, page)
            if await self._confirm_manual_login(page):
                print("Login Success.")
                await self._store_cookie(context, page)
            else:
                raise NotLoggedInException
            
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
        Path("sessions").mkdir(parents=True, exist_ok=True)
        Path(f"sessions/{self._username}.json").write_text(json.dumps(cookies))
        print(f"Wrote cookies for account {self._username}")
        
    async def _confirm_manual_login(self, page: Page) -> bool:
        '''
        確認是否登入中
        '''
        content = await page.content()
        if f'userlookup.phtml?user={self._username}' in content:
            return True
        else:
            False