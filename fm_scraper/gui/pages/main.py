import dearpygui.dearpygui as dpg
from fm_scraper.gui.windows import (
    WindowScraping,
    WindowTable
)
from fm_scraper.gui.settings import (
    GUI_MAIN_TITLE,
    MAIN_WINDOW_TAG,
    WINDOW_MIN_HEIGHT,
    WINDOW_MIN_WIDTH
)
from fm_scraper.gui.themes import GUITheme


class GUIMain:

    def __init__(self):
        self.entities = list()
        dpg.create_context()
        dpg.create_viewport(title=GUI_MAIN_TITLE, width=-1, height=-1,
                            min_width=WINDOW_MIN_WIDTH, min_height=WINDOW_MIN_HEIGHT,
                            decorated=True)
        with dpg.window(tag=MAIN_WINDOW_TAG):
            with dpg.group(horizontal=True):
                WindowScraping()
                WindowTable()
        GUITheme.load_themes()
        dpg.setup_dearpygui()
        dpg.maximize_viewport()
        dpg.show_viewport()
        dpg.set_primary_window(MAIN_WINDOW_TAG, True)
        dpg.start_dearpygui()
        dpg.destroy_context()
        dpg.show_debug()
