import flet as ft

from components.auto_steps import AutoStepsPanel, Step
from theme import (
    THEME_ACCENT,
    THEME_ACCENT_DARK,
    THEME_BORDER,
    THEME_CARD,
    THEME_SURFACE,
    THEME_TEXT_MUTED,
    THEME_TEXT_PRIMARY,
    THEME_TEXT_SECONDARY,
)


class DispenserStage:
    """
    ONE single class:
      - manual_ui() builds manual panel
      - auto_ui() builds auto panel
      - view() decides what to show based on auto_mode (toggle)
    """

    def __init__(self, auto_mode: bool, snack, on_request_error=None, on_status=None):
        self.auto_mode = auto_mode
        self.snack = snack
        self.on_request_error = on_request_error
        self.on_status = on_status

        # -------- MANUAL state (Motor 001) --------
        self.m001_distance = ft.TextField(label="Distance (mm) for < and >", value="5", dense=True)
        self.m001_slow_rpm = ft.TextField(label="Slow RPM (for < and >)", value="10", dense=True)
        self.m001_rapid_rpm = ft.TextField(label="Rapid RPM (hold RAPID)", value="60", dense=True)

        self.m001_jogging = False
        self.m001_dir = None

        # -------- MANUAL state (Pair 01.1 + 01.2) --------
        self.pair_distance = ft.TextField(label="Distance (mm) for < and > (both)", value="5", dense=True)
        self.pair_slow_rpm = ft.TextField(label="Slow RPM (for < and >)", value="10", dense=True)
        self.pair_rapid_rpm = ft.TextField(label="Rapid RPM (hold RAPID)", value="60", dense=True)

        self.pair_jogging = False
        self.pair_dir = None

        self.auto_panel = AutoStepsPanel(
            snack=self.snack,
            title="Auto Inputs (Dispenser)",
            default_unit="mm",
            require_auto_mode=lambda: self.auto_mode,
            on_submit=self._on_auto_steps_submit,
        )

    # ===================== common helpers =====================
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
                    ft.Text(title, size=18, weight=ft.FontWeight.W_700, color=THEME_ACCENT),
                    ft.Container(height=10),
                    ft.Container(expand=True, content=content),
                ],
            ),
        )

    def _read_positive(self, tf: ft.TextField):
        try:
            v = float((tf.value or "").strip())
            if v <= 0:
                return None
            return v
        except:
            return None

    def _ensure_manual(self):
        if self.auto_mode:
            self.snack("Switch is AUTO. Turn OFF AUTO to use manual controls.")
            return False
        return True

    # ===================== AUTO callbacks =====================
    def _on_auto_steps_submit(self, steps: list[Step]):
        if self.on_status:
            self.on_status(0.60, f"Auto sequence queued: {len(steps)} step(s)")

    # ===================== MANUAL: commands =====================
    def _send_command(self, cmd: dict, label: str):
        # Stub: replace with your serial/network command later
        self.snack(f"{label}: {cmd}")

    # ---- M001 ----
    def _m001_slow_step(self, direction: str, status_text: ft.Text | None = None):
        if not self._ensure_manual():
            return

        dist = self._read_positive(self.m001_distance)
        rpm = self._read_positive(self.m001_slow_rpm)
        if dist is None:
            self.snack("Invalid distance")
            return
        if rpm is None:
            self.snack("Invalid slow RPM")
            return

        self._send_command(
            {
                "motor": "M001",
                "cmd": "move_mm",
                "direction": direction,
                "distance_mm": dist,
                "rpm": rpm,
            },
            "SLOW MOVE",
        )

        if status_text:
            status_text.value = f"Step {direction} queued (distance {dist}mm, {rpm} RPM)"
            status_text.update()

        if self.on_status:
            self.on_status(0.25, "Motor M001: Slow move running")

    def _m001_jog_start(self, direction: str, status_text: ft.Text):
        if not self._ensure_manual():
            return

        rpm = self._read_positive(self.m001_rapid_rpm)
        if rpm is None:
            self.snack("Invalid rapid RPM")
            return

        self.m001_jogging = True
        self.m001_dir = direction
        status_text.value = f"RAPID jogging {direction}… (release to stop)"
        status_text.update()

        self._send_command(
            {"motor": "M001", "cmd": "jog_start", "direction": direction, "rpm": rpm},
            "RAPID START",
        )

    def _m001_jog_stop(self, status_text: ft.Text):
        if not self.m001_jogging:
            return
        self.m001_jogging = False
        self.m001_dir = None
        status_text.value = "Hold RAPID to jog fast"
        status_text.update()

        self._send_command({"motor": "M001", "cmd": "jog_stop"}, "RAPID STOP")

    # ---- Pair ----
    def _pair_slow_step(self, direction: str, status_text: ft.Text | None = None):
        if not self._ensure_manual():
            return

        dist = self._read_positive(self.pair_distance)
        rpm = self._read_positive(self.pair_slow_rpm)
        if dist is None:
            self.snack("PAIR Invalid distance")
            return
        if rpm is None:
            self.snack("PAIR Invalid slow RPM")
            return

        self._send_command(
            {
                "motors": ["M01.1", "M01.2"],
                "cmd": "move_mm",
                "direction": direction,
                "distance_mm": dist,
                "rpm": rpm,
                "mode": "COUPLED",
            },
            "PAIR SLOW MOVE",
        )

        if status_text:
            status_text.value = f"PAIR step {direction} queued ({dist}mm @ {rpm}RPM)"
            status_text.update()

    def _pair_jog_start(self, direction: str, status_text: ft.Text):
        if not self._ensure_manual():
            return

        rpm = self._read_positive(self.pair_rapid_rpm)
        if rpm is None:
            self.snack("PAIR Invalid rapid RPM")
            return

        self.pair_jogging = True
        self.pair_dir = direction
        status_text.value = f"PAIR RAPID jogging {direction}… (release to stop)"
        status_text.update()

        self._send_command(
            {
                "motors": ["M01.1", "M01.2"],
                "cmd": "jog_start",
                "direction": direction,
                "rpm": rpm,
                "mode": "COUPLED",
            },
            "PAIR RAPID START",
        )

    def _pair_jog_stop(self, status_text: ft.Text):
        if not self.pair_jogging:
            return
        self.pair_jogging = False
        self.pair_dir = None
        status_text.value = "Hold RAPID to jog fast (both motors)"
        status_text.update()

        self._send_command(
            {"motors": ["M01.1", "M01.2"], "cmd": "jog_stop", "mode": "COUPLED"},
            "PAIR RAPID STOP",
        )

    # ===================== UI: MANUAL =====================
    def manual_ui(self) -> ft.Control:
        m001_status = ft.Text("Hold RAPID to jog fast", color=THEME_TEXT_SECONDARY)
        pair_status = ft.Text("Hold RAPID to jog fast (both motors)", color=THEME_TEXT_SECONDARY)

        def rapid_hold_btn(start_fn, stop_fn, direction: str, status_text: ft.Text):
            """Start jog when the press begins, stop when it ends/cancels."""
            return ft.GestureDetector(
                on_tap_down=lambda e: start_fn(direction, status_text),
                on_tap_up=lambda e: stop_fn(status_text),
                on_tap_cancel=lambda e: stop_fn(status_text),
                content=ft.Container(
                    padding=ft.padding.symmetric(18, 12),
                    bgcolor=THEME_ACCENT_DARK,
                    border_radius=22,
                    content=ft.Text("RAPID", weight=ft.FontWeight.W_600, color="black"),
                ),
            )

        motor001_block = ft.Column(
            controls=[
                ft.Text("Motor 001 – Manual Control", size=18, weight=ft.FontWeight.W_700, color=THEME_TEXT_PRIMARY),
                ft.Container(height=12),
                self.m001_distance,
                ft.Container(height=10),
                self.m001_slow_rpm,
                ft.Container(height=10),
                self.m001_rapid_rpm,
                ft.Container(height=10),
                m001_status,
                ft.Container(height=12),
                ft.Row(
                    controls=[
                        rapid_hold_btn(self._m001_jog_start, self._m001_jog_stop, "CCW", m001_status),
                        ft.Container(width=10),
                        ft.ElevatedButton(
                            "<",
                            on_click=lambda e: self._m001_slow_step("CCW", m001_status),
                            style=ft.ButtonStyle(
                                bgcolor=THEME_ACCENT,
                                color="black",
                                shape=ft.RoundedRectangleBorder(radius=22),
                                padding=ft.padding.symmetric(20, 12),
                            ),
                        ),
                        ft.Container(width=10),
                        ft.ElevatedButton(
                            ">",
                            on_click=lambda e: self._m001_slow_step("CW", m001_status),
                            style=ft.ButtonStyle(
                                bgcolor=THEME_ACCENT,
                                color="black",
                                shape=ft.RoundedRectangleBorder(radius=22),
                                padding=ft.padding.symmetric(20, 12),
                            ),
                        ),
                        ft.Container(width=10),
                        rapid_hold_btn(self._m001_jog_start, self._m001_jog_stop, "CW", m001_status),
                    ]
                ),
            ]
        )

        pair_block = ft.Column(
            controls=[
                ft.Container(height=16),
                ft.Divider(color=ft.Colors.WHITE12),
                ft.Container(height=12),
                ft.Text("Motors 01.1 + 01.2 – Control", size=18, weight=ft.FontWeight.W_700, color=THEME_TEXT_PRIMARY),
                ft.Container(height=12),
                self.pair_distance,
                ft.Container(height=10),
                self.pair_slow_rpm,
                ft.Container(height=10),
                self.pair_rapid_rpm,
                ft.Container(height=10),
                pair_status,
                ft.Container(height=12),
                ft.Row(
                    controls=[
                        rapid_hold_btn(self._pair_jog_start, self._pair_jog_stop, "CCW", pair_status),
                        ft.Container(width=10),
                        ft.ElevatedButton(
                            "<",
                            on_click=lambda e: self._pair_slow_step("CCW", pair_status),
                            style=ft.ButtonStyle(
                                bgcolor=THEME_ACCENT,
                                color="black",
                                shape=ft.RoundedRectangleBorder(radius=22),
                                padding=ft.padding.symmetric(20, 12),
                            ),
                        ),
                        ft.Container(width=10),
                        ft.ElevatedButton(
                            ">",
                            on_click=lambda e: self._pair_slow_step("CW", pair_status),
                            style=ft.ButtonStyle(
                                bgcolor=THEME_ACCENT,
                                color="black",
                                shape=ft.RoundedRectangleBorder(radius=22),
                                padding=ft.padding.symmetric(20, 12),
                            ),
                        ),
                        ft.Container(width=10),
                        rapid_hold_btn(self._pair_jog_start, self._pair_jog_stop, "CW", pair_status),
                    ]
                ),
            ]
        )

        # Scroll to prevent overflow like your Flutter fix
        return ft.Container(
            expand=True,
            bgcolor=THEME_SURFACE,
            content=ft.Column(
                expand=True,
                controls=[
                    ft.Container(
                        expand=True,
                        content=ft.ListView(
                            expand=True,
                            spacing=0,
                            auto_scroll=False,
                            controls=[motor001_block, pair_block],
                        ),
                    )
                ],
            ),
        )

    # ===================== final view (condition on auto_mode) =====================
    def view(self) -> ft.Control:
        manual_panel = self._panel("Manual", self.manual_ui())
        auto_panel = self.auto_panel.view()

        return ft.ResponsiveRow(
            columns=12,
            controls=[
                ft.Container(col={"xs": 12, "md": 6}, content=manual_panel),
                ft.Container(col={"xs": 12, "md": 6}, content=auto_panel),
            ],
        )
