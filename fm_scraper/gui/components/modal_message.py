import dearpygui.dearpygui as dpg
from typing import Callable
from .modal import Modal


class ModalMessage(Modal):

    def __init__(self, message: str, color: list = None, callback: Callable = None) -> None:
        if not callback:
            callback = self.__default_on_selection
        with dpg.mutex():
            with dpg.window(label="Exporting File", modal=True, no_close=True) as modal_message:
                arguments = dict()
                if color:
                    arguments["color"] = color
                dpg.add_text(message, **arguments)
                dpg.add_button(label="Ok", width=-1, user_data=(modal_message, True), callback=callback)
        dpg.split_frame()
        self._center_modal_window(modal_message)

    @staticmethod
    def __default_on_selection(sender, unused, user_data):
        dpg.delete_item(user_data[0])
