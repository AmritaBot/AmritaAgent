import flet as ft
class LoadingPage(ft.Container):
    _process_text = ft.Text(
                    "正在初始化",
                    size=8,
                    weight=ft.FontWeight.W_500,
                )
    def __init__(self):
        super().__init__()
        self.content = self.build_controls()
        self.alignment=ft.alignment.center
        self.expand=True
    def apply_to_page(self,page:ft.Page):
        self.page = page
        page.clean(

        )
        page.add(self)
        page.update()
    def build_controls(self) -> ft.Column:
        return ft.Column(
            [
                ft.ProgressRing(width=32, height=32, stroke_width=3),
                ft.Text(
                    "正在加载 Amrita Agent...",
                    size=16,
                    weight=ft.FontWeight.W_500,
                ),
                self._process_text
            ],
            alignment=ft.MainAxisAlignment.CENTER,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        )
        