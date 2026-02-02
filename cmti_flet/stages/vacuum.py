import flet as ft

from theme import (
    THEME_ACCENT,
    THEME_ACCENT_DARK,
    THEME_BORDER,
    THEME_CARD,
    THEME_SURFACE,
    THEME_TEXT_PRIMARY,
    THEME_TEXT_SECONDARY,
)


class VacuumStage:
    """
    Vacuum stage:
    - Manual control only (Coupled motors 01.1 + 01.2 block copied from Dispenser manual)
    - Uses AUTO/MANUAL toggle from main header:
        If auto_mode=True -> manual actions blocked (same behavior as dispenser)
    """

    def __init__(self, auto_mode: bool, snack, on_status=None):
        self.auto_mode = auto_mode
        self.snack = snack
        self.on_status = on_status

        # Coupled motors 01.1 + 01.2 (same as dispenser coupled part)
        self.pair_distance = ft.TextField(
            label="Distance (mm) for < and > (both)",
            value="5",
            dense=True,
            keyboard_type=ft.KeyboardType.NUMBER,
        )
        self.pair_slow_rpm = ft.TextField(
            label="Slow RPM (for < and >)",
            value="10",
            dense=True,
            keyboard_type=ft.KeyboardType.NUMBER,
        )
        self.pair_rapid_rpm = ft.TextField(
            label="Rapid RPM (hold RAPID)",
            value="60",
            dense=True,
            keyboard_type=ft.KeyboardType.NUMBER,
        )

        self.pair_jogging = False
        self.pair_dir = None

    # ---------- helpers ----------
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
            self.snack("Switch is AUTO. Turn OFF AUTO to use Vacuum manual controls.")
            return False
        return True

    def _send_command(self, cmd: dict, label: str):
        # Stub: replace with actual vacuum motor command
        self.snack(f"{label}: {cmd}")

    # ---------- coupled motors actions ----------
    def _pair_slow_step(self, direction: str, status_text: ft.Text | None = None):
        if not self._ensure_manual():
            return

        dist = self._read_positive(self.pair_distance)
        rpm = self._read_positive(self.pair_slow_rpm)

        if dist is None:
            self.snack("VACUUM: Invalid distance")
            return
        if rpm is None:
            self.snack("VACUUM: Invalid slow RPM")
            return

        self._send_command(
            {
                "stage": "VACUUM",
                "motors": ["M01.1", "M01.2"],
                "cmd": "move_mm",
                "direction": direction,
                "distance_mm": dist,
                "rpm": rpm,
                "mode": "COUPLED",
            },
            "VACUUM SLOW MOVE",
        )

        if status_text:
            status_text.value = f"VACUUM step {direction} queued ({dist}mm @ {rpm}RPM)"
            status_text.update()

        if self.on_status:
            self.on_status(0.15, "Pressure sensor: sampling + motors coupled move")

    def _pair_jog_start(self, direction: str, status_text: ft.Text):
        if not self._ensure_manual():
            return

        rpm = self._read_positive(self.pair_rapid_rpm)
        if rpm is None:
            self.snack("VACUUM: Invalid rapid RPM")
            return

        self.pair_jogging = True
        self.pair_dir = direction
        status_text.value = f"VACUUM RAPID jogging {direction}… (release to stop)"
        status_text.update()

        self._send_command(
            {
                "stage": "VACUUM",
                "motors": ["M01.1", "M01.2"],
                "cmd": "jog_start",
                "direction": direction,
                "rpm": rpm,
                "mode": "COUPLED",
            },
            "VACUUM RAPID START",
        )

    def _pair_jog_stop(self, status_text: ft.Text):
        if not self.pair_jogging:
            return

        self.pair_jogging = False
        self.pair_dir = None
        status_text.value = "Hold RAPID to jog fast (both motors)"
        status_text.update()

        self._send_command(
            {
                "stage": "VACUUM",
                "motors": ["M01.1", "M01.2"],
                "cmd": "jog_stop",
                "mode": "COUPLED",
            },
            "VACUUM RAPID STOP",
        )

    # ---------- UI ----------
    def view(self) -> ft.Control:
        status = ft.Text("Hold RAPID to jog fast (both motors)", color=THEME_TEXT_SECONDARY)

        def rapid_hold_btn(direction: str):
            return ft.GestureDetector(
                on_tap_down=lambda e: self._pair_jog_start(direction, status),
                on_tap_up=lambda e: self._pair_jog_stop(status),
                on_tap_cancel=lambda e: self._pair_jog_stop(status),
                content=ft.Container(
                    padding=ft.padding.symmetric(18, 12),
                    bgcolor=THEME_ACCENT_DARK,
                    border_radius=22,
                    content=ft.Text("RAPID", weight=ft.FontWeight.W_600, color="black"),
                ),
            )

        content = ft.ListView(
            expand=True,
            controls=[
                ft.Text("Motors 01.1 + 01.2 – Vacuum Control", size=18, weight=ft.FontWeight.W_700, color=THEME_TEXT_PRIMARY),
                ft.Container(height=12),
                self.pair_distance,
                ft.Container(height=10),
                self.pair_slow_rpm,
                ft.Container(height=10),
                self.pair_rapid_rpm,
                ft.Container(height=10),
                status,
                ft.Container(height=12),
                ft.Row(
                    controls=[
                        rapid_hold_btn("CCW"),
                        ft.Container(width=10),
                        ft.ElevatedButton(
                            "<",
                            on_click=lambda e: self._pair_slow_step("CCW", status),
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
                            on_click=lambda e: self._pair_slow_step("CW", status),
                            style=ft.ButtonStyle(
                                bgcolor=THEME_ACCENT,
                                color="black",
                                shape=ft.RoundedRectangleBorder(radius=22),
                                padding=ft.padding.symmetric(20, 12),
                            ),
                        ),
                        ft.Container(width=10),
                        rapid_hold_btn("CW"),
                    ]
                ),
            ],
        )

        return ft.Container(bgcolor=THEME_SURFACE, content=self._panel("Vacuum – Manual", content))
