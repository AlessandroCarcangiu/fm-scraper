from abc import ABC
from bs4 import Tag
from fm_scraper.core import BaseRequest
from .settings import DEBUG


class BaseScraper(ABC, BaseRequest):

    @staticmethod
    def _send_message(text: str, queue) -> None:
        if DEBUG:
            print(text)
        if queue:
            queue.put(text)
        if not queue:
            print("porcoddio ladro")

    @staticmethod
    def _safe_extract_text(tag: Tag) -> str | None:
        if tag and tag.text:
            return tag.text.strip().lower()

    @staticmethod
    def _safe_to_float(value: str) -> float | None:
        if value:
            return float(value.strip().replace(",","."))
