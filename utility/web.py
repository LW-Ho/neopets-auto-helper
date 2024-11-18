
from typing import Optional
from urllib.parse import quote_plus, urlencode
from playwright.async_api import APIResponse
from playwright.async_api import Page, BrowserContext
import urls.neopets_urls as NEOPETS_URLS
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36 Edg/127.0.0.0"

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
