
import asyncio
from typing import Optional
from urllib.parse import quote_plus, urlencode
from playwright.async_api import APIResponse
from playwright.async_api import Page, BrowserContext
from playwright.async_api import TimeoutError as PlaywrightTimeoutError
import urls.neopets_urls as NEOPETS_URLS
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36 Edg/127.0.0.0"

# --- Tolerant navigation -------------------------------------------------------
# Neopets pages hang on ad/tracker/image subresources, so the old
# `page.goto(url, wait_until="load")` sat until the 120s timeout and then RAISED,
# killing the task BEFORE its real work (a page.request POST, or a scrape of the
# already-parsed initial HTML) could run. `goto()` below navigates with
# wait_until="domcontentloaded" (inline scripts that set getCK/_ref_ck tokens
# still execute; only the load-event subresources that stall are skipped) and
# never raises on a navigation timeout. A nav-level semaphore caps how many pages
# render at once, since all dailies/training run concurrently in one headed
# Camoufox instance. NOTE: this is deliberately NOT used in the login flow
# (app/account.py) so NeoPass/reCAPTCHA rendering is never weakened.

NAV_CONCURRENCY = 5
_NAV_SEMAPHORE: Optional[asyncio.Semaphore] = None

def _nav_semaphore() -> asyncio.Semaphore:
    # Created lazily inside the running loop so it binds to the correct loop.
    global _NAV_SEMAPHORE
    if _NAV_SEMAPHORE is None:
        _NAV_SEMAPHORE = asyncio.Semaphore(NAV_CONCURRENCY)
    return _NAV_SEMAPHORE

async def goto(page: Page, url: str, *, timeout: int = 45000, ready_selector: Optional[str] = None) -> bool:
    """Navigate tolerantly and report whether the page is usable.

    - wait_until="domcontentloaded": HTML parsed + inline scripts run, but we do
      NOT wait for ads/trackers/images (the source of the hangs/timeouts).
    - Only the load-event TIMEOUT is swallowed (not raised): that is the ad-hang
      case where the DOM is already present and we want to proceed. A hard
      navigation failure (DNS/connection/SSL) is NOT swallowed — it propagates so
      the caller's own try/except records the task as failed instead of running
      its POST and falsely reporting success.
    - If ready_selector is given, we confirm THAT element exists. This both
      verifies the correct page loaded (guards against scraping a stale DOM on a
      reused page) and is the success signal for DOM-scraping callers.

    Pure-POST callers can ignore the return value; the POST runs regardless.
    """
    async with _nav_semaphore():
        try:
            await page.goto(url, wait_until="domcontentloaded", timeout=timeout)
        except PlaywrightTimeoutError:
            pass

        if ready_selector:
            try:
                await page.wait_for_selector(ready_selector, state="attached", timeout=timeout)
                return True
            except Exception:
                return False

        try:
            state = await page.evaluate("document.readyState")
            if state in ("interactive", "complete"):
                return True
        except Exception:
            pass
        try:
            content = await page.content()
            return len(content) > 500 and "</html>" in content.lower()
        except Exception:
            return False

def check_for_announcement(response):
    if 'class="bg-pattern"' in response:
        print("-----------Important Announcement!------------")
        return True

async def get(url: str, context: BrowserContext, page: Page, referer: Optional[str] = None) -> str:
    headers = {
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9",
            "Accept-Encoding": "gzip, deflate",
            "Accept-Language": "en-US,en;q=0.9",
            # "Cache-Control": "max-age=0", #Cache control doesn't exist for refresh? or going to quickstock
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Host": "www.neopets.com",
            'Upgrade-Insecure-Requests': "1",
            'User-Agent': UA,
            "Sec-Fetch-Site": "same-origin",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-User": "?1",
            "Sec-Fetch-Dest": "document",
            }
    if referer:
        headers['Referer'] = referer

    response: APIResponse = await page.request.get(
        url=url,
        headers=headers
    )

    r = await response.text()

    return r

async def post(payload: dict, url: str, context: BrowserContext, page: Page, referer: str) -> str:
    headers = {
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9",
            "Accept-Encoding": "gzip, deflate",
            "Accept-Language": "en-US,en;q=0.9",
            #"Cache-Control": "max-age=0", #Cache control doesn't exist for refresh? or going to quickstock
            "Connection": "keep-alive",
            "Host": "www.neopets.com",
            'Upgrade-Insecure-Requests': "1",
            'User-Agent': UA,
            }

    s = urlencode(payload, quote_via=quote_plus)
    headers['Content-Length'] = str(len(s))
    headers['Content-Type'] = "application/x-www-form-urlencoded"
    headers["Origin"] = NEOPETS_URLS.NEO_HOMEPAGE
    headers['Referer'] = referer

    response: APIResponse = await page.request.post(
        url=url,
        form=payload,
        headers=headers
    )

    r = await response.text()

    return r

async def post_form_data(payload: dict, url: str, context: BrowserContext, page: Page, referer: str) -> str:
    headers = {
            "Accept": "*/*",
            "Accept-Encoding": "gzip, deflate, br, zstd",
            "Accept-Language": "en-US,en;q=0.9,zh-TW;q=0.8,zh;q=0.7",
            #"Cache-Control": "max-age=0", #Cache control doesn't exist for refresh? or going to quickstock
            "Connection": "keep-alive",
            "Host": "www.neopets.com",
            'Upgrade-Insecure-Requests': "1",
            'User-Agent': UA,
            "Sec-Ch-Ua": '"Not)A;Brand";v="99", "Microsoft Edge";v="127", "Chromium";v="127"',
            "Sec-Ch-Ua-Mobile": "?0",
            "Sec-Ch-Ua-Platform": "Windows",
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "same-origin",
            'x-requested-with': 'XMLHttpRequest'
            }

    s = urlencode(payload, quote_via=quote_plus)
    headers['Content-Length'] = str(len(s))
    # headers['Content-Type'] = "application/x-www-form-urlencoded"
    headers["Origin"] = NEOPETS_URLS.NEO_HOMEPAGE
    headers['Referer'] = referer

    response: APIResponse = await page.request.post(
        url=url,
        multipart=payload,
        headers=headers
    )

    r = await response.text()

    return r

async def post_json(payload: dict, url: str, context: BrowserContext, page: Page, referer: str) -> str:
    headers = {
            "Accept": "*/*",
            "Accept-Encoding": "gzip, deflate, br, zstd",
            "Accept-Language": "en-US,en;q=0.9,zh-TW;q=0.8,zh;q=0.7",
            #"Cache-Control": "max-age=0", #Cache control doesn't exist for refresh? or going to quickstock
            "Connection": "keep-alive",
            "Host": "www.neopets.com",
            'Upgrade-Insecure-Requests': "1",
            'User-Agent': UA,
            "Sec-Ch-Ua": '"Not)A;Brand";v="99", "Microsoft Edge";v="127", "Chromium";v="127"',
            "Sec-Ch-Ua-Mobile": "?0",
            "Sec-Ch-Ua-Platform": "Windows",
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "same-origin",
            'x-requested-with': 'XMLHttpRequest'
            }

    # s = urlencode(payload, quote_via=quote_plus)
    # headers['Content-Length'] = str(len(s))
    headers["Origin"] = NEOPETS_URLS.NEO_HOMEPAGE
    headers['Referer'] = referer

    response: APIResponse = await page.request.post(
        url=url,
        data=payload,
        headers=headers
    )

    r = await response.text()

    return r
