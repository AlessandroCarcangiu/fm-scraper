import dateparser
import pandas as pd
import random
from bs4 import BeautifulSoup, Tag
from functools import partial
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
from urllib.parse import urlparse
from fm_scraper.fillers import FMInsideFiller, FMTransferUpdateFiller
from .settings import MAX_THREAD_WORKERS, NUM_PROCESSORS
from .base_scraper import BaseScraper


class TuttocampoScraper(BaseScraper):

    __person_attributes = {
        "cognome": "last_name",
        "nome": "first_name",
        "numero di maglia": "squad_number",
    }

    __parser = "html.parser"

    __positions = {
        "portiere": "goalkeeper",
        "difensore": ["defender_left", "defender_central","defender_right"],
        "centrocampista": ["defensive_midfielder", "wing_back_left", "wing_back_right",
                           "midfielder_left", "midfielder_central", "midfielder_right"],
        "attaccante": ["attacking_midfielder_left", "attacking_midfielder_central",
                      "attacking_midfielder_right", "striker"],
    }

    __staff_job = {
        "presidente": "chairperson",
        "proprietario": "owner",
        "vice presidente": "director",
        "allenatore": "manager first team",
        "direttore sportivo": "director of football",
        "preparatore portieri": "gk coach first team",
        "preparatore atletico": "fitness coach first team",
        "dirigente": "director",
        "fisioterapista": "physio first team"
    }

    @classmethod
    def _send_request(cls, url: str, *args, **kwargs) -> str | None:
        parsed_url = urlparse(url)
        if not parsed_url.netloc == "www.tuttocampo.it":
            raise Exception(f"Please, give a correct url from tuttocampo italian version")
        return super()._send_request(url, *args, **kwargs)

    @classmethod
    def extract_division(cls, division_url: str, **kwargs) -> pd.DataFrame:
        """
        extract the squad of all teams of the specified division.
        :param division_url: this url must be part of the domain tuttocampo.it and concern a division
        :return:
        """
        queue = None if "queue" not in kwargs else kwargs["queue"]

        soup = BeautifulSoup(cls._send_request(url=division_url, with_session=True), cls.__parser)
        table = soup.find("div", id="last_match_ranking")

        team_urls = list()
        if table:
            rows = table.find_all("td", attrs={"class":"team"})
            for r in rows:
                a = r.find("a")
                team_urls.append(a.get("href"))

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
        :param team_url: the url must be part of the domain tuttocampo.it and concern a team.
        :return:
        """
        queue = None if "queue" not in kwargs else kwargs["queue"]

        soup = BeautifulSoup(cls._send_request(team_url.replace("Scheda", "Rosa"), with_session=True), cls.__parser)
        club_name = soup.find("h1", attrs={"class": "team", "itemprop": "name"})
        # get players and staff data
        df_staff = cls.__extract_staff(team_url, queue=queue)
        df_players = cls.__extract_squad(team_url, queue=queue)
        cls._send_message(f"\n\n{club_name.text} completed!\n",queue)
        return pd.concat([df_staff, df_players])

    @classmethod
    def __extract_staff(cls, team_url: str, **kwargs) -> pd.DataFrame:
        queue = None if "queue" not in kwargs else kwargs["queue"]
        staff_url = team_url
        if "Scheda" in team_url:
            staff_url = staff_url.replace("Scheda", "Staff")
        if not "Staff" in staff_url:
            staff_url += "/Staff" if not team_url[-1]=="/" else "Staff"
        soup = BeautifulSoup(cls._send_request(staff_url, with_session=True),
                             cls.__parser)
        staff_table = soup.find("div", id="team_staff")
        if not staff_table:
            return pd.DataFrame()
        staff_table = staff_table.findNext("tbody")
        staff_urls = list()
        for row in staff_table.find_all('tr'):
            if row:
                td = row.find_all('td')
                if td:
                    a = td[-1].find('a')
                    if a and len(a.text)>0:
                        staff_urls.append(a.get('href'))
        with ThreadPoolExecutor(max_workers=MAX_THREAD_WORKERS) as executor:
            staff_dfs = list(executor.map(lambda url: cls.extract_person(url, queue=queue), staff_urls))
        return pd.concat(staff_dfs, axis=0) if staff_dfs else pd.DataFrame()

    @classmethod
    def __extract_squad(cls, team_url: str, **kwargs):
        queue = None if "queue" not in kwargs else kwargs["queue"]
        squad_url = team_url
        if "Scheda" in team_url:
            squad_url = squad_url.replace("Scheda", "Rosa")
        if not "Rosa" in squad_url:
            squad_url += "/Rosa" if not team_url[-1]=="/" else "Rosa"
        soup = BeautifulSoup(cls._send_request(squad_url, with_session=True),
                             cls.__parser)
        players_table = soup.find("table", attrs={"class": "tc-table"})
        if not players_table:
            return pd.DataFrame()
        players_table = players_table.findNext("tbody")
        players_urls = list()
        for row in players_table.find_all('tr'):
            td = row.find('td', attrs={"class": 'player'})
            if td:
                a = td.find('a')
                if a and len(a.text) > 0:
                    players_urls.append(a.get("href"))
        with ThreadPoolExecutor(max_workers=MAX_THREAD_WORKERS) as executor:
            player_dfs = list(executor.map(lambda url: cls.extract_person(url, queue=queue), players_urls))
            return pd.concat(player_dfs, axis=0) if player_dfs else pd.DataFrame()

    @classmethod
    def extract_person(cls, person_url: str, **kwargs) -> pd.DataFrame:
        """
        extract the info of the specified person.
        :param person_url: this url must be part of the domain tuttocampo.it and concern a person
        :return:
        """
        queue = None if "queue" not in kwargs else kwargs["queue"]
        df = cls.__extract_player(person_url) if "giocatore" in person_url.lower() else cls.__extract_non_player(person_url)
        message = f"\n{df.loc[0]['first_name']} {df.loc[0]['last_name']} ({df.loc[0]['type']}) completed!" if not df.empty else f"\nError on scraping this person {person_url}"
        cls._send_message(message,queue)
        return df

    # non player
    @classmethod
    def __extract_non_player(cls, person_url: str) -> pd.DataFrame:
        soup, data_table = cls.__retry_request(person_url)
        if data_table:
            data = {"entity":"Person", "type": "staff", "club": cls.__extract_club(soup)}
            for row in data_table.find_all('tr'):
                columns = row.find_all('td')
                col_name = columns[0].text.strip().lower()
                if col_name in cls.__person_attributes:
                    data[cls.__person_attributes[col_name]] = columns[1].text
                    if col_name == "data di nascita":
                        cls.__extract_date_of_birth(data, columns)
            # get job
            role = soup.find("span", attrs={"itemprop":"role"})
            job = "dirigente"
            if role:
                job = role.text.lower()
                if job != "allenatore":
                    t = soup.find("div", attrs={"class":"data roles"}).find_all("h3")
                    if t:
                        job = t[-1].text.lower()
            data["job"] = cls.__staff_job[job] if job in cls.__staff_job else "director"
            FMTransferUpdateFiller(data).check_and_fill()
            df = pd.DataFrame(data, index=[0])
            return df
        return pd.DataFrame()

    # player
    @classmethod
    def __extract_player(cls, person_url: str) -> pd.DataFrame:
        soup, data_table = cls.__retry_request(person_url)
        if data_table:
            data = {"entity":"Person", "type": "player", "club": cls.__extract_club(soup),"job": "player"}
            for row in data_table.find_all('tr'):
                columns = row.find_all('td')
                col_name = columns[0].text.strip().lower()
                if col_name == "peso":
                    if "kg" in columns[1].text:
                        data["weight"] = columns[1].text.strip().lower()[:-3]
                if col_name == "altezza":
                    if "cm" in columns[1].text:
                        data["height"] = columns[1].text.strip().lower()[:-3]
                if col_name == "data di nascita":
                    cls.__extract_date_of_birth(data, columns)
                if col_name in cls.__person_attributes:
                    data[cls.__person_attributes[col_name]] = columns[1].text
                if col_name == "piede":
                    cls.__extract_foot(data, columns)
                if col_name == "ruolo":
                    cls.__extract_role(data, columns)
            data = FMInsideFiller(data).check_and_fill()
            df = pd.DataFrame(data, index=[0])
            return df
        return pd.DataFrame()

    @classmethod
    def __retry_request(cls, url: str) -> tuple:
        count = 0
        soup = None
        data_table = None
        while count < 10 and data_table is None:
            soup = BeautifulSoup(cls._send_request(url, with_session=True), cls.__parser)
            data_table = soup.find('table', attrs={"class": 'tc-table-slim'})
            count+=1
        return soup, data_table

    @staticmethod
    def __extract_date_of_birth(data_player:dict, tags: list) -> None:
        date_of_birth = tags[1].text.strip().lower()
        if date_of_birth and len(date_of_birth) > 1:
            try:
                dd = dateparser.parse(date_of_birth,["%d-%m-%Y"]).strftime("%d/%m/%Y")
            except AttributeError as e:
                dd = None
            data_player["date_of_birth"] = dd

    @staticmethod
    def __extract_club(soup: Tag) -> str | None:
        club = soup.find("a", attrs={"itemprop": "affiliation"})
        if club:
            club = club.text
            return club

    @staticmethod
    def __extract_foot(data_player: dict, tags: list) -> None:
        foot = tags[1].text.strip().lower()
        if foot in ["sinistro", "ambidestro"]:
            data_player["left_foot"] = 20
        if foot in ["destro", "ambidestro"]:
            data_player["right_foot"] = 20

    @classmethod
    def __extract_role(cls, data_player: dict, tags: list) -> None:
        position = tags[1].text.strip().lower()
        if position in cls.__positions:
            available_positions = cls.__positions[position]
            if isinstance(available_positions, str):
                data_player[available_positions] = 20
                return
            pos = random.choices(available_positions, k=random.randint(1, len(available_positions)))
            for index, p in enumerate(pos):
                data_player[p] = 20 if index==1 else random.randint(10,20)
