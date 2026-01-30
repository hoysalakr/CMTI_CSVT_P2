import sys
import os
from stages.vacuum import VacuumStage

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import flet as ft
from enum import Enum

from ui.sidebars import PrimarySidebar, StageSidebar
from stages.dispenser import DispenserStage
from stages.placeholder import PlaceholderStage


class Stage(Enum):
    DISPENSER = "Dispenser"
    VACUUM = "Vacuum"
    HEATING = "Heating"
    PACKAGING = "Packaging"
    STERILIZATION = "Sterilization"


class TopSection(Enum):
    DASHBOARD = "Dashboard"
    SETTINGS = "Settings"


class CmtiApp:
    def __init__(self, page: ft.Page):
        self.page = page

        self.section = TopSection.SETTINGS
        self.stage = Stage.DISPENSER
        self.auto_mode = False  # False=Manual, True=Auto

        # Main containers
        self.primary_sidebar = PrimarySidebar(
            get_active=lambda: self.section,
            on_select=self._on_section_select,
        )

        self.stage_sidebar = StageSidebar(
            get_active=lambda: self.stage,
            on_select=self._on_stage_select,
        )

        self.header_title = ft.Text("", size=26, weight=ft.FontWeight.BOLD)
        self.mode_text = ft.Text("", size=14, weight=ft.FontWeight.W_600)
        self.mode_switch = ft.Switch(value=self.auto_mode, on_change=self._on_mode_toggle)

        self.body_holder = ft.Container(expand=True)

        self.root = ft.Row(
            expand=True,
            spacing=0,
            controls=[],
        )

        self.dispenser_stage = DispenserStage(
            auto_mode=self.auto_mode,
            snack=self._snack,
            on_request_error=self._handle_stage_error,
        )

    def mount(self):
        self.page.add(self.root)
        self._render()

    # ---------- callbacks ----------
    def _on_section_select(self, section: TopSection):
        self.section = section
        self._render()

    def _on_stage_select(self, stage: Stage):
        self.stage = stage
        self._render()

    def _on_mode_toggle(self, e):
        self.auto_mode = bool(e.control.value)
        self.dispenser_stage.auto_mode = self.auto_mode
        self._render()

    # ---------- render helpers ----------
    def _build_header(self, title: str) -> ft.Control:
        self.header_title.value = title

        self.mode_text.value = "AUTO" if self.auto_mode else "MANUAL"
        self.mode_text.color = ft.Colors.GREEN_ACCENT if self.auto_mode else ft.Colors.WHITE70

        self.mode_switch.value = self.auto_mode

        return ft.Row(
            controls=[
                self.header_title,
                ft.Container(expand=True),
                self.mode_text,
                ft.Container(width=10),
                self.mode_switch,
            ]
        )

    def _build_dashboard_page(self) -> ft.Control:
        return ft.Container(
            expand=True,
            bgcolor=ft.Colors.BLACK87,
            padding=24,
            content=ft.Column(
                alignment=ft.MainAxisAlignment.CENTER,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                controls=[
                    ft.Text(
                        "DASHBOARD PAGE\n(add sensors + status later)",
                        text_align=ft.TextAlign.CENTER,
                        size=20,
                        color=ft.Colors.WHITE70,
                    )
                ],
            ),
        )

    def _build_stage_body(self) -> ft.Control:
        if self.stage == Stage.DISPENSER:
            return DispenserStage(
                auto_mode=self.auto_mode,
                on_request_error=lambda msg: self.page.snack_bar.open() or None,
                snack=self._snack,
            ).view()

        if self.stage == Stage.VACUUM:
            return VacuumStage(
                auto_mode=self.auto_mode,
                snack=self._snack,
            ).view()

        return PlaceholderStage(title=f"{self.stage.value} page\n(implement later)").view()

    def _snack(self, msg: str):
        self.page.snack_bar = ft.SnackBar(ft.Text(msg))
        self.page.snack_bar.open = True
        self.page.update()

    def _handle_stage_error(self, msg: str):
        self._snack(msg)

    def _render(self):
        self.root.controls.clear()

        # Left: primary sidebar always
        self.root.controls.append(self.primary_sidebar.view())

        # Settings section shows stage sidebar
        if self.section == TopSection.SETTINGS:
            self.root.controls.append(self.stage_sidebar.view())

        # Main area
        if self.section == TopSection.DASHBOARD:
            main = self._build_dashboard_page()
        else:
            title = self.stage.value
            header = self._build_header(title)
            body = self._build_stage_body()

            main = ft.Container(
                expand=True,
                bgcolor=ft.Colors.BLACK87,
                padding=16,
                content=ft.Column(
                    expand=True,
                    controls=[
                        header,
                        ft.Container(height=16),
                        ft.Container(expand=True, content=body),
                    ],
                ),
            )

        self.root.controls.append(main)

        self.page.update()
