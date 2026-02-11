from collections.abc import Callable
from typing import Any

import flet as ft

from amrita_agent.utils.alert import AlertDialog
from amrita_agent.utils.chat import DataManager

from ..constants import SIDEBAR_WIDTH, ColorsEnum, FontSizesEnum


class NavButton(ft.Container):
    def __init__(self, label, icon, key, on_click, on_hover):
        super().__init__()
        self.key = key
        self.icon_control = ft.Icon(
            name=icon, color=ColorsEnum.text_secondary.value, size=20
        )
        self.text_control = ft.Text(
            label,
            color=ColorsEnum.text_secondary.value,
            size=FontSizesEnum.body.value,
        )

        self.content = ft.Row(
            controls=[
                self.icon_control,
                self.text_control,
            ],
            spacing=12,
        )

        self.padding = ft.padding.symmetric(horizontal=15, vertical=12)
        self.on_hover = on_hover
        self.on_click = lambda e: on_click(key)
        self.animate_bgcolor = ft.Animation(100, ft.AnimationCurve.EASE_IN_OUT)
        self.animate_scale = ft.Animation(100, ft.AnimationCurve.EASE_IN_OUT)


class Sidebar(ft.Container):
    edit_alert: AlertDialog
    delete_alert: AlertDialog

    def __init__(self, on_nav_select: Callable[[Any], Any]):
        super().__init__()
        self.on_nav_select = on_nav_select
        self.is_collapsed = False
        self.width = SIDEBAR_WIDTH
        self.bgcolor = ColorsEnum.bg_secondary.value
        self.padding = 0
        self.margin = 0

        self.animate = ft.Animation(duration=100, curve=ft.AnimationCurve.EASE_IN_OUT)

        # 标题和图标（折叠时隐藏文本）
        self.logo_icon = ft.Icon(
            name="smart_toy",
            color=ColorsEnum.accent_primary.value,
            size=24,
        )

        self.logo_text = ft.Text(
            "AmritaAgent",
            size=FontSizesEnum.title.value,
            color=ColorsEnum.text_primary.value,
            weight=ft.FontWeight.BOLD,
        )

        self.header = ft.Container(
            content=ft.Row(
                controls=[
                    self.logo_icon,
                    self.logo_text,
                ],
                spacing=10,
            ),
            padding=ft.padding.symmetric(horizontal=15, vertical=15),
            border=ft.border.only(
                bottom=ft.border.BorderSide(1, ColorsEnum.divider.value)
            ),
        )

        self.nav_buttons = [
            NavButton(
                "新建对话",
                "add_circle",
                "chat",
                self.on_nav_select,
                self._on_button_hover,
            ),
        ]

        self.nav_column = ft.Column(
            controls=self.nav_buttons,
            spacing=8,
        )

        # 当前对话部分
        self.recent_conversations = self._create_recent_conversations()

        self.recent_title = ft.Text(
            "当前对话",
            size=FontSizesEnum.small.value,
            color=ColorsEnum.text_secondary.value,
            weight=ft.FontWeight.BOLD,
        )

        self.recent_column = ft.Column(
            controls=[self.recent_title, *self.recent_conversations],
            spacing=4,
        )

        self.recent_container = ft.Container(
            content=self.recent_column,
            padding=ft.padding.symmetric(horizontal=10, vertical=5),
        )

        # 历史记录按钮
        self.history_button = NavButton(
            "历史记录", "history", "history", self.on_nav_select, self._on_button_hover
        )

        self.main_nav_column = ft.Column(
            controls=[
                self.nav_column,
                ft.Container(height=10),
                self.recent_container,
                ft.Container(height=10),
                self.history_button,
            ],
            spacing=0,
            scroll=ft.ScrollMode.AUTO,
            expand=True,
        )

        self.settings_button = NavButton(
            "设置", "settings", "settings", self.on_nav_select, self._on_button_hover
        )

        # 折叠按钮作为一个特殊的导航按钮
        self.collapse_button = NavButton(
            "折叠侧边栏",
            "menu",
            "collapse",
            lambda key: self._toggle_collapse(),
            self._on_button_hover,
        )

        self.footer_buttons = ft.Column(
            controls=[
                self.settings_button,
                self.collapse_button,
            ],
            spacing=8,
        )

        self.content = ft.Column(
            controls=[
                self.header,
                ft.Container(
                    content=self.main_nav_column,
                    padding=ft.padding.symmetric(horizontal=10, vertical=10),
                    expand=True,
                ),
                ft.Divider(color=ColorsEnum.divider.value, height=1),
                ft.Container(
                    content=self.footer_buttons,
                    padding=ft.padding.symmetric(horizontal=10, vertical=10),
                ),
            ],
            spacing=0,
            expand=True,
        )

    def _on_button_hover(self, e):
        if e.data == "true":
            e.control.bgcolor = ColorsEnum.bg_tertiary.value
        else:
            e.control.bgcolor = None
        e.control.update()

    def _create_recent_conversations(self):
        """创建最近对话列表"""
        items = list(DataManager()._sessionid2memory.values())
        items.sort(key=lambda x: x.last_update, reverse=True)
        recent_chats: list[str] = [i.name for i in items]

        conversations = []
        for chat in recent_chats:
            # 编辑按钮
            edit_btn = ft.IconButton(
                icon="edit",
                icon_size=14,
                tooltip="编辑",
                on_click=lambda e, title=chat: self._on_edit_conversation(title),
            )

            # 删除按钮
            delete_btn = ft.IconButton(
                icon="delete",
                icon_size=14,
                tooltip="删除",
                on_click=lambda e, title=chat: self._on_delete_conversation(title),
            )

            conv_btn = ft.Container(
                content=ft.Row(
                    controls=[
                        ft.Icon(
                            name="chat", color=ColorsEnum.text_secondary.value, size=16
                        ),
                        ft.Text(
                            chat,
                            color=ColorsEnum.text_secondary.value,
                            size=FontSizesEnum.small.value,
                            max_lines=1,
                            overflow=ft.TextOverflow.ELLIPSIS,
                            expand=True,
                        ),
                        edit_btn,
                        delete_btn,
                    ],
                    spacing=4,
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                ),
                padding=ft.padding.symmetric(horizontal=8, vertical=6),
                border_radius=ft.border_radius.all(6),
                on_hover=lambda e, btn=None: self._on_conv_hover(e, btn),
                on_click=lambda _: self._on_conversation_click(chat),
            )
            conversations.append(conv_btn)

        return conversations

    def _on_conv_hover(self, e, btn):
        if e.data == "true":
            e.control.bgcolor = ColorsEnum.bg_tertiary.value
        else:
            e.control.bgcolor = None
        e.control.update()

    def _on_conversation_click(self, chat_title: str):
        """点击对话时的处理"""
        pass

    def _on_edit_conversation(self, chat_title: str):
        """编辑对话时的处理"""
        if not self.edit_alert:
            return

        def on_confirm(e):
            new_title = self.edit_alert.get_input_value()
            if new_title and new_title.strip():
                print(f"编辑对话: {chat_title} -> {new_title}")

        self.edit_alert.set_input_value(chat_title)
        self.edit_alert.clear_buttons()
        self.edit_alert.add_button("取消", lambda e: None, "normal")
        self.edit_alert.add_button("确认", on_confirm, "primary")
        self.edit_alert.show()

    def _on_delete_conversation(self, chat_title):
        """删除对话时的处理"""
        if not self.delete_alert:
            return

        def on_confirm(e):
            print(f"删除对话: {chat_title}")

        self.delete_alert.clear_buttons()
        self.delete_alert.add_button("取消", lambda e: None, "normal")
        self.delete_alert.add_button("删除", on_confirm, "danger")
        self.delete_alert.show()

    def _toggle_collapse(self):
        self.is_collapsed = not self.is_collapsed

        if self.is_collapsed:
            self.logo_text.visible = False
            self.recent_container.visible = False
            for btn in self.nav_buttons:
                btn.text_control.visible = False
                btn.padding = ft.padding.symmetric(horizontal=12, vertical=12)
            self.history_button.text_control.visible = False
            self.history_button.padding = ft.padding.symmetric(
                horizontal=12, vertical=12
            )
            self.settings_button.text_control.visible = False
            self.settings_button.padding = ft.padding.symmetric(
                horizontal=12, vertical=12
            )
            self.collapse_button.text_control.visible = False
            self.collapse_button.padding = ft.padding.symmetric(
                horizontal=12, vertical=12
            )

            # 最后改变宽度
            self.width = 60
        else:
            self.width = SIDEBAR_WIDTH
            self.update()
            self.logo_text.visible = True
            self.recent_container.visible = True
            for btn in self.nav_buttons:
                btn.text_control.visible = True
                btn.padding = ft.padding.symmetric(horizontal=15, vertical=12)
            self.history_button.text_control.visible = True
            self.history_button.padding = ft.padding.symmetric(
                horizontal=15, vertical=12
            )
            self.settings_button.text_control.visible = True
            self.settings_button.padding = ft.padding.symmetric(
                horizontal=15, vertical=12
            )
            self.collapse_button.text_control.visible = True
            self.collapse_button.padding = ft.padding.symmetric(
                horizontal=15, vertical=12
            )

        self.update()
