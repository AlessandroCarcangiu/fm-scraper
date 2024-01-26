import time
import dearpygui.dearpygui as dpg
from pydispatch import dispatcher
from threading import Thread
from fm_scraper.gui.components import Modal
from fm_scraper.gui.settings import (
    BUTTON_MODAL_EXIT_TAG,
    MESSAGE_LOG_TEXT_TAG,
    MODAL_MESSAGE_LOG_TAG,
    SIGNAL_SCRAPING_COMPLETED,
)


class WindowLog(Modal):

    __FRAME_PADDING = 1
    __is_completed = None

    def __init__(self, queue) -> None:
        self.queue = queue
        with dpg.mutex():
            with dpg.window(label="Scraping Logger", modal=True, no_close=True,
                            tag=MODAL_MESSAGE_LOG_TAG, width=500, height=400) as modal_message:
                dpg.add_button(
                    label="Ok",
                    tag=BUTTON_MODAL_EXIT_TAG,
                    width=-1,
                    show=True,
                    enabled=False,
                    callback=lambda x: dpg.delete_item(modal_message)
                )
                # log console
                with dpg.child_window():
                    dpg.add_input_text(
                        tag=MESSAGE_LOG_TEXT_TAG,
                        multiline=True,
                        readonly=True,
                        tracked=True,
                        track_offset=1,
                        width=-1,
                        height=-1,
                        default_value="Start scraping...."
                    )
        dpg.split_frame()
        self._center_modal_window(modal_message)
        dispatcher.connect(self.__end_logging, signal=SIGNAL_SCRAPING_COMPLETED)
        # start thread for reading messages from queue
        self.__is_completed = False
        thread = Thread(target=self.__read_queue_thread)
        thread.start()

    @classmethod
    def __update_log(cls, text: str) -> None:
        text = dpg.get_value(MESSAGE_LOG_TEXT_TAG) + text
        dpg.set_value(MESSAGE_LOG_TEXT_TAG, text)
        dpg.set_item_height(MESSAGE_LOG_TEXT_TAG, int(dpg.get_text_size(text)[1] + (2 * 3)))

    def __read_queue_thread(self) -> None:
        while not self.__is_completed:
            self.__read_queue()
            time.sleep(0.1)

    @classmethod
    def __show_new_message(cls, message: str) -> None:
        cls.__update_log(message)

    def __read_queue(self) -> None:
        text = ""
        if self.queue:
            while not self.queue.empty():
                mes = self.queue.get()
                if mes:
                    text += str(mes)
            if text:
                self.__update_log(text)

    def __end_logging(self, *args, **kwargs) -> None:
        self.__read_queue()
        self.__is_completed = True
        text = "\n...... scraping completed"
        self.__update_log(text)
        dpg.enable_item(BUTTON_MODAL_EXIT_TAG)
