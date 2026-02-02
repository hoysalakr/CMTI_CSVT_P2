import sys
import os
from stages.dashboard import DashboardView, StageStatus
from stages.vacuum import VacuumStage
from theme import (
    THEME_ACCENT,
    THEME_ACCENT_DARK,
    THEME_BG,
    THEME_CARD,
    THEME_SURFACE,
    THEME_SURFACE_ALT,
    THEME_TEXT_MUTED,
    THEME_TEXT_PRIMARY,
    THEME_TEXT_SECONDARY,
)


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
        self.page.bgcolor = THEME_BG
        self.page.theme_mode = ft.ThemeMode.DARK

        self.section = TopSection.SETTINGS
        self.stage = Stage.DISPENSER
        self.auto_mode = False  # False=Manual, True=Auto

        self._dispenser_stage = None
        self._vacuum_stage = None

        # ---------- DASHBOARD shared machine state ----------
        self.run_state = "STOPPED"  # RUNNING / PAUSED / STOPPED

        self.statuses = {
            "Dispenser": StageStatus(active=False, progress=0.0, now_running="Idle"),
            "Vacuum": StageStatus(active=False, progress=0.0, now_running="Idle"),
            "Heating": StageStatus(active=False, progress=0.0, now_running="Idle"),
            "Packaging": StageStatus(active=False, progress=0.0, now_running="Idle"),
            "Sterilization": StageStatus(active=False, progress=0.0, now_running="Idle"),
        }

        # Main containers
        self.primary_sidebar = PrimarySidebar(
            get_active=lambda: self.section,
            on_select=self._on_section_select,
        )

        self.stage_sidebar = StageSidebar(
            get_active=lambda: self.stage,
            on_select=self._on_stage_select,
        )

        self.header_title = ft.Text("", size=26, weight=ft.FontWeight.BOLD, color=THEME_TEXT_PRIMARY)
        self.mode_text = ft.Text("", size=14, weight=ft.FontWeight.W_600, color=THEME_TEXT_MUTED)
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
        self.mode_text.color = THEME_ACCENT if self.auto_mode else THEME_TEXT_MUTED

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
            bgcolor=THEME_SURFACE,
            padding=24,
            content=ft.Column(
                alignment=ft.MainAxisAlignment.CENTER,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                controls=[
                    ft.Text(
                        "DASHBOARD PAGE\n(add sensors + status later)",
                        text_align=ft.TextAlign.CENTER,
                        size=20,
                        color=THEME_TEXT_SECONDARY,
                    )
                ],
            ),
        )

    def _build_stage_body(self) -> ft.Control:
        if self.stage == Stage.DISPENSER:
            if self._dispenser_stage is None:
                self._dispenser_stage = DispenserStage(
                    auto_mode=self.auto_mode,
                    snack=self._snack,
                    on_request_error=self._handle_stage_error,
                    on_status=lambda p, msg: self.update_stage_status(
                        "Dispenser", progress=p, now_running=msg, make_active=True
                    ),
                )
            else:
                self._dispenser_stage.auto_mode = self.auto_mode

            return self._dispenser_stage.view()

        if self.stage == Stage.VACUUM:
            if self._vacuum_stage is None:
                self._vacuum_stage = VacuumStage(
                    auto_mode=self.auto_mode,
                    snack=self._snack,
                    on_status=lambda p, msg: self.update_stage_status(
                        "Vacuum", progress=p, now_running=msg, make_active=True
                    ),
                )
            else:
                self._vacuum_stage.auto_mode = self.auto_mode

            return self._vacuum_stage.view()

        return PlaceholderStage(title=f"{self.stage.value} page\n(implement later)").view()

    def _set_active_stage(self, name: str):
        for k in self.statuses:
            self.statuses[k].active = k == name

    def _dashboard_play(self, e):
        self.run_state = "RUNNING"
        self._snack("Machine started (stub)")
        self._render()

    def _dashboard_pause(self, e):
        self.run_state = "PAUSED"
        self._snack("Machine paused (stub)")
        self._render()

    def _dashboard_reset(self, e):
        self.run_state = "STOPPED"
        for k in self.statuses:
            self.statuses[k].progress = 0.0
            self.statuses[k].now_running = "Idle"
            self.statuses[k].active = False
        self._snack("Machine reset (stub)")
        self._render()

    def _open_stage_from_dashboard(self, stage_name: str):
        self.section = TopSection.SETTINGS

        mapping = {
            "Dispenser": Stage.DISPENSER,
            "Vacuum": Stage.VACUUM,
            "Heating": Stage.HEATING,
            "Packaging": Stage.PACKAGING,
            "Sterilization": Stage.STERILIZATION,
        }
        self.stage = mapping[stage_name]
        self._render()

    def update_stage_status(self, stage_name: str, progress=None, now_running=None, make_active=False):
        s = self.statuses[stage_name]
        if progress is not None:
            s.progress = max(0.0, min(1.0, float(progress)))
        if now_running is not None:
            s.now_running = now_running
        if make_active:
            self._set_active_stage(stage_name)
        self._render()

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
            main = DashboardView(
                statuses=self.statuses,
                run_state=self.run_state,
                on_play=self._dashboard_play,
                on_pause=self._dashboard_pause,
                on_reset=self._dashboard_reset,
                on_stage_click=self._open_stage_from_dashboard,
            ).view()
        else:
            title = self.stage.value
            header = self._build_header(title)
            body = self._build_stage_body()

            main = ft.Container(
                expand=True,
                bgcolor=THEME_SURFACE_ALT,
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
