import threading
import time
from collections.abc import Callable
from typing import Any

import flet as ft

from ..constants import ColorsEnum, FontSizesEnum


class AlertDialog(ft.Container):
    """带有动画的警告弹窗"""

    def __init__(
        self,
        title: str = "确认",
        message: str = "",
        input_field: bool = False,  # 是否显示输入框
    ):
        super().__init__()
        self.title_text = title
        self.message_text = message
        self.on_close_callback = None

        # 背景虚化层
        self.blur_background = ft.Container(
            expand=True,
            bgcolor="#000000",
            opacity=0,
            animate_opacity=300,
            on_click=self._on_background_click,
        )

        # 标题
        self.title_control = ft.Text(
            title,
            size=FontSizesEnum.title.value,
            weight=ft.FontWeight.BOLD,
            color=ColorsEnum.text_primary.value,
        )

        # 消息
        self.message_control = ft.Text(
            message,
            size=FontSizesEnum.body.value,
            color=ColorsEnum.text_secondary.value,
            selectable=True,
        )

        # 输入框（用于编辑对话）
        self.input_field = ft.TextField(
            label="对话标题",
            label_style=ft.TextStyle(color=ColorsEnum.text_secondary.value),
            text_style=ft.TextStyle(color=ColorsEnum.text_primary.value),
            bgcolor=ColorsEnum.bg_tertiary.value,
            border_color=ColorsEnum.accent_primary.value,
            focused_border_color=ColorsEnum.accent_primary.value,
            min_lines=1,
            max_lines=1,
        )

        # 对话框主体内容
        dialog_controls = [
            self.title_control,
            ft.Divider(height=10, color="transparent"),
            self.message_control,
        ]

        if input_field:
            dialog_controls.extend(
                [
                    ft.Divider(height=10, color="transparent"),
                    self.input_field,
                ]
            )

        # 按钮行
        self.button_row = ft.Row(
            controls=[],
            alignment=ft.MainAxisAlignment.END,
            spacing=10,
        )

        dialog_controls.extend(
            [
                ft.Divider(height=10, color="transparent"),
                self.button_row,
            ]
        )

        # 对话框内容 - 限制最大高度和宽度
        self.dialog_content = ft.Container(
            content=ft.Column(
                controls=dialog_controls,
                spacing=10,
            ),
            padding=20,
            bgcolor=ColorsEnum.bg_secondary.value,
            border_radius=ft.border_radius.all(12),
            width=450,
            height=500,  # 限制最大高度
            shadow=ft.BoxShadow(
                blur_radius=20,
                color="#00000044",
            ),
            opacity=0,
            scale=0.8,
            animate_opacity=300,
            animate_scale=300,
        )

        # 使用 Stack 将虚化层和对话框叠放，并居中
        self.content = ft.Stack(
            controls=[
                self.blur_background,
                ft.Container(
                    content=self.dialog_content,
                    alignment=ft.alignment.center,
                    expand=True,
                ),
            ],
            expand=True,
        )

        self.expand = True
        self.visible = False

    def set_title(self, title: str):
        """设置标题"""
        self.title_text = title
        self.title_control.value = title
        self.title_control.update()

    def set_message(self, message: str):
        """设置消息"""
        self.message_text = message
        self.message_control.value = message
        self.message_control.update()

    def set_input_value(self, value: str):
        """设置输入框的值"""
        self.input_field.value = value
        self.input_field.update()

    def set_input_label(self, value: str):
        self.input_field.label = value
        self.input_field.update()

    def get_input_value(self) -> str:
        """获取输入框的值"""
        return self.input_field.value or ""

    def add_button(
        self,
        text: str,
        callback: Callable[[Any], Any] | None = None,
        btn_type: str = "normal",
    ):
        """添加按钮"""
        btn_style = None
        if btn_type == "primary":
            btn_style = ft.ButtonStyle(
                bgcolor=ColorsEnum.accent_primary.value,
                color=ColorsEnum.text_primary.value,
            )
        elif btn_type == "danger":
            btn_style = ft.ButtonStyle(
                bgcolor="#ef4444",
                color=ColorsEnum.text_primary.value,
            )

        btn = ft.ElevatedButton(
            text=text,
            style=btn_style,
            on_click=lambda e: self._on_button_click(callback, e),
        )
        self.button_row.controls.append(btn)
        self.button_row.update()

    def clear_buttons(self):
        """清除所有按钮"""
        self.button_row.controls.clear()
        self.button_row.update()

    def show(self):
        """显示对话框，带动画"""
        self.visible = True
        self.blur_background.opacity = 0.5
        self.dialog_content.opacity = 1
        self.dialog_content.scale = 1.0
        self.update()

    def close(self):
        """关闭对话框，带动画"""
        self.blur_background.opacity = 0
        self.dialog_content.opacity = 0
        self.dialog_content.scale = 0.8
        self.update()

        # 延迟隐藏以完成动画
        def hide():
            self.visible = False
            self.update()
            if self.on_close_callback:
                self.on_close_callback()

        threading.Thread(target=hide, daemon=True).start()

    def _on_button_click(self, callback: Callable[[Any], Any] | None, e):
        """按钮点击事件"""
        if callback:
            callback(e)
        self.close()

    def _on_background_click(self, e):
        """点击虚化背景关闭（可选）"""
        # 如果想要点击背景关闭，取消注释下一行
        # self.close()
        pass
