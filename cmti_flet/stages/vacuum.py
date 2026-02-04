import time
import threading
import flet as ft

from components.auto_steps import AutoStepsPanel, Step
from hardware import get_hardware_controller
from hardware.stage_integration import VacuumControl

try:
    from hardware.controller import SENSOR_CONFIG
except ImportError:  # Fallback during packaging
    SENSOR_CONFIG = {}


class VacuumStage:
    """
    Vacuum stage:
      - Box movement is MANUAL via coupled motors UI (M02.1 + M02.2) — same as Dispenser coupled UI
      - Vacuum process is AUTOMATIC once bed is in place (or when Start pressed)
      - Only two timing inputs: evacuate_time and hold_time
      - Global Auto panel stays
    """

    BED_MOTOR = "M001"                 # if you still use it elsewhere (optional)
    BOX_MOTORS = ["M01.1", "M01.2"]    # only coupled motor pair shown in UI
    AUTO_BOX_RPM = 30                    # Fixed RPM for automatic positioning

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

        self.status_text = ft.Text("Status: IDLE", color=ft.Colors.WHITE70)

        self._abort = False
        self._worker = None

        # ---------------- Hardware ----------------
        self.hw = get_hardware_controller()
        self.vacuum = VacuumControl(self.hw)

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

    # ===================== hardware helpers =====================
    def _actuator(self, actuator_id: str, state: str, label: str):
        try:
            if state.upper() in {"ON", "OPEN", "ENABLE"}:
                self.hw.actuator_on(actuator_id)
            else:
                self.hw.actuator_off(actuator_id)
            self.snack(f"{label}: {state}")
        except Exception as exc:
            self.snack(f"Hardware error ({label}): {exc}")

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

        try:
            dir_map = {"CW": "FORWARD", "CCW": "BACKWARD"}
            self.vacuum.jog_coupled(
                distance=dist,
                rpm=rpm,
                direction=dir_map.get(direction, "FORWARD"),
            )
        except Exception as exc:
            self.snack(f"Coupled move failed: {exc}")

    def _move_box_to_position(self):
        dist = self._read_positive(self.pair_distance)
        if dist is None:
            raise ValueError("Set a valid coupled distance before running vacuum sequence")

        try:
            self.vacuum.jog_coupled(distance=dist, rpm=self.AUTO_BOX_RPM, direction="FORWARD")
        except Exception as exc:
            raise RuntimeError(f"Coupled move failed: {exc}") from exc

    def _jog_start(self, direction: str, status: ft.Text):
        rpm = self._read_positive(self.pair_rapid_rpm)
        if rpm is None:
            self.snack("Invalid rapid RPM")
            return

        try:
            dir_map = {"CW": "FORWARD", "CCW": "BACKWARD"}
            self.vacuum.jog_coupled_start(rpm, dir_map.get(direction, "FORWARD"))
        except Exception as exc:
            self.snack(f"Coupled jog start failed: {exc}")
        status.value = f"RAPID jogging {direction}… (release to stop)"
        self._ui_update(status)

    def _jog_stop(self, status: ft.Text):
        try:
            self.vacuum.jog_coupled_stop()
        except Exception as exc:
            self.snack(f"Coupled jog stop failed: {exc}")
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
        self._actuator("solenoid_valve", "CLOSE", "OUTLET SOLENOID")

        # Move box based on coupled distance input
        try:
            self._set_status("POSITIONING: Moving vacuum box")
            self._move_box_to_position()
        except ValueError as err:
            self.snack(str(err))
            return
        except RuntimeError as err:
            self.snack(str(err))
            return

        # Pump ON + Inlet OPEN -> wait evacuate_time
        self._set_status(f"EVACUATING ({t_evac:.1f}s): Pump ON + Inlet OPEN")
        self._actuator("pump_relay", "ON", "PUMP RELAY")
        self._actuator("solenoid_inlet", "OPEN", "INLET SOLENOID")

        if self.on_status:
            self.on_status(0.60, "Vacuum: evacuating")

        if not self._sleep_or_abort(t_evac):
            return

        # Inlet CLOSE -> Pump stays ON until inlet closed
        self._set_status("INLET CLOSING: Pump still ON")
        self._actuator("solenoid_inlet", "CLOSE", "INLET SOLENOID")

        # Pump OFF
        self._set_status("PUMP OFF: Holding vacuum")
        self._actuator("pump_relay", "OFF", "PUMP RELAY")

        if self.on_status:
            self.on_status(0.85, "Vacuum: holding")

        if not self._sleep_or_abort(t_hold):
            return

        # Final: Outlet OPEN
        self._set_status("DONE: Outlet OPEN")
        self._actuator("solenoid_valve", "OPEN", "OUTLET SOLENOID")

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
        self._actuator("solenoid_inlet", "CLOSE", "INLET SOLENOID")
        self._actuator("solenoid_valve", "CLOSE", "OUTLET SOLENOID")
        self._actuator("pump_relay", "OFF", "PUMP RELAY")

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
