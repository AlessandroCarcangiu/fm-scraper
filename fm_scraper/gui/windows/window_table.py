import dearpygui.dearpygui as dpg
import pandas as pd
from pydispatch import dispatcher
from fm_scraper.gui.components import Modal
from fm_scraper.gui.settings import (
    SIGNAL_TABLE_LOADED_DATA,
    SIGNAL_TABLE_EMPTY,
    TABLE_TAG,
    WINDOW_TABLE_TAG
)


class WindowTable:
    df = pd.DataFrame()
    __headers = ["type", "club", "last_name", "first_name", "date_of_birth"]

    def __init__(self) -> None:
        with dpg.group(label="Table"):
            with dpg.child_window(height=-1, width=-1, label="Table", tag=WINDOW_TABLE_TAG):
                dpg.add_spacer(height=5)
                self.create_table()

    @classmethod
    def create_table(cls) -> None:
        with dpg.table(header_row=True, resizable=True, policy=dpg.mvTable_SizingStretchProp,
                       row_background=True,
                       tag=TABLE_TAG, parent=WINDOW_TABLE_TAG):
            cls.add_headers(cls.__headers)
            pass

    @staticmethod
    def add_headers(headers: list) -> None:
        for header in headers:
            dpg.add_table_column(label=header, parent=TABLE_TAG)

    @classmethod
    def add_rows(cls, rows: pd.DataFrame) -> None:
        for index, row in rows.iterrows():
            with dpg.table_row(parent=TABLE_TAG):
                for column in [c for c in cls.__headers if c in row]:
                    dpg.add_selectable(label=f"{row[column]}", span_columns=True, callback=RowTable.show_row, user_data=row)
        cls.df = pd.concat([cls.df, rows])
        if not cls.df.empty:
            dispatcher.send(SIGNAL_TABLE_LOADED_DATA, dpg.last_item(), row=None)

    @classmethod
    def clear_table(cls) -> None:
        cls.entities = pd.DataFrame()
        dpg.delete_item(TABLE_TAG)
        cls.create_table()
        dispatcher.send(SIGNAL_TABLE_EMPTY, dpg.last_item())


class RowTable(Modal):

    __latest_window = None

    @classmethod
    def show_row(cls, sender, app_data, user_data) -> None:
        if cls.__latest_window and dpg.does_alias_exist(cls.__latest_window):
            dpg.delete_item(cls.__latest_window)
        with dpg.mutex():
            tag = f"row_tooltip_{user_data['tag']}"
            with dpg.window(width=400, height=400, tag=tag):
                with dpg.table(header_row=False, row_background=True):
                    dpg.add_table_column()
                    dpg.add_table_column()
                    for k, v in user_data.items():
                        with dpg.table_row():
                            dpg.add_text(k)
                            dpg.add_text(v)
            cls.__latest_window = tag
        dpg.split_frame()
