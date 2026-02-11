import html
import re
from html.parser import HTMLParser
from typing import cast

import flet as ft
import markdown
from amrita_core import PresetManager

from ..constants import MAIN_PADDING, ColorsEnum, FontSizesEnum
from ..utils.alert import AlertDialog


class MarkdownHTMLParser(HTMLParser):
    """高级 HTML 解析器，将 HTML 转换为 Flet 控件"""

    def __init__(self):
        super().__init__()
        self.controls: list[ft.Control] = []
        self.current_text = ""
        self.current_bold = False
        self.current_italic = False
        self.current_code = False
        self.current_list_items: list[str] = []
        self.in_list = False
        self.in_code_block = False
        self.code_language = ""
        self.code_content = ""

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag == "strong" or tag == "b":
            self.current_bold = True
        elif tag == "em" or tag == "i":
            self.current_italic = True
        elif tag == "code":
            self.current_code = True
        elif tag == "pre":
            self.in_code_block = True
            # 获取代码语言
            for attr, value in attrs:
                if attr == "class":
                    match = re.search(r"language-(\w+)", value or "")
                    if match:
                        self.code_language = match.group(1)
        elif tag == "ul" or tag == "ol":
            self.in_list = True
        elif tag == "li":
            pass  # 处理列表项在文本处理中
        elif tag == "br":
            self.current_text += "\n"

    def handle_endtag(self, tag: str) -> None:
        if tag == "strong" or tag == "b":
            self.current_bold = False
        elif tag == "em" or tag == "i":
            self.current_italic = False
        elif tag == "code":
            self.current_code = False
        elif tag == "pre":
            self.in_code_block = False
            if self.code_content.strip():
                self._add_code_block(self.code_content, self.code_language)
            self.code_content = ""
            self.code_language = ""
        elif tag == "p":
            if self.current_text.strip():
                self._add_text_control()
        elif tag == "ul" or tag == "ol":
            self.in_list = False
            if self.current_list_items:
                self._add_list_control()
        elif tag == "li":
            if self.current_text.strip():
                self.current_list_items.append(self.current_text.strip())
                self.current_text = ""

    def handle_data(self, data: str) -> None:
        if self.in_code_block:
            self.code_content += data
        else:
            decoded_data = html.unescape(data)
            self.current_text += decoded_data

    def _add_text_control(self) -> None:
        if not self.current_text.strip():
            return

        text = self.current_text.strip()
        weight = ft.FontWeight.BOLD if self.current_bold else ft.FontWeight.NORMAL

        text_control = ft.Text(
            text,
            color=ColorsEnum.text_primary.value,
            size=FontSizesEnum.body.value,
            selectable=True,
            weight=weight,
            italic=self.current_italic,
        )

        self.controls.append(text_control)
        self.current_text = ""

    def _add_code_block(self, code: str, language: str = "") -> None:
        code_text = html.unescape(code).strip()
        if not code_text:
            return

        # 创建代码块容器
        code_container = ft.Container(
            content=ft.Text(
                code_text,
                color=ColorsEnum.text_primary.value,
                size=FontSizesEnum.body.value,
                selectable=True,
                font_family="Courier New",
                no_wrap=False,
            ),
            bgcolor=ColorsEnum.bg_tertiary.value,
            padding=12,
            border_radius=ft.border_radius.all(6),
        )

        self.controls.append(code_container)

    def _add_list_control(self) -> None:
        if not self.current_list_items:
            return

        list_controls = []
        for item in self.current_list_items:
            item_row = ft.Row(
                controls=[
                    ft.Text("•", size=FontSizesEnum.body.value),
                    ft.Text(
                        item,
                        color=ColorsEnum.text_primary.value,
                        size=FontSizesEnum.body.value,
                        selectable=True,
                        expand=True,
                    ),
                ],
                spacing=8,
            )
            list_controls.append(item_row)

        list_column = ft.Column(
            controls=list_controls,
            spacing=4,
        )

        self.controls.append(list_column)
        self.current_list_items = []


def markdown_to_flet_controls(text: str) -> list[ft.Control]:
    """使用 HTMLParser 将 Markdown 完整渲染为 Flet 控件"""
    # 转换 Markdown 为 HTML
    html_content = markdown.markdown(
        text,
        extensions=[
            "tables",
            "fenced_code",
            "nl2br",
            "sane_lists",
        ],
    )

    # 使用自定义解析器解析 HTML
    parser = MarkdownHTMLParser()
    parser.feed(html_content)

    # 如果没有生成任何控件，返回原始文本
    if not parser.controls:
        parser.controls.append(
            ft.Text(
                text,
                color=ColorsEnum.text_primary.value,
                size=FontSizesEnum.body.value,
                selectable=True,
            )
        )

    return parser.controls


