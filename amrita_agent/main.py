import asyncio

import amrita_core
import flet as ft

from amrita_agent.utils.chat import (
    DataManager,
)

from .config import apply_config
from .app_view import AppView
from .pages.loading import LoadingPage


def set_head(page: ft.Page, message: str):
    page.title = f"Amrita Agent - {message}" if message else "Amrita Agent"
    amrita_core.logger.info(message)
    page.update()


async def main_async(page: ft.Page):
    global app
    page.title = "Amrita Agent"
    title = page.title
    page.window.width = 1200
    page.window.height = 800
    page.window.min_width = 800
    page.window.min_height = 600
    page.title = f"{title} - Loading..."
    ld = LoadingPage()
    ld.apply_to_page(page)
    await asyncio.sleep(1)
    set_head(page, "正在初始化Core...")
    amrita_core.init()
    set_head(page, "正在初始化配置...")
    apply_config()
    set_head(page, "正在初始化Core服务...")
    await amrita_core.load_amrita()
    set_head(page, "正在初始化记忆与模型")
    DataManager().loads()
    page.title = title
    page.clean()
    app = AppView(page)
    page.add(app)
    page.update()


ft.app(main_async)
