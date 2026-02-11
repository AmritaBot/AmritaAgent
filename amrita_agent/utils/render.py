import re
from typing import Any

import flet as ft
from pydantic import BaseModel
from pydantic.fields import FieldInfo

from ..constants import ColorsEnum, FontSizesEnum


def parse_ui_config(description: str) -> tuple[str, dict[str, Any]]:
    """从description中解析@ui指令

    返回 (清理后的description, ui配置字典)
    支持: @ui[slider,min,max] 等格式
    """
    ui_config: dict[str, Any] = {}
    cleaned_description = description

    if not description:
        return cleaned_description, ui_config

    # 匹配 @ui[type,param1,param2,...] 格式
    pattern = r"@ui\[([^\]]+)\]"
    matches = re.findall(pattern, description)

    for match in matches:
        parts = match.split(",")
        if len(parts) > 0:
            ui_type = parts[0].strip()

            if ui_type == "slider" and len(parts) >= 3:
                try:
                    min_val = float(parts[1].strip())
                    max_val = float(parts[2].strip())
                    ui_config["slider"] = {"min": min_val, "max": max_val}
                except ValueError:
                    pass

    # 移除所有 @ui[...] 指令
    cleaned_description = re.sub(pattern, "", description).strip()

    return cleaned_description, ui_config


def create_control_for_field(
    field_type: type | None, field_info: FieldInfo | None, current_value: Any = None
) -> ft.Control:
    """根据字段类型创建相应的 UI 控件"""

    # 获取默认值
    default_value = current_value
    assert field_info
    if default_value is None:
        if field_info.default:
            default_value = field_info.default
        elif field_info.default_factory:
            default_value = field_info.default_factory()  # type: ignore

    # 解析 description 中的 @ui 指令
    description = field_info.description or ""
    clean_description, ui_config = parse_ui_config(description)

    # 检查是否为 List 类型
    if (
        field_type is not None
        and hasattr(field_type, "__origin__")
        and field_type.__origin__ is list
    ):
        # 获取列表元素的类型
        list_item_type = field_type.__args__[0] if field_type.__args__ else str

        # 创建列表编辑控件
        return create_list_control(list_item_type, default_value or [])

    # 处理 bool 类型
    if field_type is bool:
        return ft.Switch(
            value=bool(default_value) if default_value is not None else False,
            thumb_color=ColorsEnum.accent_primary.value,
        )

    # 处理 float 类型（温度等滑块）
    if field_type is float:
        slider_config = ui_config.get("slider", {})
        min_val = slider_config.get("min", 0)
        max_val = slider_config.get("max", 2)

        return ft.Slider(
            min=min_val,
            max=max_val,
            divisions=20,
            value=float(default_value or 0.7),
            width=200,
        )

    # 处理 int 类型
    if field_type is int:
        slider_config = ui_config.get("slider", {})
        # 如果有 slider 配置，使用 Slider 而不是 TextField
        if slider_config:
            min_val = int(slider_config.get("min", 0))
            max_val = int(slider_config.get("max", 100))
            return ft.Slider(
                min=min_val,
                max=max_val,
                divisions=max_val - min_val,
                value=float(default_value or min_val),
                width=200,
            )

        return ft.TextField(
            label="数值",
            value=str(default_value or 0),
            width=150,
            bgcolor=ColorsEnum.input_bg.value,
            color=ColorsEnum.text_primary.value,
            label_style=ft.TextStyle(color=ColorsEnum.text_secondary.value),
            border_color=ColorsEnum.input_border.value,
        )

    # 处理 str 类型（默认为文本输入）
    if field_type is str:
        # 检查字段描述中是否有 password 标记
        is_password = "password" in clean_description.lower()

        return ft.TextField(
            label="文本",
            value=str(default_value or ""),
            password=is_password,
            bgcolor=ColorsEnum.input_bg.value,
            color=ColorsEnum.text_primary.value,
            label_style=ft.TextStyle(color=ColorsEnum.text_secondary.value),
            border_color=ColorsEnum.input_border.value,
            expand=True,
        )

    # 默认为文本输入框
    return ft.TextField(
        label="值",
        value=str(default_value or ""),
        bgcolor=ColorsEnum.input_bg.value,
        color=ColorsEnum.text_primary.value,
        label_style=ft.TextStyle(color=ColorsEnum.text_secondary.value),
        border_color=ColorsEnum.input_border.value,
    )


