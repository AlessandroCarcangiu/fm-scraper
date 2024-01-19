from abc import ABC, abstractmethod
from fm_scraper.core import BaseRequest


class BaseFiller(ABC, BaseRequest):

    def __init__(self, item: any) -> None:
        self.item = item

    @staticmethod
    @abstractmethod
    def _get_base_url() -> str:
        pass

    @staticmethod
    @abstractmethod
    def check_and_fill() -> any:
        pass
