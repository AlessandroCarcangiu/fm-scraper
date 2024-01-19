from bs4 import BeautifulSoup
from typing import Callable, List
from urllib.parse import urljoin
from fm_scraper.core import DateUtilities, StringUtilities, TypeRequest
from .base_filler import BaseFiller


class FMInsideFiller(BaseFiller):

    @staticmethod
    def _get_base_url() -> str:
        return "https://fminside.net/players"

    @classmethod
    def __query_request(cls, full_name: str) -> str:
        return cls._filter_request(
            url=cls._get_base_url(),
            filter_data={
                "[placeholder=Name]":full_name
            }
        )

    def check_and_fill(self) -> any:
        full_name = f"{self.item['first_name']} {self.item['last_name']}".lower().strip()
        response = self.__query_request(full_name)
        if response:
            soup = BeautifulSoup(response, self._parser)
            if soup:
                player_table = soup.find("div", id="player_table")
                if player_table:
                    items = player_table.find_all("b")
                    urls = [t.find("a").attrs['href'] for t in items
                            if StringUtilities.safe_equals(t.text, full_name, True, 0.80)]
                    for u in urls:
                        self.__analise_item(u)
        return self.item

    def __analise_item(self, url: str) -> None:
        # get player data and compare
        response = self._send_request(urljoin(self._get_base_url(), url))
        if response:
            # player info section
            player_info = BeautifulSoup(response, self._parser).find("div", id="player")
            if player_info:
                player_details = player_info.find_next("div", attrs={"class":"column"}).find_all("li")
                # compare name, birth of date and club (if applicable)
                funcs: List[Callable] = [self.__compare_name, self.__compare_birth_date]
                if all([f(player_details) for f in funcs]):
                    self.item["db_unique_id"] = self.__get_db_unique_id(player_details)

    # compare
    def __compare_name(self, items: list) -> bool:
        item = items[0]
        key = item.find_next("span")
        if key and key.text.strip().lower() == "name":
            name = StringUtilities.extract_safe_text(item.find_next("span", attrs={"value"}))
            return StringUtilities.safe_equals(
                name, f"{self.item['first_name']} {self.item['last_name']}",
                True, 0.90
            )
        return False

    def __compare_birth_date(self, items: list) -> bool:
        item = items[1]
        key = item.find_next("span")
        if key and key.text.strip().lower() == "age":
            age = int(StringUtilities.extract_safe_text(item.find_next("span", attrs={"value"})))
            if age and "date_of_birth" in self.item and self.item["date_of_birth"]:
                return age == DateUtilities.get_years_from_today(self.item["date_of_birth"])
        return False

    # setters
    @staticmethod
    def __get_db_unique_id(items: list) -> str:
        item = items[-1]
        key = item.find_next("span")
        if key and key.text.strip().lower() == "unique id":
            unique_db = StringUtilities.extract_safe_text(item.find_next("span", attrs={"value"}))
            return unique_db
