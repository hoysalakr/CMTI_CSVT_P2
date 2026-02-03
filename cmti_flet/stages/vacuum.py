import time
import threading
import flet as ft

from components.auto_steps import AutoStepsPanel, Step


class VacuumStage:
    """
    Vacuum stage:
      - Box movement is MANUAL via coupled motors UI (M02.1 + M02.2) — same as Dispenser coupled UI
      - Vacuum process is AUTOMATIC once bed is in place (or when Start pressed)
      - Only two timing inputs: evacuate_time and hold_time
      - Global Auto panel stays
    """

    BED_MOTOR = "M001"                 # if you still use it elsewhere (optional)
    BOX_MOTORS = ["M02.1", "M02.2"]    # only coupled motor pair shown in UI

    def __init__(self, auto_mode: bool, snack, on_status=None):
        self.auto_mode = auto_mode
        self.snack = snack
        self.on_status = on_status

        # ---------------- Coupled motors inputs (ONLY THIS for box movement) ----------------
        self.pair_distance = ft.TextField(label="Distance (mm) for < and > (both)", value="5", dense=True)
        self.pair_slow_rpm = ft.TextField(label="Slow RPM (for < and >)", value="10", dense=True)
        self.pair_rapid_rpm = ft.TextField(label="Rapid RPM (hold RAPID)", value="60", dense=True)

        # ---------------- Vacuum timing inputs (ONLY 2 inputs) ----------------
        self.evacuate_time = ft.TextField(
            label="Evacuate time (seconds)",
            value="10",
            dense=True,
            keyboard_type=ft.KeyboardType.NUMBER,
        )
        self.hold_time = ft.TextField(
            label="Hold time (seconds)",
            value="5",
            dense=True,
            keyboard_type=ft.KeyboardType.NUMBER,
        )

        # Bed-in-place / Box-in-place can later come from sensors.
        # For base solution we keep a toggle to simulate "bed is in place + box seated".
        self.bed_in_place = False
        self.box_seated = False

        self.status_text = ft.Text("Status: IDLE", color=ft.Colors.WHITE70)

        self._abort = False
        self._worker = None

        # ---------------- Global Auto panel (keep as-is) ----------------
        self.auto_panel = AutoStepsPanel(
            snack=self.snack,
            title="Auto Inputs (Global) — Vacuum",
            default_unit="mm",
            require_auto_mode=lambda: self.auto_mode,
            on_submit=self._on_global_auto_submit,
        )

    # ===================== helpers =====================
    def _panel(self, title: str, content: ft.Control) -> ft.Control:
        return ft.Container(
            padding=14,
            bgcolor=ft.Colors.BLACK54,
            border=ft.border.all(1, ft.Colors.WHITE12),
            border_radius=14,
            content=ft.Column(
                controls=[
                    ft.Text(title, size=18, weight=ft.FontWeight.W_700),
                    ft.Container(height=12),
                    content,
                ],
            ),
        )

    def _ui_update(self, c: ft.Control):
        if c.page is not None:
            c.update()

    def _set_status(self, msg: str):
        self.status_text.value = f"Status: {msg}"
        self._ui_update(self.status_text)

    def _read_positive(self, tf: ft.TextField):
        try:
            v = float((tf.value or "").strip())
            if v <= 0:
                return None
            return v
        except:
            return None

    def _ensure_auto(self):
        if not self.auto_mode:
            self.snack("Turn ON AUTO to run the vacuum sequence.")
            return False
        return True

    # ===================== hardware stub =====================
    def _send_hw(self, cmd: dict, label: str):
        # Replace later with GPIO mapping
        self.snack(f"{label}: {cmd}")

    # ===================== global auto submit =====================
    def _on_global_auto_submit(self, steps: list[Step]):
        if self.on_status:
            self.on_status(0.10, f"Vacuum: Global steps loaded ({len(steps)} step(s))")

    # ===================== coupled motor commands (same logic, different name) =====================
    def _move_coupled(self, direction: str):
        dist = self._read_positive(self.pair_distance)
        rpm = self._read_positive(self.pair_slow_rpm)
        if dist is None:
            self.snack("Invalid distance")
            return
        if rpm is None:
            self.snack("Invalid slow RPM")
            return

        self._send_hw(
            {
                "motors": self.BOX_MOTORS,      # M02.1, M02.2
                "cmd": "move_mm",
                "direction": direction,
                "distance_mm": dist,
                "rpm": rpm,
                "mode": "COUPLED",
            },
            "BOX MOVE (COUPLED)",
        )

    def _jog_start(self, direction: str, status: ft.Text):
        rpm = self._read_positive(self.pair_rapid_rpm)
        if rpm is None:
            self.snack("Invalid rapid RPM")
            return

        self._send_hw(
            {
                "motors": self.BOX_MOTORS,
                "cmd": "jog_start",
                "direction": direction,
                "rpm": rpm,
                "mode": "COUPLED",
            },
            "BOX RAPID START",
        )
        status.value = f"RAPID jogging {direction}… (release to stop)"
        self._ui_update(status)

    def _jog_stop(self, status: ft.Text):
        self._send_hw(
            {"motors": self.BOX_MOTORS, "cmd": "jog_stop", "mode": "COUPLED"},
            "BOX RAPID STOP",
        )
        status.value = "Hold RAPID to jog fast (both motors)"
        self._ui_update(status)

    def _rapid_hold_btn(self, direction: str, status: ft.Text):
        return ft.GestureDetector(
            on_tap_down=lambda e: self._jog_start(direction, status),
            on_tap_up=lambda e: self._jog_stop(status),
            on_tap_cancel=lambda e: self._jog_stop(status),
            content=ft.Container(
                padding=ft.padding.symmetric(18, 12),
                bgcolor=ft.Colors.BLUE_GREY,
                border_radius=22,
                content=ft.Text("RAPID", weight=ft.FontWeight.W_600),
            ),
        )

    # ===================== AUTOMATIC VACUUM SEQUENCE =====================
    def _sleep_or_abort(self, seconds: float) -> bool:
        end = time.time() + seconds
        while time.time() < end:
            if self._abort:
                return False
            time.sleep(0.1)
        return True

    def _run_vacuum_sequence(self, t_evac: float, t_hold: float):
        self._abort = False

        # Requirement: Outlet CLOSED until final open
        self._send_hw({"solenoid_outlet": "CLOSE"}, "OUTLET SOLENOID")

        # Make sure bed + box are in place
        if not self.bed_in_place:
            self._set_status("BLOCKED: bed not in position")
            self.snack("Bed is not in position. Set 'Bed in place' first.")
            return
        if not self.box_seated:
            self._set_status("BLOCKED: box not seated")
            self.snack("Vacuum box not seated. Set 'Box seated' first.")
            return

        # Pump ON + Inlet OPEN -> wait evacuate_time
        self._set_status(f"EVACUATING ({t_evac:.1f}s): Pump ON + Inlet OPEN")
        self._send_hw({"relay_pump": "ON"}, "PUMP RELAY")
        self._send_hw({"solenoid_inlet": "OPEN"}, "INLET SOLENOID")
        self._send_hw({"solenoid_outlet": "CLOSE"}, "OUTLET SOLENOID")

        if self.on_status:
            self.on_status(0.60, "Vacuum: evacuating")

        if not self._sleep_or_abort(t_evac):
            return

        # Inlet CLOSE + Pump OFF -> wait hold_time
        self._set_status(f"HOLDING ({t_hold:.1f}s): Inlet CLOSED + Pump OFF")
        self._send_hw({"solenoid_inlet": "CLOSE"}, "INLET SOLENOID")
        self._send_hw({"relay_pump": "OFF"}, "PUMP RELAY")
        self._send_hw({"solenoid_outlet": "CLOSE"}, "OUTLET SOLENOID")

        if self.on_status:
            self.on_status(0.85, "Vacuum: holding")

        if not self._sleep_or_abort(t_hold):
            return

        # Final: Outlet OPEN
        self._set_status("DONE: Outlet OPEN")
        self._send_hw({"solenoid_outlet": "OPEN"}, "OUTLET SOLENOID")

        if self.on_status:
            self.on_status(1.00, "Vacuum: completed (outlet open)")

    def start_auto_vacuum(self, e=None):
        if not self._ensure_auto():
            return

        if self._worker is not None and self._worker.is_alive():
            self.snack("Vacuum sequence already running.")
            return

        t_evac = self._read_positive(self.evacuate_time)
        t_hold = self._read_positive(self.hold_time)
        if t_evac is None:
            self.snack("Invalid evacuate time")
            return
        if t_hold is None:
            self.snack("Invalid hold time")
            return

        self._worker = threading.Thread(
            target=self._run_vacuum_sequence,
            args=(t_evac, t_hold),
            daemon=True,
        )
        self._worker.start()

    def stop_auto_vacuum(self, e=None):
        self._abort = True

        # Safe off
        self._send_hw({"solenoid_inlet": "CLOSE"}, "INLET SOLENOID")
        self._send_hw({"solenoid_outlet": "CLOSE"}, "OUTLET SOLENOID")
        self._send_hw({"relay_pump": "OFF"}, "PUMP RELAY")

        self._set_status("ABORTED by user")
        if self.on_status:
            self.on_status(0.0, "Vacuum: aborted")

    # ===================== UI sections =====================
    def coupled_motors_ui(self) -> ft.Control:
        status = ft.Text("Hold RAPID to jog fast (both motors)", color=ft.Colors.WHITE70)

        return ft.Column(
            controls=[
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
                        self._rapid_hold_btn("CCW", status),
                        ft.Container(width=10),
                        ft.ElevatedButton("<", on_click=lambda e: self._move_coupled("CCW")),
                        ft.Container(width=10),
                        ft.ElevatedButton(">", on_click=lambda e: self._move_coupled("CW")),
                        ft.Container(width=10),
                        self._rapid_hold_btn("CW", status),
                    ]
                ),
            ]
        )

    def timing_ui(self) -> ft.Control:
        # These are the ONLY inputs you wanted below coupled motor section
        return ft.Column(
            controls=[
                self.evacuate_time,
                ft.Container(height=10),
                self.hold_time,
                ft.Container(height=12),

                # base “position” toggles (replace with sensors later)
                ft.Row(
                    controls=[
                        ft.Switch(
                            label="Bed in place (sensor/toggle)",
                            value=self.bed_in_place,
                            on_change=lambda e: setattr(self, "bed_in_place", e.control.value),
                        ),
                        ft.Container(width=10),
                        ft.Switch(
                            label="Box seated (sensor/toggle)",
                            value=self.box_seated,
                            on_change=lambda e: setattr(self, "box_seated", e.control.value),
                        ),
                    ]
                ),

                ft.Container(height=10),
                ft.Row(
                    controls=[
                        ft.ElevatedButton("START AUTO VACUUM", icon=ft.Icons.PLAY_ARROW, on_click=self.start_auto_vacuum),
                        ft.OutlinedButton("STOP", icon=ft.Icons.STOP, on_click=self.stop_auto_vacuum),
                    ]
                ),
                ft.Container(height=10),
                self.status_text,
            ]
        )

    # ===================== final view =====================
    def view(self) -> ft.Control:
        left_scroll = ft.ListView(
            expand=True,
            controls=[
                self._panel("Motors 02.1 + 02.2 – Control", self.coupled_motors_ui()),
                ft.Container(height=14),
                self._panel("Vacuum timings (only 2 inputs) + Auto vacuum", self.timing_ui()),
            ],
        )

        return ft.ResponsiveRow(
            columns=12,
            controls=[
                ft.Container(col={"xs": 12, "md": 7}, content=left_scroll),
                ft.Container(col={"xs": 12, "md": 5}, content=self.auto_panel.view()),
            ],
        )
