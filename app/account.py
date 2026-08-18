import json
import os
from datetime import datetime
from random import randrange
from playwright.async_api import Page, BrowserContext
from os.path import exists
from pathlib import Path
import urls.neopets_urls as NEOPETS_URLS
from utility import random_sleep, web

# Cap the debug/ folder so failed-login artifacts (HTML + screenshot per dump)
# can't fill the disk over months of scheduled runs. Keep the newest N files;
# each incident writes 2 files, so 40 == ~20 most recent incidents. Override per
# container with `-e DEBUG_KEEP_FILES=...`.
DEBUG_KEEP_FILES = int(os.environ.get("DEBUG_KEEP_FILES", "40"))

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

    async def login(self, context: BrowserContext, page: Page) -> bool:
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

            # Short in-process backoff only. One run == one account then exit, so
            # spacing between attempts is the external scheduler's job; a long sleep
            # here just makes a failed run look frozen for minutes.
            await random_sleep(10, 30)
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
            await page.goto(NEOPETS_URLS.NEO_BANK, wait_until="domcontentloaded", timeout=60000)
            await random_sleep(5, 10)

            if not await  self._confirm_manual_login(page):
                self._remove_cookie()
                await self._login_account_portal(context, page)
                if await self._confirm_manual_login(page):
                    print(f"{_username_t} Login Success.")
                    await self._store_cookie(context, page)
                else:
                    await self._dump_debug(page, "login_confirm_fail")
                    raise NotLoggedInException("Raised when we cannot confirm we've logged in successfully.")
            print(f"{_username_t} Login Success using Cookie.")
        else:
            await self._login_account_portal(context, page)
            if await self._confirm_manual_login(page):
                print(f"{_username_t} Login Success.")
                await self._store_cookie(context, page)
            else:
                await self._dump_debug(page, "login_confirm_fail")
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
                await page.evaluate("""
                        Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
                    """)

                await page.mouse.move(randrange(1, 300), randrange(1, 300))
                # Avoid reChatcha v3 
                email_field_box = await page.locator("input[name=\"email\"]").bounding_box()
                if email_field_box:
                    await page.mouse.click(email_field_box['x'] + randrange(1, 100), email_field_box['y'] + randrange(1,30))
                    await page.locator("input[name=\"email\"]").type(self._username, delay=200)
                    
                await random_sleep(2, 5)
                await page.mouse.move(randrange(1, 300), randrange(1, 300))
                
                password_field_box = await page.locator("input[name=\"password\"]").bounding_box()
                if password_field_box:
                    await page.mouse.click(password_field_box['x'] + randrange(1, 100), password_field_box['y'] + randrange(1,30))
                    await page.locator("input[name=\"password\"]").type(self._password, delay=300)

                await random_sleep(2, 5)
                await page.keyboard.press('Tab')
                await random_sleep(1,2)
                await page.keyboard.press('Tab')
                await random_sleep(1,2)
                await page.keyboard.press('Tab')
                await random_sleep(1,2)
                await page.keyboard.press('Space')
                await random_sleep(3,5)
                await page.keyboard.press('Tab')
                await random_sleep(1,2)
                await page.keyboard.press('Tab')
                await random_sleep(1,2)
                await page.keyboard.press('Tab')
                await random_sleep(1,2)
                await page.keyboard.press('Tab')
                await random_sleep(1,2)
                await page.mouse.move(randrange(1, 300), randrange(1, 300))
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

        # ---- Account selection page (account.neopets.com/classic/login) ----
        # NeoPass lists the linked Neopets accounts here; the "Continue" button
        # stays DISABLED until one is selected. The old code blind-clicked it,
        # which just burns the 30s locator timeout when nothing got selected and
        # hides *why*. Instead: select the account, then wait for the button to
        # actually become enabled before clicking, and dump debug on failure.
        account = page.locator(f"text={self._neopass_username}").first
        try:
            await account.wait_for(state="visible", timeout=20000)
            await account.click(delay=200)
        except Exception:
            # Account name never rendered -> the email/password step upstream
            # almost certainly failed (reCAPTCHA / wrong credentials), or
            # NEOPASS_USERNAME doesn't match the displayed name.
            await self._dump_debug(page, "neopass_account_not_listed")
            raise NotLoggedInException(
                f"NeoPass account '{self._neopass_username}' not shown on the "
                f"selection page (url={page.url}). The email/password login "
                f"likely failed (reCAPTCHA) or NEOPASS_USERNAME is wrong."
            )

        continue_btn = page.get_by_role("button", name="Continue")
        try:
            await continue_btn.wait_for(state="visible", timeout=10000)
            # Wait for the selection to enable the button rather than clicking it
            # while disabled (which is what timed out before).
            await page.wait_for_function(
                """() => {
                    const b = [...document.querySelectorAll('button')]
                        .find(el => el.textContent.trim() === 'Continue');
                    return !!b && !b.disabled;
                }""",
                timeout=10000,
            )
        except Exception:
            await self._dump_debug(page, "neopass_continue_disabled")
            raise NotLoggedInException(
                "NeoPass 'Continue' stayed disabled — account selection didn't "
                f"register (url={page.url})."
            )

        await continue_btn.click(delay=200)
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

    async def _dump_debug(self, page: Page, label: str) -> None:
        '''
        Save the current page's HTML + a screenshot so we can see WHY login could
        not be confirmed (wrong password page, captcha/challenge, announcement,
        empty response, etc.). Artifacts land in debug/. Never raises.
        '''
        try:
            _username_t = self._username if self._legacy else self._neopass_username
            Path("debug").mkdir(parents=True, exist_ok=True)
            # Timestamp the filename so successive failures keep a short history
            # (instead of overwriting); _prune_debug() below bounds the total.
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            base = f"debug/{_username_t}_{label}_{ts}"
            html = await page.content()
            Path(f"{base}.html").write_text(html, encoding="utf-8")
            await page.screenshot(path=f"{base}.png", full_page=True)
            # Quick hint in the log without needing to open the files.
            markers = [m for m in ("password", "incorrect", "captcha", "recaptcha",
                                   "bg-pattern", "login") if m in html.lower()]
            print(f"[debug] url={page.url} len={len(html)} markers={markers} "
                  f"-> saved {base}.html / {base}.png")
            self._prune_debug()
        except Exception as e:
            print(f"[debug] dump failed: {e}")

    def _prune_debug(self) -> None:
        '''
        Keep debug/ bounded to the DEBUG_KEEP_FILES most recent files, deleting
        the oldest first. Runs after each dump so the newest artifacts survive.
        Never raises.
        '''
        try:
            files = [p for p in Path("debug").glob("*") if p.is_file()]
            if len(files) <= DEBUG_KEEP_FILES:
                return
            files.sort(key=lambda p: p.stat().st_mtime, reverse=True)
            stale = files[DEBUG_KEEP_FILES:]
            for p in stale:
                try:
                    p.unlink()
                except OSError:
                    pass
            print(f"[debug] pruned {len(stale)} old artifact(s), "
                  f"kept newest {DEBUG_KEEP_FILES}.")
        except Exception as e:
            print(f"[debug] prune failed: {e}")

    async def _confirm_manual_login(self, page: Page) -> bool:
        '''
        Check if logged in.
        '''
        await page.goto(NEOPETS_URLS.NEO_BANK, wait_until="domcontentloaded", timeout=60000)
        content = await page.content()
        if self._legacy:
            if f'userlookup.phtml?user={self._username}' in content:
                return True
        else:
            if f'userlookup.phtml?user={self._neopass_username}' in content:
                return True

        print('Not logging.')
        return False