class MessageBubble(ft.Container):
    def __init__(self, text, is_user=True):
        super().__init__()
        self.is_user = is_user
        self.padding = ft.padding.symmetric(horizontal=12, vertical=10)
        self.border_radius = ft.border_radius.all(12)
        self.bgcolor = (
            ColorsEnum.input_bg.value if is_user else ColorsEnum.bg_tertiary.value
        )
        self.alignment = ft.alignment.center_left

        # 使用 Markdown 渲染
        if not is_user:
            controls = markdown_to_flet_controls(text)
        else:
            controls = [ft.Text(text)]
        self.content: ft.Column = ft.Column(
            controls=controls,
            spacing=8,
        )


class ChatArea(ft.Container):
    _last_bubble: MessageBubble
    _edit_alert: AlertDialog

    def __init__(self, alert: AlertDialog):
        self._edit_alert = alert
        super().__init__()
        self.bgcolor = ColorsEnum.bg_primary.value
        self.expand = True
        self.padding = MAIN_PADDING

        self.messages_container = ft.Column(
            spacing=12,
            scroll=ft.ScrollMode.AUTO,
            expand=True,
        )

        self.model_selector = ft.Dropdown(
            label="预设",
            options=[ft.dropdown.Option(model) for model in self._get_models()],
            value="default",
            bgcolor=ColorsEnum.input_bg.value,
            color=ColorsEnum.text_primary.value,
            label_style=ft.TextStyle(color=ColorsEnum.text_secondary.value),
            width=180,
        )

        self.input_field = ft.TextField(
            label="输入消息",
            multiline=True,
            min_lines=1,
            bgcolor=ColorsEnum.input_bg.value,
            color=ColorsEnum.text_primary.value,
            label_style=ft.TextStyle(color=ColorsEnum.text_secondary.value),
            border_color=ColorsEnum.input_border.value,
            focused_border_color=ColorsEnum.accent_primary.value,
            expand=True,
        )

        self.send_button = ft.IconButton(
            icon="send",
            icon_color=ColorsEnum.text_primary.value,
            bgcolor=ColorsEnum.accent_primary.value,
        )

        input_row = ft.Row(
            controls=[
                self.model_selector,
                self.input_field,
                self.send_button,
            ],
            spacing=10,
            vertical_alignment=ft.CrossAxisAlignment.END,
        )

        self.content = ft.Column(
            controls=[
                ft.Container(
                    content=ft.Text(
                        "新的对话",
                        size=FontSizesEnum.heading.value,
                        weight=ft.FontWeight.BOLD,
                        color=ColorsEnum.text_primary.value,
                    ),
                    padding=ft.padding.only(bottom=15),
                    border=ft.border.only(
                        bottom=ft.border.BorderSide(1, ColorsEnum.divider.value)
                    ),
                ),
                self.messages_container,
                input_row,
            ],
            spacing=12,
            expand=True,
        )

    def _get_models(self):
        return [i.name for i in PresetManager().get_all_presets()]

    def add_message(self, text, is_user=True):
        self._last_bubble = bubble = MessageBubble(text, is_user)

        def copy_bubble(e):
            nonlocal bubble
            assert self.page is not None
            self.page.set_clipboard(text)

        def edit_bubble(e):
            nonlocal self, text
            # 检查是否是最后一条用户消息
            last_user_msg_idx = -1
            msg_row = None
            actual_bubble = None

            for i in range(len(self.messages_container.controls) - 1, -1, -1):
                current_msg_row = self.messages_container.controls[i]
                if isinstance(current_msg_row, ft.Row):
                    # 获取气泡控件
                    bubble_col = (
                        current_msg_row.controls[0]
                        if current_msg_row.controls
                        else None
                    )
                    if (
                        bubble_col
                        and isinstance(bubble_col, ft.Column)
                        and len(bubble_col.controls) > 0
                    ):
                        container_with_bubble = bubble_col.controls[0]

                        # 检查container是否具有content属性且是MessageBubble类型
                        if hasattr(container_with_bubble, "content"):
                            content_control = getattr(container_with_bubble, "content")

                            # 确保content_control是我们自定义的MessageBubble
                            if hasattr(content_control, "is_user"):
                                current_bubble = content_control
                                if current_bubble.is_user:
                                    last_user_msg_idx = i
                                    msg_row = current_msg_row
                                    actual_bubble = current_bubble
                                    break

            # 只有当点击的是最后一条用户消息时才允许编辑
            if (
                msg_row is None
                or actual_bubble is None
                or self.messages_container.controls.index(msg_row) != last_user_msg_idx
            ):
                print("Only the last user message can be edited")
                return

            # 获取当前文本
            current_text = self._extract_text_from_bubble(actual_bubble)

            def on_confirm(e):
                nonlocal self, text
                new_text = self._edit_alert.get_input_value()
                self._edit_alert.input_field.multiline = None
                self._edit_alert.input_field.max_lines = 1
                self._edit_alert.input_field.min_lines = 1
                if new_text and new_text.strip():
                    text = new_text
                    # 更新气泡内容
                    self._update_bubble_content(actual_bubble, new_text)

                    # 检查下一条消息是否为AI消息，如果是则删除
                    current_index = self.messages_container.controls.index(msg_row)
                    if current_index + 1 < len(self.messages_container.controls):
                        next_row = self.messages_container.controls[current_index + 1]
                        if isinstance(next_row, ft.Row):
                            # 获取下一个气泡
                            next_bubble_col = (
                                next_row.controls[0] if next_row.controls else None
                            )
                            if (
                                next_bubble_col
                                and isinstance(next_bubble_col, ft.Column)
                                and len(next_bubble_col.controls) > 0
                            ):
                                next_container_with_bubble = next_bubble_col.controls[0]

                                # 检查next_container是否具有content属性
                                if hasattr(next_container_with_bubble, "content"):
                                    next_content_control = getattr(
                                        next_container_with_bubble, "content"
                                    )

                                    # 确保next_content_control是我们自定义的MessageBubble
                                    if hasattr(next_content_control, "is_user"):
                                        next_actual_bubble = next_content_control
                                        if not next_actual_bubble.is_user:
                                            # 删除下一条AI消息
                                            self.messages_container.controls.remove(
                                                next_row
                                            )

                    self.update()

            # 设置编辑对话框
            self._edit_alert.set_input_value(current_text)
            self._edit_alert.clear_buttons()
            self._edit_alert.set_title("编辑消息")
            self._edit_alert.set_message("编辑消息内容")
            self._edit_alert.set_input_label("消息内容")
            self._edit_alert.add_button("取消", lambda e: None, "normal")
            self._edit_alert.add_button("确认", on_confirm, "primary")
            self._edit_alert.input_field.multiline = True
            self._edit_alert.input_field.max_lines = None
            self._edit_alert.input_field.min_lines = None
            self._edit_alert.show()
            self._edit_alert.input_field.update()

        bubble = ft.Column(
            [
                ft.Container(bubble),
                ft.Row(
                    [
                        ft.IconButton(
                            "edit",
                            icon_size=15,
                            on_click=edit_bubble,
                        ),
                        ft.IconButton(
                            "copy",
                            icon_size=15,
                            on_click=copy_bubble,
                        ),
                    ]
                ),
            ],
        )
        row = ft.Row(
            controls=[bubble],
            alignment=ft.MainAxisAlignment.END
            if is_user
            else ft.MainAxisAlignment.START,
        )
        self.messages_container.controls.append(row)
        self.messages_container.scroll_to(offset=-1, duration=200)
        self.update()

    def _extract_text_from_bubble(self, bubble):
        """从气泡中提取文本内容"""
        texts = []

        def extract_from_controls(controls):
            for control in controls:
                if isinstance(control, ft.Text):
                    texts.append(control.value)
                elif hasattr(control, "controls") and control.controls:
                    extract_from_controls(control.controls)
                elif hasattr(control, "content") and control.content:
                    if (
                        hasattr(control.content, "controls")
                        and control.content.controls
                    ):
                        extract_from_controls(control.content.controls)

        extract_from_controls([bubble.content])
        return "\n".join(texts)

    def _update_bubble_content(self, bubble: MessageBubble, new_text: str):
        """更新气泡的内容"""
        # 重新生成气泡的控件
        new_controls = (
            markdown_to_flet_controls(new_text)
            if bubble.is_user
            else [ft.Text(new_text)]
        )

        # 清空现有控件
        bubble.content.controls.clear()
        # 添加新控件
        bubble.content.controls.extend(new_controls)

        # 更新界面
        bubble.update()

    def get_input_value(self):
        return self.input_field.value

    def clear_input(self):
        self.input_field.value = ""
        self.update()

    def get_selected_preset(self) -> str | None:
        return self.model_selector.value
