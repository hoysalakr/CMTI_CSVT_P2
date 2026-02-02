import flet as ft
from dataclasses import dataclass
from typing import Dict


@dataclass
class StageStatus:
    active: bool = False
    progress: float = 0.0  # 0.0 to 1.0
    now_running: str = "Idle"


class DashboardView:
    def __init__(
        self,
        statuses: Dict[str, StageStatus],
        run_state: str,  # "RUNNING" | "PAUSED" | "STOPPED"
        on_play,
        on_pause,
        on_reset,
    ):
        self.statuses = statuses
        self.run_state = run_state
        self.on_play = on_play
        self.on_pause = on_pause
        self.on_reset = on_reset

    def _stage_card(self, name: str, s: StageStatus) -> ft.Control:
        # highlight active stage
        border_color = ft.Colors.GREEN_ACCENT if s.active else ft.Colors.WHITE12
        bg = ft.Colors.with_opacity(0.25, ft.Colors.GREEN) if s.active else ft.Colors.BLACK54

        return ft.Container(
            width=240,
            padding=14,
            bgcolor=bg,
            border_radius=14,
            border=ft.border.all(2 if s.active else 1, border_color),
            content=ft.Column(
                tight=True,
                spacing=8,
                controls=[
                    ft.Row(
                        controls=[
                            ft.Text(
                                name,
                                size=16,
                                weight=ft.FontWeight.BOLD,
                                color=ft.Colors.WHITE,
                            ),
                            ft.Container(expand=True),
                            ft.Container(
                                padding=ft.padding.symmetric(8, 4),
                                bgcolor=ft.Colors.GREEN if s.active else ft.Colors.GREY_800,
                                border_radius=8,
                                content=ft.Text(
                                    "ACTIVE" if s.active else "IDLE",
                                    size=11,
                                    color=ft.Colors.BLACK if s.active else ft.Colors.WHITE70,
                                    weight=ft.FontWeight.W600,
                                ),
                            ),
                        ]
                    ),
                    ft.ProgressBar(value=s.progress),
                    ft.Text(
                        f"{int(s.progress * 100)}% complete",
                        size=12,
                        color=ft.Colors.WHITE70,
                    ),
                    ft.Text(
                        f"Now: {s.now_running}",
                        size=12,
                        color=ft.Colors.WHITE70,
                    ),
                ],
            ),
        )

    def _connector(self) -> ft.Control:
        return ft.Container(
            width=40,
            alignment=ft.alignment.center,
            content=ft.Icon(ft.Icons.ARROW_FORWARD_IOS, size=18, color=ft.Colors.WHITE24),
        )

    def view(self) -> ft.Control:
        # stage order
        order = ["Dispenser", "Vacuum", "Heating", "Packaging", "Sterilization"]

        cards = []
        for i, name in enumerate(order):
            cards.append(self._stage_card(name, self.statuses[name]))
            if i != len(order) - 1:
                cards.append(self._connector())

        # play/pause/reset bar
        state_chip_color = (
            ft.Colors.GREEN_ACCENT if self.run_state == "RUNNING"
            else ft.Colors.AMBER_ACCENT if self.run_state == "PAUSED"
            else ft.Colors.RED_ACCENT
        )

        controls_bar = ft.Row(
            controls=[
                ft.Text("Machine Control", size=16, weight=ft.FontWeight.BOLD),
                ft.Container(expand=True),
                ft.Container(
                    padding=ft.padding.symmetric(10, 6),
                    border_radius=10,
                    bgcolor=ft.Colors.with_opacity(0.15, state_chip_color),
                    border=ft.border.all(1, state_chip_color),
                    content=ft.Text(
                        f"STATE: {self.run_state}",
                        size=12,
                        color=state_chip_color,
                        weight=ft.FontWeight.W700,
                    ),
                ),
                ft.Container(width=10),
                ft.ElevatedButton(
                    "PLAY",
                    icon=ft.Icons.PLAY_ARROW,
                    on_click=self.on_play,
                ),
                ft.ElevatedButton(
                    "PAUSE",
                    icon=ft.Icons.PAUSE,
                    on_click=self.on_pause,
                ),
                ft.OutlinedButton(
                    "RESET",
                    icon=ft.Icons.RESTART_ALT,
                    on_click=self.on_reset,
                ),
            ],
        )

        return ft.Container(
            expand=True,
            padding=20,
            bgcolor=ft.Colors.BLACK87,
            content=ft.Column(
                expand=True,
                spacing=18,
                controls=[
                    controls_bar,
                    ft.Divider(color=ft.Colors.WHITE12),
                    ft.Text(
                        "Process Flow",
                        size=18,
                        weight=ft.FontWeight.BOLD,
                        color=ft.Colors.WHITE,
                    ),
                    ft.Container(
                        expand=False,
                        content=ft.Row(
                            controls=cards,
                            scroll=ft.ScrollMode.AUTO,  # allows horizontal scroll if window is small
                        ),
                    ),
                    ft.Container(
                        padding=14,
                        border_radius=14,
                        bgcolor=ft.Colors.BLACK54,
                        border=ft.border.all(1, ft.Colors.WHITE12),
                        content=ft.Text(
                            "Tip: When stage actions happen (motor/sensor), update the dashboard status using the shared callback.",
                            size=12,
                            color=ft.Colors.WHITE54,
                        ),
                    ),
                ],
            ),
        )
