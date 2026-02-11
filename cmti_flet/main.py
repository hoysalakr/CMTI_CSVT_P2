import flet as ft

try:
    from .app import CmtiApp  # When executed via `python -m cmti_flet.main`
except ImportError:
    from app import CmtiApp  # When running `python cmti_flet\main.py`


def main(page: ft.Page):
    page.title = "CMTI GUI"
    page.theme_mode = ft.ThemeMode.DARK
    page.window_min_width = 1100
    page.window_min_height = 650
    # Try to start as large as possible on a typical HD screen
    page.window_width = 1920
    page.window_height = 1080
    page.window_maximized = True
    page.window_full_screen = True
    page.padding = 0

    CmtiApp(page).mount()


ft.run(main)
