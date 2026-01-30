import flet as ft
from enum import Enum


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
                    bgcolor=ft.Colors.BLUE_GREY if is_active else ft.Colors.BLACK54,
                    shape=ft.RoundedRectangleBorder(radius=18),
                    padding=18,
                ),
                content=ft.Icon(icon, size=28, color=ft.Colors.WHITE if is_active else ft.Colors.WHITE70),
            ),
        )

    def view(self):
        active = self.get_active()

        # We compare by string so it works even if caller uses Enum
        is_dash = str(active).endswith("DASHBOARD")
        is_set = str(active).endswith("SETTINGS")

        return ft.Container(
            width=90,
            bgcolor=ft.Colors.BLACK87,
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
                    bgcolor=ft.Colors.BLUE_GREY if active else ft.Colors.BLACK87,
                    padding=ft.padding.symmetric(vertical=14),
                ),
                content=ft.Text(text, text_align=ft.TextAlign.CENTER),
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
            (stage_enum.STERILIZATION, "Sterilization"),
        ]

        return ft.Container(
            width=220,
            bgcolor=ft.Colors.with_opacity(0.55, ft.Colors.BLACK87),
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
