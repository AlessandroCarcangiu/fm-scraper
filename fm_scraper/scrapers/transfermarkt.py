import Levenshtein
import pandas as pd
import random
import re
from bs4 import BeautifulSoup, Tag
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
from datetime import datetime
from functools import partial
from urllib.parse import urljoin, urlparse
from fm_scraper.fillers import FMInsideFiller, FMTransferUpdateFiller
from .base_scraper import BaseScraper
from .settings import MAX_THREAD_WORKERS, NUM_PROCESSORS


class TransfermarktScraper(BaseScraper):

    __base_url = "https://www.transfermarkt.com"
    __format_date = "%b %d, %Y"
    __player_headers = {
        #"place of birth": "city",
        "citizenship": "citizenship"
    }
    __player_positions = {
        'goalkeeper': 'goalkeeper',
        "centre-back": 'defender_central',
        "right-back": 'defender_right',
        "left-back": 'defender_left',
        "defensive midfield": "defensive_midfielder",
        "central midfield": "midfielder_central",
        "left midfield": "midfielder_left",
        "right midfield": "midfielder_right",
        "attacking midfield": "attacking_midfielder_central",
        "left winger": "attacking_midfielder_left",
        "right winger": "attacking_midfielder_right",
        "centre-forward": "striker",
        "second-striker": "striker",
    }
    __staff_job = ['chairperson', 'owner', 'managing director', 'director', 'manager', 'head of youth development',
                   'assistant manager', 'coach', 'gk coach', 'fitness coach', 'set piece coach',
                   'head performance analyst', 'performance analyst', 'director of football',
                   'technical director', 'chief scout', 'scout', 'recruitment analyst', 'loan manager', 'head physio',
                   'physio', 'head of sports science', 'sports scientist', 'chief doctor', 'doctor',
                   'manager reserve team', 'manager third team', 'manager u23 team', 'assistant manager reserve team',
                   'coach reserve team', 'gk coach reserve team', 'fitness coach reserve team',
                   'performance analyst reserve team', 'physio reserve team', 'sports scientist reserve team',
                   'doctor reserve team', 'assistant manager u23 team', 'coach u23 team', 'gk coach u23 team',
                   'fitness coach u23 team', 'performance analyst u23 team', 'physio u23 team',
                   'sports scientist u23 team', 'doctor u23 team', 'manager u22 team', 'assistant manager u22 team',
                   'coach u22 team', 'gk coach u22 team', 'fitness coach u22 team', 'performance analyst u22 team',
                   'physio u22 team', 'sports scientist u22 team', 'doctor u22 team', 'manager u21 team',
                   'assistant manager u21 team', 'coach u21 team', 'gk coach u21 team', 'fitness coach u21 team',
                   'performance analyst u21 team', 'physio u21 team', 'sports scientist u21 team', 'doctor u21 team',
                   'manager u20 team', 'assistant manager u20 team', 'coach u20 team', 'gk coach u20 team',
                   'fitness coach u20 team', 'performance analyst u20 team', 'physio u20 team', 'sports scientist u20 team',
                   'doctor u20 team', 'manager u19 team', 'assistant manager u19 team', 'coach u19 team',
                   'gk coach u19 team', 'fitness coach u19 team', 'performance analyst u19 team', 'physio u19 team',
                   'sports scientist u19 team', 'doctor u19 team', 'manager u18 team', 'assistant manager u18 team',
                   'coach u18 team', 'gk coach u18 team', 'fitness coach u18 team', 'performance analyst u18 team',
                   'physio u18 team', 'sports scientist u18 team', 'doctor u18 team', 'coach youth teams']

    @classmethod
    def _send_get_request(cls, url: str, *args, **kwargs) -> str | None:
        if not "https" in url:
            url = urljoin(cls.__base_url, url)
        parsed_url = urlparse(url)
        if not parsed_url.netloc == "www.transfermarkt.com":
            raise Exception(f"Please, give a correct url from transfermarkt english version")
        return super()._send_request(url, *args, **kwargs)

    @classmethod
    def extract_division(cls, division_url: str, **kwargs) -> pd.DataFrame:
        """
        extract the squad of all teams of the specified division.
        :param division_url: this url must be part of the domain transfermarkt.com and concern a division
        :return:
        """
        queue = None if "queue" not in kwargs else kwargs["queue"]
        soup = BeautifulSoup(cls._send_get_request(division_url), cls._parser)

        data = None
        division_table = soup.find("div", attrs={"class":"grid-view"})
        if division_table:
            team_urls = list()
            for row in division_table.find_all("td",attrs={"class":"hauptlink no-border-links"}):
                team_urls.append(row.find_next("a").get("href"))
            if team_urls:
                # return pd.concat([cls.extract_team(t) for t in team_urls])
                worker = partial(cls.extract_team, queue=queue)
                with ProcessPoolExecutor(max_workers=NUM_PROCESSORS) as executor:
                    data = list(executor.map(worker, team_urls))

        cls._send_message(f"\n{division_url} completed!", queue)
        if data:
            return pd.concat(data, axis=0)
        return pd.DataFrame()

    @classmethod
    def extract_team(cls, team_url: str, **kwargs) -> pd.DataFrame:
        """
        extract players and staff of the specified team.
        :param team_url: the url must be part of the domain transfermarkt.com and concern a team.
        :return:
        """
        queue = None if "queue" not in kwargs else kwargs["queue"]
        soup = BeautifulSoup(cls._send_get_request(team_url), cls._parser)
        club_name = soup.find("h1", attrs={"class":"data-header__headline-wrapper data-header__headline-wrapper--oswald"})
        dfs = list()
        # extract squad
        dfs.append(cls.__extract_squad(soup, queue=queue))
        # extract staff
        match = re.search(r'\d+', team_url)
        club_tfm_id = match.group() if match else None
        club_name_tfm = team_url.split("/")[3]
        if club_tfm_id and club_name_tfm:
            dfs.append(cls.__extract_staff(club_name_tfm, club_tfm_id, queue=queue))
        cls._send_message(f"\n\n{club_name.text.strip()} completed!\n", queue)
        return pd.concat(dfs) if dfs else pd.DataFrame()

    @classmethod
    def __extract_staff(cls, club_name:str, club_id: str, **kwargs) -> pd.DataFrame:
        queue = None if "queue" not in kwargs else kwargs["queue"]
        soup = BeautifulSoup(cls._send_get_request(f"{club_name}/mitarbeiter/verein/{club_id}"), cls._parser)
        if not soup:
            return pd.DataFrame()
        staff_urls = list()
        staff_data = soup.find("div", attrs={"class":"large-8 columns"})
        for box in staff_data.find_all("tbody"):
            staff_urls += [td.find("a").get("href") for td in box.find_all("td",attrs={"class":"hauptlink"})]
        with ThreadPoolExecutor(max_workers=MAX_THREAD_WORKERS) as executor:
            dfs = list(executor.map(lambda url: cls.extract_person(url, queue=queue), staff_urls))
        return pd.concat(dfs) if dfs else pd.DataFrame()

    @classmethod
    def __extract_squad(cls, soup: BeautifulSoup, **kwargs) -> pd.DataFrame:
        queue = None if "queue" not in kwargs else kwargs["queue"]
        roster_data = soup.find("table", attrs={"class":"items"})
        if not roster_data:
            return pd.DataFrame()
        player_urls = [r.find("a",attrs={"title": None}).get("href") for r in roster_data.find("tbody").find_all("tr", recursive=False)]
        with ThreadPoolExecutor(max_workers=MAX_THREAD_WORKERS) as executor:
            dfs = list(executor.map(lambda url: cls.extract_person(url, queue=queue), player_urls))
            return pd.concat(dfs) if dfs else pd.DataFrame()

    @classmethod
    def extract_person(cls, person_url: str, **kwargs) -> pd.DataFrame:
        """
        extract the info of the specified person.
        :param person_url: this url must be part of the domain transfermarkt.com and concern a person
        :return:
        """
        queue = None if "queue" not in kwargs else kwargs["queue"]
        soup = BeautifulSoup(cls._send_get_request(person_url), cls._parser)
        regex = re.compile('.*Player data.*')
        player_data = soup.find("h2", string=regex)
        df = cls.__extract_player(soup) if player_data else cls.__extract_non_player(soup)
        message = f"\n{df.loc[0]['first_name']} {df.loc[0]['last_name']} ({df.loc[0]['type']}) completed!" if not df.empty else f"\nError on scraping this person {person_url}"
        cls._send_message(message, queue)
        return df

    @classmethod
    def __extract_non_player(cls, soup: Tag) -> pd.DataFrame:
        data = {
            "type": "staff"
        }
        # get name
        header_name = soup.find("div", attrs={"class": "data-header__headline-container"})
        data["last_name"] = cls._safe_extract_text(header_name.find("strong"))
        data["first_name"] = cls._safe_extract_text(header_name).split(data["last_name"])[0].strip()
        # get data from header info
        club_span = soup.find("span", attrs={"itemprop":"affiliation"})
        if club_span:
            tags_a = club_span.find_all("a")
            if tags_a:
                current_club = tags_a[-1].get("title")
                if current_club:
                    current_club.strip()
            else:
                current_club = cls._safe_extract_text(club_span)
            data["club"] = current_club
        current_job = cls._safe_extract_text(club_span.find_next("span"))
        if current_job:
            if "Last position:" in current_job:
                current_job = cls._safe_extract_text(club_span.find_next("span", attrs={"class":"dataValue"}))
            lev_values = [
                Levenshtein.ratio(current_job, a) for a in cls.__staff_job
            ]
            data["job"] = cls.__staff_job[max(enumerate(lev_values), key=lambda x: x[1])[0]]
        # get data from personal details
        personal_details = soup.find("table", attrs={"class":"auflistung"})
        if personal_details:
            for d in personal_details.find_all("tr"):
                key = cls._safe_extract_text(d.find("th"))
                value = cls._safe_extract_text(d.find("td"))
                if key in cls.__player_headers:
                    data[cls.__player_headers[key]] = value
                if "date of birth" in key:
                    data["date_of_birth"] = datetime.strptime(value.split("(")[0].strip(), cls.__format_date).strftime("%d/%m/%Y")
        data = FMTransferUpdateFiller(data).check_and_fill()
        return pd.DataFrame(data, index=[0]) if data else pd.DataFrame()

    @classmethod
    def __extract_player(cls, soup: Tag) -> pd.DataFrame:
        data = {
            "entity": "Person",
            "type": "player"
        }
        # get data from header info
        header_data = soup.find("header", attrs={"class":"data-header"})
        wrapper_number_name = header_data.find('h1', attrs={"class": "data-header__headline-wrapper"})
        data["squad_number"] = cls._safe_extract_text(wrapper_number_name.find('span', attrs={"class": "data-header__shirt-number"}))
        player_name = re.sub(r'#\d+', '',cls._safe_extract_text(wrapper_number_name)).strip()
        data["last_name"] = cls._safe_extract_text(wrapper_number_name.find("strong"))
        data["first_name"] = player_name.split(data["last_name"])[0].strip()
        data["date_of_birth"] = datetime.strptime(
            cls._safe_extract_text(header_data.find('span', attrs={"itemprop": "birthDate"})).split("(")[0].strip(),
            cls.__format_date
        ).strftime("%d/%m/%Y")
        # height
        height_span = header_data.find('span', attrs={"itemprop": "height"})
        if height_span:
            data["height"] = int(cls._safe_to_float(cls._safe_extract_text(height_span)[:-2])*100)
        # get player data
        regex = re.compile('.*info-table info-table--right-space.*')
        player_data = soup.find("div", attrs={"class":regex})
        if player_data:
            for row in player_data.find_all('span', attrs={"class":'info-table__content--regular'}):
                key = cls._safe_extract_text(row).rstrip(':')
                if key:
                    value = cls._safe_extract_text(row.find_next('span'))
                    if key in cls.__player_headers:
                        data[cls.__player_headers[key]] = value
                    # foot
                    if key == "foot":
                        if value in ["left", "both"]:
                            data["left_foot"] = 20
                        if value in ["right", "both"]:
                            data["right_foot"] = 20
                    # current club
                    if key == "current club":
                        on_loan_from = player_data.find('span', string="On loan from")
                        data["job"] = "player"
                        if not on_loan_from:
                            tags_a = row.find_next('span').find_all("a")
                            if tags_a:
                                value = tags_a[-1].get("title").strip()
                            data["club"] = value
                            continue
                        data["club"] = cls._safe_extract_text(on_loan_from.find_next('span'))
                        data["loan_to"] = value
                        if "date_joined" in data:
                            data["loan_start"] = data.pop["joined"]
                        if "contract_expires" in data:
                            data["loan_end"] = data.pop["contract_expires"]
                        contract_expires = player_data.find('span', string="Contract there expires")
                        if contract_expires:
                            data["contract_expires"] = datetime.strptime(
                                cls._safe_extract_text(contract_expires.find_next("span")),
                                cls.__format_date
                            ).strftime("%d/%m/%Y")
                    # joined and contract expires
                    if key == "joined" and len(value) > 1:
                        data["date_joined"] = datetime.strptime(value, cls.__format_date).strftime("%d/%m/%Y")
                    if key == "contract expires" and len(value) > 1:
                        try:
                            data["contract_expires"] = datetime.strptime(value, cls.__format_date).strftime("%d/%m/%Y")
                        except Exception as e:
                            print(value)
                            raise e
        # position data
        position_data = soup.find("div", attrs={"class":"detail-position"})
        if position_data:
            divs = {"Main position:":True, "Other position:":False}
            for d,is_main in divs.items():
                pos_box = position_data.find("dt", string=d)
                if pos_box:
                    p = pos_box.parent.find_all("dd")
                    for i in p:
                        cls.__set_player_position(data, cls._safe_extract_text(i), is_main)
        data = FMInsideFiller(data).check_and_fill()
        return pd.DataFrame(data, index=[0])

    @classmethod
    def __set_player_position(cls, player_data:dict, position:str, is_main:bool=True) -> None:
        if position in cls.__player_positions:
            player_data[cls.__player_positions[position]] = 20 if is_main else random.randint(10,20)
