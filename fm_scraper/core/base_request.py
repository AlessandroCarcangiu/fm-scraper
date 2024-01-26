import os
import random
import requests
import time
from enum import Enum
from playwright.sync_api import sync_playwright
from typing import Tuple
from fm_scraper.browsers import WEBKIT_PATH
from fm_scraper.scrapers.settings import (
    MAX_RETRIES,
    MAX_WAIT_SECONDS
)


class TypeRequest(Enum):
    POST = 0
    GET = 1


class BaseRequest:

    __user_agent = ('Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) '
                    'Chrome/58.0.3029.110 Safari/537.3')
    _parser = "html.parser"

    @classmethod
    def __get_method(cls, type_request: TypeRequest) -> any:
        if type_request == TypeRequest.GET:
            return cls.__send_get_request
        if type_request == TypeRequest.POST:
            return cls.__send_post_request
        return None

    @classmethod
    def __get_playwright_browser(cls, p, **kwargs):
        return p.webkit.launch(executable_path=os.path.join(WEBKIT_PATH), **kwargs)

    @classmethod
    def _send_request(cls, url: str, type_request:TypeRequest = TypeRequest.GET, with_session: bool=False, data: dict = None) -> str | None:
        fun = cls.__get_method(type_request)
        count = 0
        content = None
        while count < MAX_RETRIES:
            status_code, content = fun(url, with_session, data)
            if status_code >= 300 and status_code != 404:
                temp_sec = random.randint(0, MAX_WAIT_SECONDS)
                count += 1
                time.sleep(temp_sec)
                continue
            return content
        return content

    @classmethod
    def _filter_request(cls, url: str, filter_data: dict) -> str | None:
        count = 0
        while count < MAX_RETRIES:
            with sync_playwright() as p:
                browser = cls.__get_playwright_browser(p)
                context = browser.new_context(user_agent=cls.__user_agent)
                page = context.new_page()
                response = page.goto(url, timeout=0)
                page.wait_for_load_state("load")
                page.locator('p[class=fc-button-label]').get_by_text("Consent", exact=True).click()
                for k,v in filter_data.items():
                    page.locator(k).fill(v)
                page.keyboard.press("Enter")
                time.sleep(1)
                content = page.content()
                context.close()
                browser.close()
            if response.status >= 300:
                count += 1
                time.sleep(random.randint(0, MAX_WAIT_SECONDS))
                continue
            return content

    @classmethod
    def __send_get_request(cls, url:str, with_session: bool = False, data: dict = None) -> Tuple[int, str]:
        if with_session:
            with sync_playwright() as p:
                browser = cls.__get_playwright_browser(p)
                context = browser.new_context(
                    user_agent=cls.__user_agent
                )
                page = context.new_page()
                response = page.goto(url, wait_until='load')
                content = page.content()
                browser.close()
                return response.status, content
        response = requests.get(url, headers={"User-Agent": cls.__user_agent, "Content-Type":"application/x-www-form-urlencoded; charset=UTF-8"}, data=data)
        return response.status_code, response.text

    @classmethod
    def __send_post_request(cls, url: str, with_session: bool = False, data: dict = None) -> tuple:
        if with_session:
            with sync_playwright() as p:
                browser = cls.__get_playwright_browser(p)
                context = browser.new_context(
                    user_agent=cls.__user_agent
                )
                page = context.new_page()
                response = page.request.post(url=url, data=data, headers={"User-Agent": cls.__user_agent})
                content = page.content()
                browser.close()
                return response.status, content
        response = requests.post(url, headers={"User-Agent": cls.__user_agent}, data=data)
        return response.status_code, response.text
