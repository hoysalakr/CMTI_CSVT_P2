import flet as ft

from components.auto_steps import AutoStepsPanel, Step
from theme import THEME_BORDER, THEME_CARD, THEME_TEXT_PRIMARY, THEME_TEXT_SECONDARY


class PackagingStage:
    def __init__(self, auto_mode: bool, snack, on_status=None):
        self.auto_mode = auto_mode
        self.snack = snack
        self.on_status = on_status

        # last submitted auto steps (used by dashboard play)
        self.last_auto_steps: list[Step] | None = None

        self.auto_panel = AutoStepsPanel(
            snack=self.snack,
            title="Auto Inputs (Packaging)",
            default_unit="mm",
            require_auto_mode=lambda: self.auto_mode,
            on_submit=self._on_auto_steps_submit,
        )

    def _on_auto_steps_submit(self, steps: list[Step]):
        # remember last submitted steps so dashboard can use them
        self.last_auto_steps = steps
        if self.on_status:
            self.on_status(0.60, f"Packaging auto queued: {len(steps)} step(s)")

    def manual_ui(self) -> ft.Control:
        return ft.Container(
            expand=True,
            alignment=ft.alignment.Alignment(0, 0),
            content=ft.Text(
                "Packaging manual page (to be implemented)",
                color=THEME_TEXT_SECONDARY,
            ),
        )

    def _panel(self, title: str, content: ft.Control) -> ft.Control:
        return ft.Container(
            expand=True,
            padding=14,
            bgcolor=THEME_CARD,
            border=ft.border.all(1, THEME_BORDER),
            border_radius=14,
            content=ft.Column(
                expand=True,
                controls=[
                    ft.Text(title, size=18, weight=ft.FontWeight.W_700, color=THEME_TEXT_PRIMARY),
                    ft.Container(height=12),
                    ft.Container(expand=True, content=content),
                ],
            ),
        )

    def view(self) -> ft.Control:
        return ft.ResponsiveRow(
            columns=12,
            controls=[
                ft.Container(col={"xs": 12, "md": 6}, content=self._panel("Manual", self.manual_ui())),
                ft.Container(col={"xs": 12, "md": 6}, content=self.auto_panel.view()),
            ],
        )
