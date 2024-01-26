import dearpygui.dearpygui as dpg
import inspect
import fm_scraper.scrapers as scrapers
from pathlib import Path
from pydispatch import dispatcher
from fm_scraper.core.utilities import ClassUtilities
from fm_scraper.gui.components import Modal
from fm_scraper.gui.settings import (
    MESSAGE_QUEUE,
    SIGNAL_SCRAPING_COMPLETED,
    SIGNAL_TABLE_LOADED_DATA,
    SIGNAL_TABLE_EMPTY,
    WINDOW_SCRAPING_TAG,
)
from fm_scraper.gui.themes import GUITheme
from fm_scraper.scrapers.settings import DEBUG
from .window_log import WindowLog
from .window_table import WindowTable


class WindowScraping(Modal):

    __scrapers = {n:c for n,c in inspect.getmembers(scrapers, inspect.isclass)}
    __url_scraped_successfully = "Url scraped successfully!"
    __url_scraped_failed = "Error on running {method}.\nError: {error}."

    def __init__(self):
        GUITheme.load_other_themes()
        with dpg.file_dialog(label="Save scraped data as", show=False,
                             callback=self.export_scraping_data,
                             width=700,
                             height=400, default_filename="scraping_result",
                             default_path="./") as export_scraping_data:
            dpg.add_file_extension("", color=(255, 150, 150, 255))
            dpg.add_file_extension(".xlsx")
            dpg.add_file_extension(".csv")
            dpg.add_file_extension(".xml")
            dpg.add_file_extension(".json")

        with dpg.child_window(width=800, tag=WINDOW_SCRAPING_TAG):
            with dpg.group():
                with dpg.group():
                    with dpg.group():
                        # export data
                        dpg.add_button(
                            label="Export scraped data",
                            callback=lambda: dpg.show_item(export_scraping_data),
                            # callback=fd.show_file_dialog,
                            enabled=False,
                            tag="export_file",
                            width=-1
                        )
                        dpg.bind_item_theme(dpg.last_item(), "success_button_theme")
                        # clear table
                        dpg.add_button(
                           label="Clear table",
                           enabled=False,
                           tag="clear_table",
                           callback=lambda: WindowTable.clear_table(),
                           width=-1
                        )
                        dpg.bind_item_theme(dpg.last_item(), "alert_button_theme")
                with dpg.group():
                    dpg.add_text("Available scrapers")
                    dpg.add_spacer(width=10)
                    for n, c in self.__scrapers.items():
                        with dpg.collapsing_header(label=n):
                            available_methods = ClassUtilities.extract_methods_from_class(c)
                            for method in available_methods:
                                tag = method.name
                                with dpg.tree_node(label=method.name.replace('_', ' '), tag=f"{n}_{tag}") as tree_node:
                                    dpg.add_text("(?)")
                                    with dpg.tooltip(dpg.last_item()):
                                        dpg.add_text(method.doc)
                                    for argument in method.arguments:
                                        kwargs = {
                                            "width": dpg.get_item_width(tree_node) // 2,
                                            "tag": f"{n}_{method.name}_{argument.name}",
                                            "label": argument.name
                                        }
                                        if argument.default_value:
                                            kwargs["default_value"] = str(argument.default_value)
                                        if isinstance(argument.type, int):
                                            dpg.add_input_int(**kwargs)
                                        elif isinstance(argument.type, float):
                                            dpg.add_input_float(**kwargs)
                                        else:
                                            dpg.add_input_text(**kwargs)
                                    dpg.add_button(
                                        label=f"Applica funzione",
                                        callback=self.__apply_entity_method,
                                        user_data={"class": c, "method": method.name, "args": method.arguments},
                                        width=-1
                                    )
                                    dpg.add_spacer(height=5)
            dispatcher.connect(self.__added_row_table, signal=SIGNAL_TABLE_LOADED_DATA)
            dispatcher.connect(self.__empty_table, signal=SIGNAL_TABLE_EMPTY)

    @staticmethod
    def export_scraping_data(sender: int, app_data: dict) -> None:
        file_path = Path(app_data["file_path_name"]).resolve()
        # save
        format_file = file_path.suffix
        df = WindowTable.df
        df.reset_index(drop=True, inplace=True)
        if format_file == ".xml":
            df.to_xml(file_path, index=False)
            return
        if format_file == ".csv":
            df.to_csv(file_path, index=False)
            return
        if format_file == ".xlsx":
            df.to_excel(file_path, index=False)
            return
        if format_file == ".json":
            df.to_json(file_path, index=False, indent=4, orient='records', date_format='iso')

    @classmethod
    def __apply_entity_method(cls, sender: int, app_data: dict, user_data: dict) -> None:
        class_name = user_data["class"]
        method_name = user_data["method"]
        args = user_data["args"]
        from multiprocessing import Manager
        with Manager() as m:
            try:
                q = m.Queue()
                # start scraping and open a log window
                a = {arg.name: arg.type(dpg.get_value(f"{class_name.__name__}_{method_name}_{arg.name}")) for arg in args}
                WindowLog(q)
                obj = class_name()
                df = getattr(obj, method_name)(**a,queue=q)
                if not df.empty:
                    WindowTable.add_rows(df)
                for arg in args:
                    dpg.set_value(f"{class_name.__name__}_{method_name}_{arg.name}", "")
            except Exception as e:
                message = f"\n\nError!"
                if DEBUG:
                    message += f" - {e}\n\n"
                    raise e
                q.put(message)
            dispatcher.send(SIGNAL_SCRAPING_COMPLETED, cls, event=None)

    @classmethod
    def __added_row_table(cls, row: object) -> None:
        dpg.enable_item("export_file")
        dpg.enable_item("clear_table")

    @classmethod
    def __empty_table(cls) -> None:
        dpg.disable_item("export_file")
        dpg.disable_item("clear_table")
