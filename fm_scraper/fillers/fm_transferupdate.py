import Levenshtein
from bs4 import BeautifulSoup
from dateutil import parser
from typing import Callable, List
from fm_scraper.core import StringUtilities
from .base_filler import BaseFiller


class FMTransferUpdateFiller(BaseFiller):

    @staticmethod
    def _get_base_url() -> str:
        return "https://fmtransferupdate.com/"

    @classmethod
    def __query_request(cls, full_name: str, person_type: str) -> str:
        typology = "players" if person_type == "player" else "staff"
        return cls._send_request(
            url=f"{cls._get_base_url()}{typology}?filter_name={full_name}",
            with_session=True
        )

    def check_and_fill(self) -> any:
        full_name_1 = f"{self.item['first_name']}+{self.item['last_name']}".lower().strip()
        full_name_2 = f"{self.item['first_name']} {self.item['last_name']}".lower().strip()
        response = self.__query_request(full_name_1, self.item["type"])
        if response:
            soup = BeautifulSoup(response, "html.parser")
            if soup:
                content_panel = soup.find(id="fmtu-content-pane")
                if content_panel:
                    items = content_panel.find_all(lambda tag:
                                                   tag.name == "a"
                                                   and Levenshtein.ratio(tag.text.strip().lower(), full_name_2) > 0.85
                                                   and 'href' in tag.attrs
                                                   and any(i in tag.attrs['href'] for i in ['players', 'staff']))
                    for item in items:
                        url = item.attrs['href']
                        self.__analise_item(url)
        return self.item

    def __analise_item(self, url: str) -> None:
        # get player/staff data and compare
        response = self._send_request(url, with_session=True)
        if response:
            item_soup = BeautifulSoup(response, "html.parser").find("div", itemscope=True)
            # compare name, birth of date and club (if applicable)
            funcs: List[Callable] = [self.__compare_name, self.__compare_birth_date]
            if all([f(item_soup) for f in funcs]):
                self.item["db_unique_id"] = self.__get_db_unique_id(url)
                self.item["citizenship"] = self.__get_citizenships(item_soup)
                if self.item.get("type") == "staff":
                    self.item["job"] = self.__get_job(item_soup)

    # compare
    def __compare_name(self, soup) -> bool:
        name = soup.find(itemprop="name")
        if not name:
            return False
        return StringUtilities.safe_equals(
            name.text,
            f"{self.item['first_name']} {self.item['last_name']}",
            True,
            0.92
        )

    def __compare_birth_date(self, soup) -> bool:
        d = soup.find(itemprop="birthDate")
        birth_date = parser.parse(d.text.strip()).strftime("%d/%m/%Y") if d else None
        if birth_date and "date_of_birth" in self.item:
            return birth_date == self.item["date_of_birth"]
        if birth_date and "date_of_birth" not in self.item:
            self.item["date_of_birth"] = birth_date
        return True

    # getters
    @staticmethod
    def __get_db_unique_id(url: str) -> str:
        return url.split("/")[-1].split("-")[0]

    @staticmethod
    def __get_citizenships(soup) -> str:
        flag = soup.select_one('a[href*=nation]').select_one('img')
        if not flag:
            return ""
        return flag['alt'].lower()

    @staticmethod
    def __get_job(soup) -> str | None:
        job_span = soup.find('span', attrs={"itemprop":"knowsAbout"})
        if job_span:
            job = job_span.text.strip().lower()
            if job == "assistant manager":
                job += " first team"
            return job
        return None
