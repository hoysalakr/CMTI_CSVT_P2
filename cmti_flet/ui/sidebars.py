import flet as ft
from enum import Enum

from theme import (
    THEME_ACCENT,
    THEME_ACCENT_DARK,
    THEME_BORDER,
    THEME_CARD,
    THEME_SURFACE,
    THEME_SURFACE_MUTED,
    THEME_TEXT_PRIMARY,
    THEME_TEXT_SECONDARY,
)


class PrimarySidebar:
    def __init__(self, get_active, on_select):
        self.get_active = get_active
        self.on_select = on_select

    def _btn(self, icon, is_active, on_click):
        return ft.Container(
            padding=ft.padding.symmetric(horizontal=12, vertical=10),
            content=ft.ElevatedButton(
                on_click=on_click,
                style=ft.ButtonStyle(
                    bgcolor=THEME_ACCENT if is_active else THEME_SURFACE_MUTED,
                    overlay_color=THEME_ACCENT_DARK,
                    shape=ft.RoundedRectangleBorder(radius=18),
                    padding=18,
                ),
                content=ft.Icon(icon, size=28, color="black" if is_active else THEME_TEXT_SECONDARY),
            ),
        )

    def view(self):
        active = self.get_active()

        # We compare by string so it works even if caller uses Enum
        is_dash = str(active).endswith("DASHBOARD")
        is_set = str(active).endswith("SETTINGS")

        return ft.Container(
            width=90,
            bgcolor=THEME_SURFACE,
            content=ft.Column(
                controls=[
                    ft.Container(height=18),
                    self._btn(ft.Icons.DASHBOARD_ROUNDED, is_dash, lambda e: self.on_select(active.__class__.DASHBOARD)),
                    self._btn(ft.Icons.SETTINGS_ROUNDED, is_set, lambda e: self.on_select(active.__class__.SETTINGS)),
                ]
            ),
        )


class StageSidebar:
    def __init__(self, get_active, on_select):
        self.get_active = get_active
        self.on_select = on_select

    def _stage_btn(self, text, active, on_click):
        return ft.Container(
            padding=ft.padding.symmetric(horizontal=10, vertical=6),
            content=ft.ElevatedButton(
                on_click=on_click,
                style=ft.ButtonStyle(
                    bgcolor=THEME_ACCENT if active else THEME_SURFACE_MUTED,
                    overlay_color=THEME_ACCENT_DARK,
                    padding=ft.padding.symmetric(vertical=14),
                    text_style=ft.TextStyle(color="black" if active else THEME_TEXT_PRIMARY),
                ),
                content=ft.Text(text, text_align=ft.TextAlign.CENTER, color="black" if active else THEME_TEXT_PRIMARY),
            ),
        )

    def view(self):
        active = self.get_active()
        stage_enum = active.__class__

        items = [
            (stage_enum.DISPENSER, "Dispenser"),
            (stage_enum.VACUUM, "Vacuum"),
            (stage_enum.HEATING, "Heating"),
            (stage_enum.PACKAGING, "Packaging"),
            (stage_enum.STERILIZATION_ACETONE, "Sterilization (Acetone)"),
            (stage_enum.STERILIZATION_UV, "Sterilization (UV)"),
        ]

        return ft.Container(
            width=220,
            bgcolor=THEME_SURFACE,
            border=ft.border.only(left=ft.BorderSide(1, THEME_BORDER)),
            content=ft.Column(
                controls=[
                    ft.Container(height=25),
                    *[
                        self._stage_btn(
                            label,
                            active == st,
                            (lambda s=st: (lambda e: self.on_select(s)))(),
                        )
                        for st, label in items
                    ],
                ]
            ),
        )
