import flet as ft

from theme import THEME_SURFACE, THEME_TEXT_SECONDARY


class PlaceholderStage:
    def __init__(self, title: str):
        self.title = title

    def view(self) -> ft.Control:
        return ft.Container(
            expand=True,
            bgcolor=THEME_SURFACE,
            alignment=ft.alignment.Alignment(0, 0),
            content=ft.Text(self.title, size=18, color=THEME_TEXT_SECONDARY, text_align=ft.TextAlign.CENTER),
        )
