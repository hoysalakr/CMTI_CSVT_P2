import time
import threading
import flet as ft

try:  # Preferred when running as package (python -m cmti_flet.main)
    from cmti_flet.hardware import get_hardware_controller
    from cmti_flet.hardware.stage_integration import VacuumControl
    from cmti_flet.hardware.controller import SENSOR_CONFIG
except ModuleNotFoundError:
    from hardware import get_hardware_controller
    from hardware.stage_integration import VacuumControl
    try:
        from hardware.controller import SENSOR_CONFIG
    except ImportError:
        SENSOR_CONFIG = {}


class VacuumStage:
    """Vacuum stage manual + auto sequence with shared inputs."""

    BOX_MOTORS = ["M01.1", "M01.2"]
    AUTO_BOX_RPM = 30
    AUTO_STEP_LABELS = [
        "Box move down",
        "Pump ON",
        "Inlet OPEN + evacuate",
        "Inlet CLOSE",
        "Pump OFF",
        "Hold",
        "Outlet OPEN",
        "Box move up",
        "Outlet CLOSE",
    ]

    def __init__(self, auto_mode: bool, snack, on_status=None):
        self.auto_mode = auto_mode
        self.snack = snack
        self.on_status = on_status

        # Shared manual inputs (feed both manual + auto flows)
        self.pair_distance = ft.TextField(label="Distance (mm)", value="5", dense=True)
        self.pair_slow_rpm = ft.TextField(label="Slow RPM (manual < / >)", value="10", dense=True)
        self.pair_rapid_rpm = ft.TextField(label="Rapid RPM (hold RAPID)", value="60", dense=True)
        self.evacuate_time = ft.TextField(label="Evacuate time (s)", value="10", dense=True, keyboard_type=ft.KeyboardType.NUMBER)
        self.hold_time = ft.TextField(label="Hold time (s)", value="5", dense=True, keyboard_type=ft.KeyboardType.NUMBER)

        self.status_text = ft.Text("Status: IDLE", color=ft.Colors.WHITE70)

        self._abort = False
        self._worker = None
        self._pause_event = threading.Event()
        self._pause_event.set()
        self._current_step_index = -1

        self._step_states = ["pending"] * len(self.AUTO_STEP_LABELS)
        self._step_controls = [self._build_step_chip(i, label) for i, label in enumerate(self.AUTO_STEP_LABELS)]

        # ---------------- Hardware ----------------
        self.hw = get_hardware_controller()
        self.vacuum = VacuumControl(self.hw)

    # ===================== helpers =====================
    def _build_step_chip(self, idx: int, label: str) -> ft.Control:
        text = ft.Text(label, size=13, color=ft.Colors.WHITE70, expand=True)
        indicator = ft.Container(width=10, height=10, border_radius=20, bgcolor=ft.Colors.WHITE24)
        chip = ft.Container(
            padding=ft.padding.symmetric(12, 10),
            bgcolor=ft.Colors.GREY_900,
            border_radius=12,
            border=ft.border.all(1, ft.Colors.WHITE10),
            content=ft.Row(controls=[indicator, ft.Container(width=12), text], alignment=ft.MainAxisAlignment.START),
            expand=True,
        )
        chip.data = {"text": text, "indicator": indicator, "idx": idx}
        return chip

    def _set_step_state(self, idx: int, state: str):
        if idx < 0 or idx >= len(self._step_states):
            return
        self._step_states[idx] = state
        chip = self._step_controls[idx]
        text = chip.data["text"]
        indicator = chip.data["indicator"]
        colors = {
            "pending": (ft.Colors.GREY_900, ft.Colors.WHITE38, ft.Colors.WHITE24),
            "active": (ft.Colors.BLUE_500, ft.Colors.BLACK, ft.Colors.AMBER_200),
            "done": (ft.Colors.GREEN_600, ft.Colors.BLACK, ft.Colors.LIGHT_GREEN_ACCENT),
            "aborted": (ft.Colors.RED_700, ft.Colors.WHITE, ft.Colors.RED_ACCENT),
        }
        bgcolor, tcolor, ind_color = colors.get(state, (ft.Colors.GREY_900, ft.Colors.WHITE70, ft.Colors.WHITE24))
        chip.bgcolor = ft.Colors.with_opacity(0.95, bgcolor)
        chip.border = ft.border.all(1.5 if state == "active" else 1, ft.Colors.WHITE24)
        text.color = tcolor
        text.weight = ft.FontWeight.W_600 if state == "active" else ft.FontWeight.NORMAL
        indicator.bgcolor = ind_color
        self._ui_update(chip)

    def _reset_sequence_state(self):
        self._current_step_index = -1
        for idx in range(len(self._step_states)):
            self._set_step_state(idx, "pending")

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
        # Safely attempt to update the control; when called from a
        # background thread some controls may not yet be attached to
        # a page, in which case Flet raises RuntimeError. We can
        # ignore that here because it only affects visual feedback.
        try:
            c.update()
        except RuntimeError:
            pass

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

    def _move_box(self, distance: float, direction: str):
        try:
            self.vacuum.jog_coupled(distance=distance, rpm=self.AUTO_BOX_RPM, direction=direction)
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
    def _wait_with_pause(self, seconds: float) -> bool:
        target = time.time() + seconds
        while True:
            if self._abort:
                return False
            self._pause_event.wait()
            now = time.time()
            if now >= target:
                return True
            time.sleep(0.05)

    def _run_manual_timing(self, t_evac: float, t_hold: float):
        """Run only the timing part (no box movement) for MANUAL mode using shared inputs."""
        self._abort = False
        self._pause_event.set()
        self._reset_sequence_state()

        # Ensure outlet is initially closed
        self._actuator("solenoid_valve", "CLOSE", "OUTLET SOLENOID")

        # Map into existing step chips: indices 1..6 (skip box moves)
        manual_steps = [
            (1, "Pump ON", lambda: self._actuator("pump_relay", "ON", "PUMP RELAY") or True),
            (
                2,
                f"Evacuating for {t_evac:.1f}s",
                lambda: self._actuator("solenoid_inlet", "OPEN", "INLET SOLENOID") or self._wait_with_pause(t_evac),
            ),
            (3, "Inlet CLOSE", lambda: self._actuator("solenoid_inlet", "CLOSE", "INLET SOLENOID") or True),
            (4, "Pump OFF", lambda: self._actuator("pump_relay", "OFF", "PUMP RELAY") or True),
            (5, f"Hold for {t_hold:.1f}s", lambda: self._wait_with_pause(t_hold)),
            (6, "Outlet OPEN", lambda: self._actuator("solenoid_valve", "OPEN", "OUTLET SOLENOID") or True),
        ]

        for idx, label, action in manual_steps:
            if self._abort:
                self._set_step_state(idx, "aborted")
                self._set_status("ABORTED")
                return

            self._current_step_index = idx
            self._set_step_state(idx, "active")
            self._set_status(label)
            if self.on_status:
                # Use a coarse fraction based on this subset of steps
                self.on_status((idx + 0.1) / len(self.AUTO_STEP_LABELS), f"Vacuum (manual): {label}")

            self._pause_event.wait()
            try:
                if action() is False:
                    self._set_step_state(idx, "aborted")
                    self._set_status("ABORTED")
                    return
            except RuntimeError as err:
                self.snack(str(err))
                self._set_step_state(idx, "aborted")
                self._set_status("ERROR")
                return

            self._set_step_state(idx, "done")

        self._set_status("Manual timing complete")
        if self.on_status:
            self.on_status(1.0, "Vacuum: manual timing complete")

    def _run_vacuum_sequence(self, distance: float, t_evac: float, t_hold: float):
        self._abort = False
        self._pause_event.set()
        self._reset_sequence_state()

        self._actuator("solenoid_valve", "CLOSE", "OUTLET SOLENOID")

        steps = [
            ("Box moving down", lambda: self._move_box(distance, "FORWARD")),
            ("Pump ON", lambda: self._actuator("pump_relay", "ON", "PUMP RELAY") or True),
            (
                f"Evacuating for {t_evac:.1f}s",
                lambda: self._actuator("solenoid_inlet", "OPEN", "INLET SOLENOID") or self._wait_with_pause(t_evac),
            ),
            ("Inlet CLOSE", lambda: self._actuator("solenoid_inlet", "CLOSE", "INLET SOLENOID") or True),
            ("Pump OFF", lambda: self._actuator("pump_relay", "OFF", "PUMP RELAY") or True),
            (f"Hold for {t_hold:.1f}s", lambda: self._wait_with_pause(t_hold)),
            ("Outlet OPEN", lambda: self._actuator("solenoid_valve", "OPEN", "OUTLET SOLENOID") or True),
            ("Box moving up", lambda: self._move_box(distance, "BACKWARD")),
            ("Outlet CLOSE", lambda: self._actuator("solenoid_valve", "CLOSE", "OUTLET SOLENOID") or True),
        ]

        for idx, (label, action) in enumerate(steps):
            if self._abort:
                self._set_step_state(idx, "aborted")
                self._set_status("ABORTED")
                return

            self._current_step_index = idx
            self._set_step_state(idx, "active")
            self._set_status(label)
            if self.on_status:
                self.on_status((idx + 0.1) / len(steps), f"Vacuum: {label}")

            self._pause_event.wait()
            try:
                if action() is False:
                    self._set_step_state(idx, "aborted")
                    self._set_status("ABORTED")
                    return
            except RuntimeError as err:
                self.snack(str(err))
                self._set_step_state(idx, "aborted")
                self._set_status("ERROR")
                return

            self._set_step_state(idx, "done")

        self._set_status("Sequence complete")
        if self.on_status:
            self.on_status(1.0, "Vacuum: sequence complete")

    def start_auto_vacuum(self, e=None):
        if not self._ensure_auto():
            return

        if self._worker is not None and self._worker.is_alive():
            self.snack("Vacuum sequence already running.")
            return

        distance = self._read_positive(self.pair_distance)
        t_evac = self._read_positive(self.evacuate_time)
        t_hold = self._read_positive(self.hold_time)
        if distance is None:
            self.snack("Invalid distance for auto sequence")
            return
        if t_evac is None:
            self.snack("Invalid evacuate time")
            return
        if t_hold is None:
            self.snack("Invalid hold time")
            return

        self._worker = threading.Thread(
            target=self._run_vacuum_sequence,
            args=(distance, t_evac, t_hold),
            daemon=True,
        )
        self._worker.start()

    def stop_auto_vacuum(self, e=None):
        self._abort = True
        self._pause_event.set()

        # Safe off
        self._actuator("solenoid_inlet", "CLOSE", "INLET SOLENOID")
        self._actuator("solenoid_valve", "CLOSE", "OUTLET SOLENOID")
        self._actuator("pump_relay", "OFF", "PUMP RELAY")

        self._set_status("ABORTED by user")
        self._reset_sequence_state()
        if self.on_status:
            self.on_status(0.0, "Vacuum: aborted")

    def start_manual_vacuum(self, e=None):
        """Start timing-only vacuum using current evacuate/hold values in MANUAL mode.

        Box position is assumed to be set by the user via coupled motor controls.
        """
        if self.auto_mode:
            self.snack("Switch to MANUAL to run manual timing.")
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
            target=self._run_manual_timing,
            args=(t_evac, t_hold),
            daemon=True,
        )
        self._worker.start()

    def pause_auto_sequence(self):
        if self._worker and self._worker.is_alive():
            self._pause_event.clear()
            self._set_status("Paused")

    def resume_auto_sequence(self):
        if self._worker and self._worker.is_alive():
            self._pause_event.set()
            if self._current_step_index >= 0:
                label = self.AUTO_STEP_LABELS[self._current_step_index]
                self._set_status(f"Resumed: {label}")

    def reset_auto_sequence(self):
        self.stop_auto_vacuum()
        self._reset_sequence_state()

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
                ft.Container(height=16),
                ft.Divider(color=ft.Colors.WHITE12),
                ft.Container(height=8),
                ft.Text("Vacuum timing inputs (shared)", color=ft.Colors.WHITE70, size=14, weight=ft.FontWeight.W_600),
                ft.Container(height=8),
                self.evacuate_time,
                ft.Container(height=10),
                self.hold_time,
                ft.Container(height=12),
                ft.Row(
                    controls=[
                        ft.ElevatedButton(
                            "RUN VACUUM (manual)",
                            icon=ft.Icons.PLAY_ARROW,
                            on_click=self.start_manual_vacuum,
                        ),
                    ]
                ),
            ]
        )

    def auto_sequence_ui(self) -> ft.Control:
        return ft.Column(
            spacing=10,
            controls=[
                ft.Text("Auto sequence status", color=ft.Colors.WHITE70, size=16, weight=ft.FontWeight.W_600),
                ft.Column(controls=self._step_controls, spacing=8, tight=True),
                ft.Text(
                    "Use the dashboard controls to START / PAUSE / RESUME this stage.",
                    size=12,
                    color=ft.Colors.WHITE54,
                ),
                self.status_text,
            ],
        )

    # ===================== final view =====================
    def view(self) -> ft.Control:
        return ft.ResponsiveRow(
            columns=12,
            controls=[
                ft.Container(col={"xs": 12, "md": 7}, content=self._panel("Motors 01.1 + 01.2 – Manual control", self.coupled_motors_ui())),
                ft.Container(col={"xs": 12, "md": 5}, content=self._panel("Auto vacuum sequence", self.auto_sequence_ui())),
            ],
        )
