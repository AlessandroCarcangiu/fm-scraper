import dearpygui.dearpygui as dpg


class GUITheme:

    @staticmethod
    def load_themes():
        with dpg.theme() as global_theme:
            with dpg.theme_component(dpg.mvTable):
                dpg.add_theme_color(dpg.mvThemeCol_HeaderHovered, (255, 0, 0, 100), category=dpg.mvThemeCat_Core)
                dpg.add_theme_color(dpg.mvThemeCol_HeaderActive, (0, 0, 0, 0), category=dpg.mvThemeCat_Core)
                dpg.add_theme_color(dpg.mvThemeCol_Header, (0, 0, 0, 0), category=dpg.mvThemeCat_Core)
                dpg.add_theme_color(dpg.mvThemeCol_TextDisabled, (0, 0, 0, 0), category=dpg.mvThemeCat_Core)
            with dpg.theme_component(dpg.mvButton):
                dpg.add_theme_color(dpg.mvThemeCol_Button, (255, 0, 0, 255))
                dpg.add_theme_style(dpg.mvStyleVar_FrameRounding, 12)
        with dpg.theme() as disabled_theme:
            with dpg.theme_component(dpg.mvButton, enabled_state=False):
                dpg.add_theme_color(dpg.mvThemeCol_ButtonActive, [50, 50, 50])
                dpg.add_theme_color(dpg.mvThemeCol_Button, [50, 50, 50])
                dpg.add_theme_color(dpg.mvThemeCol_ButtonHovered, [50, 50, 50])
                dpg.add_theme_color(dpg.mvThemeCol_Text, [128, 128, 128])
        for t in [global_theme,disabled_theme]:
            dpg.bind_theme(t)

    @staticmethod
    def load_other_themes() -> None:
        with dpg.theme(tag="alert_button_theme") as alert_button_theme:
            with dpg.theme_component(dpg.mvButton):
                dpg.add_theme_color(dpg.mvThemeCol_Button, (160, 0, 0))
                dpg.add_theme_color(dpg.mvThemeCol_ButtonActive, (160, 0, 0))
                dpg.add_theme_color(dpg.mvThemeCol_ButtonHovered, (200, 0, 0))
            with dpg.theme_component(dpg.mvButton, enabled_state=False):
                dpg.add_theme_color(dpg.mvThemeCol_ButtonActive, [120, 0, 0])
                dpg.add_theme_color(dpg.mvThemeCol_Button, [120, 0, 0])
                dpg.add_theme_color(dpg.mvThemeCol_ButtonHovered, [120, 0, 0])
        with dpg.theme(tag="success_button_theme") as success_button_theme:
            with dpg.theme_component(dpg.mvButton):
                dpg.add_theme_color(dpg.mvThemeCol_Button, (0, 120, 0))
                dpg.add_theme_color(dpg.mvThemeCol_ButtonActive, (0, 120, 0))
                dpg.add_theme_color(dpg.mvThemeCol_ButtonHovered, (0, 160, 0))
            with dpg.theme_component(dpg.mvButton, enabled_state=False):
                dpg.add_theme_color(dpg.mvThemeCol_ButtonActive, [0, 100, 0])
                dpg.add_theme_color(dpg.mvThemeCol_Button, [0, 100, 0])
                dpg.add_theme_color(dpg.mvThemeCol_ButtonHovered, [0, 100, 0])
        with dpg.theme(tag="success_message_theme") as success_message_theme:
            with dpg.theme_component(dpg.mvText):
                dpg.add_theme_color(dpg.mvThemeCol_Text, (0, 120, 0))
        with dpg.theme(tag="error_message_theme") as error_message_theme:
            with dpg.theme_component(dpg.mvText):
                dpg.add_theme_color(dpg.mvThemeCol_Text, (160, 0, 0))
        for t in [alert_button_theme,success_button_theme,success_message_theme,error_message_theme]:
            dpg.bind_theme(t)

    # @staticmethod
    # def load_disable_button_theme() -> None:
    #     with dpg.theme(tag="alert_button_theme"):
    #         with dpg.theme_component(dpg.mvButton):
    #             dpg.add_theme_color(dpg.mvThemeCol_Button, (160, 0, 0))
    #             dpg.add_theme_color(dpg.mvThemeCol_ButtonActive, (160, 0, 0))
    #             dpg.add_theme_color(dpg.mvThemeCol_ButtonHovered, (200, 0, 0))
    #         with dpg.theme_component(dpg.mvButton, enabled_state=False):
    #             dpg.add_theme_color(dpg.mvThemeCol_ButtonActive, [120, 0, 0])
    #             dpg.add_theme_color(dpg.mvThemeCol_Button, [120, 0, 0])
    #             dpg.add_theme_color(dpg.mvThemeCol_ButtonHovered, [120, 0, 0])
    #
    # @staticmethod
    # def load_success_button_theme() -> None:
    #     with dpg.theme(tag="success_button_theme"):
    #         with dpg.theme_component(dpg.mvButton):
    #             dpg.add_theme_color(dpg.mvThemeCol_Button, (0, 120, 0))
    #             dpg.add_theme_color(dpg.mvThemeCol_ButtonActive, (0, 120, 0))
    #             dpg.add_theme_color(dpg.mvThemeCol_ButtonHovered, (0, 160, 0))
    #         with dpg.theme_component(dpg.mvButton, enabled_state=False):
    #             dpg.add_theme_color(dpg.mvThemeCol_ButtonActive, [0, 100, 0])
    #             dpg.add_theme_color(dpg.mvThemeCol_Button, [0, 100, 0])
    #             dpg.add_theme_color(dpg.mvThemeCol_ButtonHovered, [0, 100, 0])
    #
    # @staticmethod
    # def success_message_theme() -> None:
    #     with dpg.theme(tag="success_message_theme"):
    #         with dpg.theme_component(dpg.mvText):
    #             dpg.add_theme_color(dpg.mvThemeCol_Text, (0, 120, 0))
    #
    # @staticmethod
    # def error_message_theme() -> None:
    #     with dpg.theme(tag="error_message_theme"):
    #         with dpg.theme_component(dpg.mvText):
    #             dpg.add_theme_color(dpg.mvThemeCol_Text, (160, 0, 0))
