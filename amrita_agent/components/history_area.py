import flet as ft
from amrita_core import logger

from amrita_agent.utils.alert import AlertDialog
from amrita_agent.utils.chat import DataManager

from ..constants import MAIN_PADDING, ColorsEnum, FontSizesEnum


class HistoryItem(ft.Container):
    def __init__(self, title, timestamp, on_click, on_edit=None, on_delete=None):
        super().__init__()
        self.title = title
        self.padding = ft.padding.symmetric(horizontal=12, vertical=10)
        self.bgcolor = ColorsEnum.bg_tertiary.value
        self.border_radius = ft.border_radius.all(8)
        self.margin = ft.margin.symmetric(vertical=5)
        self.on_click = on_click

        # 编辑和删除按钮容器（初始隐藏）
        self.edit_btn = ft.IconButton(
            icon="edit",
            icon_size=18,
            icon_color=ColorsEnum.accent_primary.value,
            on_click=lambda _: on_edit(title) if on_edit else None,
        )

        self.delete_btn = ft.IconButton(
            icon="delete",
            icon_size=18,
            icon_color="#ef4444",
            on_click=lambda _: on_delete(title) if on_delete else None,
        )

        self.button_row = ft.Row(
            controls=[
                self.edit_btn,
                self.delete_btn,
            ],
            spacing=8,
            visible=False,  # 默认隐藏，hover 时显示
        )

        self.content = ft.Row(
            controls=[
                ft.Column(
                    controls=[
                        ft.Text(
                            title,
                            size=FontSizesEnum.body.value,
                            color=ColorsEnum.text_primary.value,
                            weight=ft.FontWeight.BOLD,
                            max_lines=1,
                            overflow=ft.TextOverflow.ELLIPSIS,
                        ),
                        ft.Text(
                            timestamp,
                            size=FontSizesEnum.small.value,
                            color=ColorsEnum.text_secondary.value,
                        ),
                    ],
                    spacing=5,
                    expand=True,
                ),
                self.button_row,
            ],
            spacing=10,
        )

        # 添加 hover 效果
        self.on_hover = self._on_hover

    def _on_hover(self, e):
        if e.data == "true":
            self.button_row.visible = True
        else:
            self.button_row.visible = False
        self.button_row.update()


class HistoryArea(ft.Container):
    edit_alert: AlertDialog
    delete_alert: AlertDialog

    def __init__(self):
        super().__init__()
        self.bgcolor = ColorsEnum.bg_primary.value
        self.expand = True
        self.padding = MAIN_PADDING

        self.search_field = ft.TextField(
            label="搜索历史",
            prefix_icon="search",
            bgcolor=ColorsEnum.input_bg.value,
            color=ColorsEnum.text_primary.value,
            label_style=ft.TextStyle(color=ColorsEnum.text_secondary.value),
            border_color=ColorsEnum.input_border.value,
            focused_border_color=ColorsEnum.accent_primary.value,
        )

        self.clear_button = ft.IconButton(
            icon="delete_sweep",
            icon_color="#ff0000",
            on_click=lambda _: self._on_clear_all(),
        )

        self.history_list = ft.Column(
            spacing=8,
            scroll=ft.ScrollMode.AUTO,
            expand=True,
        )

        self.empty_state = ft.Column(
            controls=[
                ft.Icon(
                    name="history",
                    size=64,
                    color=ColorsEnum.text_secondary.value,
                ),
                ft.Text(
                    "没有历史记录",
                    size=FontSizesEnum.body.value,
                    color=ColorsEnum.text_secondary.value,
                    text_align=ft.TextAlign.CENTER,
                ),
            ],
            spacing=20,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            alignment=ft.MainAxisAlignment.CENTER,
        )

        self.content = ft.Column(
            controls=[
                ft.Row(
                    controls=[
                        ft.Text(
                            "历史记录",
                            size=FontSizesEnum.heading.value,
                            weight=ft.FontWeight.BOLD,
                            color=ColorsEnum.text_primary.value,
                        ),
                        ft.Container(expand=True),
                        self.clear_button,
                    ],
                    spacing=10,
                ),
                self.search_field,
                self.history_list,
            ],
            spacing=15,
            expand=True,
        )

        self._load_history()

    def _load_history(self):
        self.history_list.controls.clear()

        items = list(DataManager()._sessionid2memory.values())
        items.sort(key=lambda x: x.last_update, reverse=True)
        items = [(i.name, i.last_update.strftime("%Y-%m-%d %H:%M:%S")) for i in items]
        if not items:
            self.history_list.controls.append(self.empty_state)
        else:
            for title, timestamp in items:
                item = HistoryItem(
                    title,
                    timestamp,
                    lambda _: self._on_history_select(),
                    on_edit=self._on_edit_history,
                    on_delete=self._on_delete_history,
                )
                self.history_list.controls.append(item)

    def _on_history_select(self):
        pass

    def _on_edit_history(self, history_title):
        """编辑历史记录"""
        if not self.edit_alert:
            return

        def on_confirm(e):
            new_title = self.edit_alert.get_input_value()
            if new_title and new_title.strip():
                try:
                    DataManager().rename(history_title, new_title)
                    logger.info(f"重命名历史记录: {history_title} -> {new_title}")
                except ValueError:
                    self.edit_alert.set_message("无法重命名，请检查名称")

        self.edit_alert.set_input_value(history_title)
        self.edit_alert.clear_buttons()
        self.edit_alert.add_button("取消", lambda e: None, "normal")
        self.edit_alert.add_button("确认", on_confirm, "primary")
        self.edit_alert.show()

    def _on_delete_history(self, history_title):
        """删除历史记录"""
        if not self.delete_alert:
            return

        def on_confirm(e):
            DataManager().destroy(history_title)
            logger.warning(f"删除历史记录: {history_title}")

        self.delete_alert.clear_buttons()
        self.delete_alert.add_button("取消", lambda e: None, "normal")
        self.delete_alert.add_button("删除", on_confirm, "danger")
        self.delete_alert.show()

    def _on_clear_all(self):
        self.history_list.controls.clear()
        self.history_list.controls.append(self.empty_state)
        self.update()

    def search_history(self, query):
        pass
