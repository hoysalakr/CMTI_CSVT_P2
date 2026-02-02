import flet as ft
from app import CmtiApp


def main(page: ft.Page):
    page.title = "CMTI GUI"
    page.theme_mode = ft.ThemeMode.DARK
    page.window_min_width = 1100
    page.window_min_height = 650
    page.padding = 0

    CmtiApp(page).mount()


ft.run(main)
