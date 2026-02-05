import flet as ft
from dataclasses import dataclass
from typing import Dict, Callable


@dataclass
class StageStatus:
    active: bool = False
    progress: float = 0.0
    now_running: str = "Idle"


class DashboardView:
    def __init__(
        self,
        statuses: Dict[str, StageStatus],
        run_state: str,
        on_play,
        on_pause,
        on_reset,
        on_stage_click: Callable[[str], None],
    ):
        self.statuses = statuses
        self.run_state = run_state
        self.on_play = on_play
        self.on_pause = on_pause
        self.on_reset = on_reset
        self.on_stage_click = on_stage_click

        # Tune these once and the whole dashboard stays aligned
        self.card_w = 290
        self.card_h = 140
        self.gap = 22
        self.arrow_w = 42

    # ---------- UI pieces ----------
    def _stage_card(self, name: str, s: StageStatus) -> ft.Control:
        border_color = ft.Colors.GREEN_ACCENT if s.active else ft.Colors.WHITE12
        bg = (
            ft.LinearGradient(
                begin=ft.alignment.top_left,
                end=ft.alignment.bottom_right,
                colors=[ft.Colors.GREEN_ACCENT.with_opacity(0.25), ft.Colors.BLACK54],
            )
            if s.active
            else ft.Colors.BLACK54
        )
        glow = [
            ft.BoxShadow(
                spread_radius=3,
                blur_radius=18,
                color=ft.Colors.GREEN_ACCENT.with_opacity(0.45),
                offset=ft.Offset(0, 0),
            )
        ] if s.active else []

        card = ft.Container(
            width=self.card_w,
            height=self.card_h,
            padding=14,
            bgcolor=bg,
            border_radius=14,
            border=ft.border.all(2 if s.active else 1, border_color),
            shadow=glow,
            content=ft.Column(
                spacing=8,
                controls=[
                    ft.Row(
                        controls=[
                            ft.Text(name, size=16, weight=ft.FontWeight.BOLD),
                            ft.Container(expand=True),
                            ft.Container(
                                padding=ft.padding.symmetric(8, 4),
                                bgcolor=ft.Colors.GREEN if s.active else ft.Colors.GREY_800,
                                border_radius=8,
                                content=ft.Text(
                                    "ACTIVE" if s.active else "IDLE",
                                    size=11,
                                    color=ft.Colors.BLACK if s.active else ft.Colors.WHITE70,
                                    weight=ft.FontWeight.W_600,
                                ),
                            ),
                        ]
                    ),
                    ft.ProgressBar(value=s.progress),
                    ft.Text(f"{int(s.progress * 100)}% complete", size=12, color=ft.Colors.WHITE70),
                    ft.Text(f"Now: {s.now_running}", size=12, color=ft.Colors.WHITE70),
                ],
            ),
        )

        return ft.GestureDetector(
            on_tap=lambda e: self.on_stage_click(name),
            content=card,
        )

    def _arrow_h(self) -> ft.Control:
        return ft.Container(
            width=self.arrow_w,
            height=self.card_h,
            alignment=ft.alignment.Alignment(0, 0),
            content=ft.Icon(ft.Icons.ARROW_FORWARD_IOS, size=18, color=ft.Colors.WHITE30),
        )

    def _arrow_left(self) -> ft.Control:
        return ft.Container(
            width=self.arrow_w,
            height=self.card_h,
            alignment=ft.alignment.Alignment(0, 0),
            content=ft.Icon(ft.Icons.ARROW_BACK_IOS, size=18, color=ft.Colors.WHITE30),
        )

    def _arrow_down(self) -> ft.Control:
        return ft.Container(
            width=self.card_w,
            height=40,
            alignment=ft.alignment.Alignment(0, 0),
            content=ft.Icon(ft.Icons.ARROW_DOWNWARD, size=22, color=ft.Colors.WHITE30),
        )

    def _arrow_vertical(self) -> ft.Control:
        return ft.Container(
            height=36,
            alignment=ft.alignment.Alignment(0, 0),
            content=ft.Icon(ft.Icons.ARROW_DOWNWARD, size=20, color=ft.Colors.WHITE24),
        )

    def _arrow_blank(self) -> ft.Control:
        return ft.Container(width=self.arrow_w, height=self.card_h)  # keeps grid spacing consistent

    def _heating_offset(self) -> int:
        # Distance from the row's left edge to the Heating card start
        return 2 * self.card_w + 2 * self.arrow_w + 4 * self.gap

    def _controls_bar(self) -> ft.Control:
        state_color = (
            ft.Colors.GREEN_ACCENT if self.run_state == "RUNNING"
            else ft.Colors.AMBER_ACCENT if self.run_state == "PAUSED"
            else ft.Colors.RED_ACCENT
        )

        return ft.Row(
            controls=[
                ft.Text("Machine Control", size=18, weight=ft.FontWeight.BOLD),
                ft.Container(expand=True),
                ft.Container(
                    padding=ft.padding.symmetric(10, 6),
                    border_radius=10,
                    bgcolor=ft.Colors.with_opacity(0.12, state_color),
                    border=ft.border.all(1, state_color),
                    content=ft.Text(
                        f"STATE: {self.run_state}",
                        size=12,
                        color=state_color,
                        weight=ft.FontWeight.W_700,
                    ),
                ),
                ft.Container(width=10),
                ft.ElevatedButton("PLAY", icon=ft.Icons.PLAY_ARROW, on_click=self.on_play),
                ft.ElevatedButton("PAUSE", icon=ft.Icons.PAUSE, on_click=self.on_pause),
                ft.OutlinedButton("RESET", icon=ft.Icons.RESTART_ALT, on_click=self.on_reset),
            ],
        )

    # ---------- Final dashboard ----------
    def view(self) -> ft.Control:
        # Vertical flow listing – matches dashboard plus highlights active stage
        flow = ["Dispenser", "Vacuum", "Heating", "Packaging", "Sterilization"]
        flow_controls: list[ft.Control] = []

        for idx, stage_name in enumerate(flow):
            flow_controls.append(self._stage_card(stage_name, self.statuses[stage_name]))
            if idx < len(flow) - 1:
                flow_controls.append(self._arrow_vertical())

        return ft.Container(
            expand=True,
            padding=20,
            bgcolor=ft.Colors.BLACK87,
            content=ft.Column(
                spacing=18,
                controls=[
                    self._controls_bar(),
                    ft.Divider(color=ft.Colors.WHITE12),
                    ft.Text("Process Flow", size=18, weight=ft.FontWeight.BOLD),
                    ft.Column(spacing=10, controls=flow_controls, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                ],
            ),
        )
