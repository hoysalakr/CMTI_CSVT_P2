import flet as ft


class PlaceholderStage:
    def __init__(self, title: str):
        self.title = title

    def view(self) -> ft.Control:
        return ft.Container(
            expand=True,
            alignment=ft.alignment.Alignment(0, 0),
            content=ft.Text(self.title, size=18, color=ft.Colors.WHITE70, text_align=ft.TextAlign.CENTER),
        )