def create_list_control(item_type: type, values: list) -> ft.Control:
    """创建列表编辑控件"""
    # 列表容器
    list_items = ft.Column(scroll=ft.ScrollMode.AUTO, spacing=5)

    # 创建输入控件
    input_field = ft.TextField(
        hint_text=f"输入{item_type.__name__}值",
        bgcolor=ColorsEnum.input_bg.value,
        color=ColorsEnum.text_primary.value,
        label_style=ft.TextStyle(color=ColorsEnum.text_secondary.value),
        border_color=ColorsEnum.input_border.value,
    )

    # 添加按钮
    add_btn = ft.ElevatedButton(
        text="添加",
        icon=ft.Icons.ADD,
        on_click=lambda _: add_list_item(item_type, input_field, list_items),
    )

    # 初始化现有项
    for i, value in enumerate(values):
        add_list_item_to_container(item_type, list_items, str(value), i)

    return ft.Column([list_items, ft.Row([input_field, add_btn], spacing=5)], spacing=5)


def add_list_item(item_type: type, input_field: ft.TextField, list_items: ft.Column):
    """添加列表项"""
    value_str = input_field.value
    if not value_str:
        return

    # 尝试转换值到指定类型
    try:
        if item_type is str:
            converted_value = value_str
        elif item_type is int:
            converted_value = int(value_str)
        elif item_type is float:
            converted_value = float(value_str)
        elif item_type is bool:
            converted_value = value_str.lower() in ["true", "1", "yes", "on"]
        else:
            converted_value = value_str  # 默认为字符串

        # 添加新项到列表
        index = len(list_items.controls)
        add_list_item_to_container(item_type, list_items, str(converted_value), index)
        input_field.value = ""  # 清空输入框
        list_items.update()  # 更新列表
    except ValueError:
        pass


def add_list_item_to_container(
    item_type: type, container: ft.Column, value: str, index: int
):
    """向容器添加列表项控件"""
    row = ft.Row(
        controls=[
            ft.Text(str(value), expand=True),
            ft.IconButton(
                icon=ft.Icons.DELETE,
                on_click=lambda _: remove_list_item(container, row),
            ),
        ],
        spacing=5,
    )
    container.controls.append(row)
    container.update()


def remove_list_item(container: ft.Column, item_row):
    """从列表中移除项"""
    container.controls.remove(item_row)
    container.update()


class SettingItem(ft.Container):
    def __init__(self, label, description, control):
        super().__init__()
        self.padding = ft.padding.symmetric(horizontal=15, vertical=12)
        self.bgcolor = ColorsEnum.bg_tertiary.value
        self.border_radius = ft.border_radius.all(8)
        self.margin = ft.margin.symmetric(vertical=5)

        self.content = ft.Column(
            controls=[
                ft.Row(
                    controls=[
                        ft.Text(
                            label,
                            size=FontSizesEnum.body.value,
                            color=ColorsEnum.text_primary.value,
                            weight=ft.FontWeight.BOLD,
                        ),
                        ft.Container(expand=True),
                        control,
                    ],
                    spacing=10,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                ),
                ft.Text(
                    description,
                    size=FontSizesEnum.small.value,
                    color=ColorsEnum.text_secondary.value,
                    italic=True,
                ),
            ],
            spacing=5,
        )


class SettingsSection(ft.Container):
    def __init__(self, title, children):
        super().__init__()
        self.margin = ft.margin.symmetric(vertical=15)

        self.content = ft.Column(
            controls=[
                ft.Text(
                    title,
                    size=FontSizesEnum.title.value,
                    color=ColorsEnum.text_primary.value,
                    weight=ft.FontWeight.BOLD,
                ),
                ft.Container(height=1, bgcolor=ColorsEnum.divider.value),
                *children,
            ],
            spacing=0,
        )


