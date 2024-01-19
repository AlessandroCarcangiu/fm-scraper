import dateparser
import inspect
from bs4 import Tag
from collections import namedtuple
from datetime import datetime, date
from dateutil.relativedelta import relativedelta
from Levenshtein import ratio
from typing import Callable, List


Method = namedtuple("Method", ['name', 'arguments', "doc"])
Argument = namedtuple("Argument", ['name', 'type', 'default_value'])


class ClassUtilities:

    @staticmethod
    def extract_methods_from_class(clazz:Callable, methods_to_exclude:list=None) -> List[Method]:
        if not methods_to_exclude:
            methods_to_exclude = list()
        methods = [method for name, method in clazz.__dict__.items()
                   if not name.startswith("_") and name not in methods_to_exclude]
        available_methods = list()
        for i in methods:
            data = {
                "name": i.__name__,
                "doc": i.__doc__
            }
            arguments = list()
            for argument, info in inspect.signature(i.__func__).parameters.items():
                if argument not in ["self", "cls", "kwargs", "args"]:
                    arguments.append(Argument(
                        argument,
                        info.annotation if info.annotation != inspect.Parameter.empty else any,
                        info.default if info.default != inspect.Parameter.empty else None
                    ))
            data["arguments"] = arguments
            available_methods.append(Method(**data))
        return available_methods


class DateUtilities:

    @staticmethod
    def string_to_datetime(string_date: str) -> datetime:
        formats = ["%Y-%m-%d", "%Y/%m/%d", "%Y%m%d", "%B %d, %Y", "%b %d, %Y", "%d %B %Y", "%d %b %Y",
                   "%d/%m/%Y", "%d-%m-%Y", "%d%m%Y"]
        for format_str in formats:
            try:
                date_obj = datetime.strptime(string_date, format_str)
                return date_obj
            except ValueError:
                pass
        raise Exception(
            f"Error on parsing this date: {string_date}, please check its format or value. List of accepted date formats: {formats}")

    @classmethod
    def get_years_from_today(cls, a: any) -> int:
        today = date.today()
        delta = cls.__sub_two_dates(today, dateparser.parse(a))
        return delta.years

    @staticmethod
    def __sub_two_dates(a, b) -> any:
        return relativedelta(a, b)


class StringUtilities:

    @staticmethod
    def safe_equals(a: str, b: str, use_levenshtein: bool = True, acceptable_levenshtein_ration: float = 0.85) -> bool:
        a = a.strip().lower()
        b = b.strip().lower()
        if use_levenshtein:
            return ratio(a, b) > acceptable_levenshtein_ration or b.startswith(a)
        return a == b

    @staticmethod
    def extract_safe_text(item: Tag) -> str:
        return item.text.strip().lower() if item else ""
