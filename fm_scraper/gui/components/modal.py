import dearpygui.dearpygui as dpg
from abc import ABC
from typing import Tuple


class Modal(ABC):

    @staticmethod
    def _get_viewport_sizes() -> Tuple[int, int]:
        viewport_width = dpg.get_viewport_client_width()
        viewport_height = dpg.get_viewport_client_height()
        return viewport_width, viewport_height

    @staticmethod
    def _get_item_sizes(item) -> Tuple[int, int]:
        width = dpg.get_item_width(item)
        height = dpg.get_item_height(item)
        return width, height

    @classmethod
    def _center_modal_window(cls, modal_window) -> None:
        viewport_width, viewport_height = cls._get_viewport_sizes()
        width, height = cls._get_item_sizes(modal_window)
        dpg.set_item_pos(modal_window, [viewport_width // 2 - width, viewport_height // 2 - height])
