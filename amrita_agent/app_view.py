from amrita_core import logger
import flet as ft

from .components.chat_area import ChatArea
from .components.history_area import HistoryArea
from .components.settings_area import SettingsArea
from .components.sidebar import Sidebar
from .config import AgentConfig
from .constants import ColorsEnum
from .utils.alert import AlertDialog


class AppView(ft.Container):
    def __init__(self, page: ft.Page):
        super().__init__()
        self.page = page
        self.expand = True
        self.padding = 0
        self.bgcolor = ColorsEnum.bg_primary.value

        self.sidebar = Sidebar(
            on_nav_select=self._on_nav_select,
        )
        self.delete_alert = AlertDialog(
            title="删除对话",
            message="确定要删除这个对话吗？",
        )

        # AlertDialog - 编辑对话
        self.edit_alert = AlertDialog(
            title="编辑对话标题",
            message="请输入新的对话标题：",
            input_field=True,
        )
        self.chat_area = ChatArea(self.edit_alert)
        self.history_area = HistoryArea()
        self.settings_area = SettingsArea()

        self.main_content = ft.AnimatedSwitcher(
            content=self.chat_area,
            transition=ft.AnimatedSwitcherTransition.FADE,
            duration=300,
            switch_in_curve=ft.AnimationCurve.EASE_IN_OUT,
            switch_out_curve=ft.AnimationCurve.EASE_IN_OUT,
            expand=True,
        )

        # 设置 sidebar 的对话框引用
        self.sidebar.delete_alert = self.delete_alert
        self.sidebar.edit_alert = self.edit_alert

        self.content = ft.Stack(
            controls=[
                ft.Row(
                    controls=[
                        self.sidebar,
                        self.main_content,
                    ],
                    spacing=0,
                    expand=True,
                ),
                self.delete_alert,
                self.edit_alert,
            ],
            expand=True,
        )

        self.history_area.delete_alert = self.delete_alert
        self.history_area.edit_alert = self.edit_alert

    def _on_nav_select(self, nav_key):
        if nav_key == "chat":
            self._show_chat()
        elif nav_key == "history":
            self._show_history()
        elif nav_key == "settings":
            self._show_settings()

    def _show_chat(self):
        self._transition_content(self.chat_area)

    def _show_history(self):
        self._transition_content(self.history_area)

    def _show_settings(self):
        self._transition_content(self.settings_area)

    def _transition_content(self, new_content):
        """带动画的内容切换"""
        self.main_content.opacity = 0
        self.main_content.update()
        self.main_content.content = new_content
        self.main_content.opacity = 1
        self.main_content.update()

    def _on_send_message(self, e):
        message = self.chat_area.get_input_value()
        if not message or not message.strip():
            return

        preset = self.chat_area.get_selected_preset()
        if not preset:
            logger.info("No preset selected")
            return

        self.chat_area.add_message(message, is_user=True)
        self.chat_area.clear_input()

        self._send_to_backend(message, preset)

    def build(self):
        self.chat_area.send_button.on_click = self._on_send_message
    def _send_to_backend(self, message: str, model: str):
        pass
