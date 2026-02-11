import re
from typing import Any, List, Union

import flet as ft
from pydantic import BaseModel

from amrita_agent.config import AgentConfig, get_config, update_config
from amrita_agent.utils.render import BaseModelRender

from ..constants import MAIN_PADDING, ColorsEnum, FontSizesEnum


class SettingsArea(ft.Container):
    def __init__(self):
        super().__init__()
        self.bgcolor = ColorsEnum.bg_primary.value
        self.expand = True
        self.padding = MAIN_PADDING
        config_model = get_config()
        self.config_model = config_model
        
        # 使用BaseModelRender来渲染配置
        self.renderer = BaseModelRender()
        self.settings_control = self.renderer.render(config_model)

        buttons_row = ft.Row(
            controls=[
                ft.ElevatedButton(
                    text="保存设置",
                    bgcolor=ColorsEnum.accent_primary.value,
                    color=ColorsEnum.text_primary.value,
                    on_click=lambda _: self._on_save(),
                ),
                ft.ElevatedButton(
                    text="重置默认值",
                    bgcolor=ColorsEnum.bg_tertiary.value,
                    color=ColorsEnum.text_primary.value,
                    on_click=lambda _: self._on_reset(),
                ),
                ft.ElevatedButton(
                    text="从配置文件重载",
                    bgcolor=ColorsEnum.bg_tertiary.value,
                    color=ColorsEnum.text_primary.value,
                    on_click=lambda _: self._on_reload(),
                ),
            ],
            spacing=10,
        )

        self.content = ft.Column(
            controls=[
                ft.Text(
                    "设置",
                    size=FontSizesEnum.heading.value,
                    weight=ft.FontWeight.BOLD,
                    color=ColorsEnum.text_primary.value,
                ),
                ft.Column(
                    controls=[self.settings_control, buttons_row],
                    spacing=0,
                    scroll=ft.ScrollMode.AUTO,
                    expand=True,
                ),
            ],
            spacing=15,
            expand=True,
        )

    def _on_save(self):
        """保存设置"""
        values = self.renderer.get_values()
        config = AgentConfig.model_validate(values)
        update_config(config)

    def _on_reset(self):
        """重置为默认值"""
        from ..config import AgentConfig

        default_config = AgentConfig()
        # 重新渲染默认配置
        self.renderer = BaseModelRender()
        self.settings_control = self.renderer.render(default_config)

        buttons_row = ft.Row(
            controls=[
                ft.ElevatedButton(
                    text="保存设置",
                    bgcolor=ColorsEnum.accent_primary.value,
                    color=ColorsEnum.text_primary.value,
                    on_click=lambda _: self._on_save(),
                ),
                ft.ElevatedButton(
                    text="重置默认值",
                    bgcolor=ColorsEnum.bg_tertiary.value,
                    color=ColorsEnum.text_primary.value,
                    on_click=lambda _: self._on_reset(),
                ),
                ft.ElevatedButton(
                    text="从配置文件重载",
                    bgcolor=ColorsEnum.bg_tertiary.value,
                    color=ColorsEnum.text_primary.value,
                    on_click=lambda _: self._on_reload(),
                ),
            ],
            spacing=10,
        )

        # 重建 content
        if isinstance(self.content, ft.Column):
            main_column = self.content
            if len(main_column.controls) >= 2:
                # 替换设置控件，保留按钮行
                settings_and_buttons = main_column.controls[1]
                if isinstance(settings_and_buttons, ft.Column) and len(settings_and_buttons.controls) >= 2:
                    settings_and_buttons.controls[0] = self.settings_control  # 替换设置控件
                    # 重新渲染后需要更新
                    self.update()

    def _on_reload(self):
        """从配置文件重载设置"""
        from amrita_agent.config import get_config, reload_config

        reload_config()
        # 重新加载配置
        config = get_config()

        # 重新渲染配置
        self.renderer = BaseModelRender()
        self.settings_control = self.renderer.render(config)

        buttons_row = ft.Row(
            controls=[
                ft.ElevatedButton(
                    text="保存设置",
                    bgcolor=ColorsEnum.accent_primary.value,
                    color=ColorsEnum.text_primary.value,
                    on_click=lambda _: self._on_save(),
                ),
                ft.ElevatedButton(
                    text="重置默认值",
                    bgcolor=ColorsEnum.bg_tertiary.value,
                    color=ColorsEnum.text_primary.value,
                    on_click=lambda _: self._on_reset(),
                ),
                ft.ElevatedButton(
                    text="从配置文件重载",
                    bgcolor=ColorsEnum.bg_tertiary.value,
                    color=ColorsEnum.text_primary.value,
                    on_click=lambda _: self._on_reload(),
                ),
            ],
            spacing=10,
        )

        # 重建 content
        if isinstance(self.content, ft.Column):
            main_column = self.content
            if len(main_column.controls) >= 2:
                # 替换设置控件，保留按钮行
                settings_and_buttons = main_column.controls[1]
                if isinstance(settings_and_buttons, ft.Column) and len(settings_and_buttons.controls) >= 2:
                    settings_and_buttons.controls[0] = self.settings_control  # 替换设置控件
                    # 重新渲染后需要更新
                    self.update()

    def get_settings(self) -> dict[str, Any]:
        """获取所有设置值"""
        return self.renderer.get_values()
