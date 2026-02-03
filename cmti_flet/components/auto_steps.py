import flet as ft
from dataclasses import dataclass
from typing import Callable, List, Optional


@dataclass
class Step:
    measurement: float
    unit: str = "mm"


class AutoStepsPanel:
    """
    Reusable Auto panel:
    - dynamic rows (Measurement + Unit)
    - Add step / Remove step
    - ENTER validation + submit callback
    - Keeps state internally (textfields persist as long as object persists)
    """

    def __init__(
        self,
        snack: Callable[[str], None],
        title: str = "Auto Inputs",
        default_unit: str = "mm",
        on_submit: Optional[Callable[[List[Step]], None]] = None,
        require_auto_mode: Optional[Callable[[], bool]] = None,  # return True if AUTO is enabled
    ):
        self.snack = snack
        self.title = title
        self.default_unit = default_unit
        self.on_submit = on_submit
        self.require_auto_mode = require_auto_mode

        # list of (measurement_tf, unit_tf)
        self.rows: List[tuple[ft.TextField, ft.TextField]] = []
        self._add_row()  # start with 1 row

    def _add_row(self):
        m = ft.TextField(
            label="Measurement",
            hint_text="value",
            dense=True,
            keyboard_type=ft.KeyboardType.NUMBER,
        )
        u = ft.TextField(
            label="Unit",
            hint_text=self.default_unit,
            value=self.default_unit,
            dense=True,
        )
        self.rows.append((m, u))

    def _remove_row(self, idx: int, list_view: ft.ListView):
        if len(self.rows) <= 1:
            self.snack("At least 1 step is required.")
            return

        self.rows.pop(idx)
        list_view.controls = self._rows_controls(list_view)
        if list_view.page is not None:
            list_view.update()

    def _rows_controls(self, list_view: ft.ListView):
        controls = []
        for i, (m, u) in enumerate(self.rows, start=1):
            controls.append(
                ft.Row(
                    vertical_alignment=ft.CrossAxisAlignment.START,
                    controls=[
                        ft.Container(width=34, content=ft.Text(f"{i}.", color=ft.Colors.WHITE70)),
                        ft.Container(expand=True, content=m),
                        ft.IconButton(
                            icon=ft.Icons.CLOSE,
                            tooltip="Remove step",
                            on_click=(lambda e, k=i - 1: self._remove_row(k, list_view)),
                        ),
                        ft.Container(width=130, content=u),
                    ],
                )
            )
            controls.append(ft.Container(height=10))
        return controls

    def _submit(self):
        # Enforce AUTO mode if hook is provided
        if self.require_auto_mode is not None:
            if not self.require_auto_mode():
                self.snack("Switch is MANUAL. Turn ON AUTO to submit auto steps.")
                return

        steps: List[Step] = []

        for idx, (m, u) in enumerate(self.rows, start=1):
            raw = (m.value or "").strip()
            if raw == "":
                self.snack(f"Row {idx}: measurement is empty")
                return

            try:
                val = float(raw)
            except:
                self.snack(f"Row {idx}: measurement must be a number")
                return

            unit = (u.value or "").strip() or self.default_unit
            steps.append(Step(measurement=val, unit=unit))

        self.snack(f"{self.title}: Submitted {len(steps)} step(s)")
        if self.on_submit:
            self.on_submit(steps)

    def view(self) -> ft.Control:
        list_view = ft.ListView(expand=True, spacing=0)
        list_view.controls = self._rows_controls(list_view)

        def refresh_rows():
            list_view.controls = self._rows_controls(list_view)
            if list_view.page is not None:
                list_view.update()

        def add_step(e):
            self._add_row()
            refresh_rows()

        return ft.Container(
            padding=14,
            bgcolor=ft.Colors.BLACK54,
            border=ft.border.all(1, ft.Colors.WHITE12),
            border_radius=14,
            content=ft.Column(
                expand=True,
                controls=[
                    ft.Text(self.title, size=18, weight=ft.FontWeight.W_700),
                    ft.Container(height=12),
                    ft.Container(expand=True, content=list_view),
                    ft.Container(height=12),
                    ft.Row(
                        controls=[
                            ft.ElevatedButton(
                                "Add step",
                                icon=ft.Icons.ADD,
                                on_click=add_step,
                                style=ft.ButtonStyle(padding=ft.padding.symmetric(16, 12)),
                            ),
                            ft.Container(width=12),
                            ft.ElevatedButton(
                                "ENTER",
                                on_click=lambda e: self._submit(),
                                style=ft.ButtonStyle(padding=ft.padding.symmetric(18, 12)),
                            ),
                        ]
                    ),
                ],
            ),
        )