class BaseModelRender:
    def __init__(self):
        self.field_controls: dict[str, ft.Control] = {}

    def render(self, model_instance: BaseModel) -> ft.Control:
        """将BaseModel实例渲染为Flet控件"""
        model_type = type(model_instance)
        sections = self._build_sections_from_model(model_type, model_instance)
        
        return ft.Column(controls=sections, expand=True)

    def _build_sections_from_model(self, model_class, config_instance=None) -> list[ft.Control]:
        """从 Pydantic 模型构建设置部分"""
        sections = []
        model_fields = model_class.model_fields

        if config_instance is not None:
            current_config = config_instance
        else:
            current_config = model_class()

        # 处理嵌套字段
        for field_name, field_info in model_fields.items():
            field_type = field_info.annotation
            current_value = (
                getattr(current_config, field_name, None) if current_config else None
            )

            # 检查字段是否是嵌套的 BaseModel（支持一层嵌套）
            try:
                if isinstance(field_type, type) and issubclass(field_type, BaseModel):
                    # 这是一个嵌套模型，创建一个分组部分
                    nested_items = self._build_items_from_model(
                        field_type, current_value
                    )
                    if nested_items:
                        section = SettingsSection(
                            field_info.title or field_name, nested_items
                        )
                        sections.append(section)
            except (TypeError, AttributeError):
                pass

        # 处理普通字段
        regular_fields = []
        for field_name, field_info in model_fields.items():
            field_type = field_info.annotation
            current_value = (
                getattr(current_config, field_name, None) if current_config else None
            )

            try:
                if isinstance(field_type, type) and issubclass(field_type, BaseModel):
                    continue  # 已处理过的嵌套模型
            except (TypeError, AttributeError):
                pass

            control = create_control_for_field(field_type, field_info, current_value)
            self.field_controls[field_name] = control

            # 清理 description 中的 @ui 指令
            description = field_info.description or ""
            clean_description, _ = parse_ui_config(description)

            item = SettingItem(
                field_info.title or field_name,
                clean_description,
                control,
            )
            regular_fields.append(item)

        # 如果有常规字段，添加一个通用设置部分
        if regular_fields:
            sections.append(SettingsSection("通用设置", regular_fields))

        return sections

    def _build_items_from_model(
        self, model_class: type[BaseModel], current_instance: BaseModel | None = None
    ) -> list[ft.Control]:
        """从嵌套的 Pydantic 模型构建设置项"""
        items = []
        model_fields = model_class.model_fields

        for field_name, field_info in model_fields.items():
            field_type = field_info.annotation
            current_value = (
                getattr(current_instance, field_name, None)
                if current_instance
                else None
            )

            control = create_control_for_field(field_type, field_info, current_value)
            # 使用嵌套路径作为 key
            full_field_name = f"{model_class.__name__}.{field_name}"
            self.field_controls[full_field_name] = control

            # 清理 description 中的 @ui 指令
            description = field_info.description or ""
            clean_description, _ = parse_ui_config(description)

            item = SettingItem(
                field_info.title or field_name,
                clean_description,
                control,
            )
            items.append(item)

        return items

    def get_values(self) -> dict[str, Any]:
        """获取所有控件的值"""
        settings = {}
        for field_name, control in self.field_controls.items():
            # 特殊处理列表控件
            if (
                isinstance(control, ft.Column)
                and len(control.controls) >= 2
                and hasattr(control.controls[0], "controls")
            ):
                # 这是一个列表控件，提取其中的值
                list_items_column = control.controls[0]
                values = []

                for list_row in list_items_column.controls:
                    if isinstance(list_row, ft.Row) and len(list_row.controls) >= 1:
                        text_control = list_row.controls[0]
                        if isinstance(text_control, ft.Text):
                            values.append(text_control.value)

                value = values
            elif isinstance(control, ft.Slider):
                value = control.value
            elif isinstance(control, ft.Switch):
                value = control.value
            elif isinstance(control, ft.TextField):
                value = control.value
            else:
                value = None

            # 处理嵌套字段的情况 (例如: "ModelName.fieldName")
            if "." in field_name:
                # 嵌套字段，需要重构回嵌套结构
                model_name, field_name_part = field_name.split(".", 1)
                if model_name not in settings:
                    settings[model_name] = {}
                settings[model_name][field_name_part] = value
            else:
                # 普通字段
                settings[field_name] = value
        return settings