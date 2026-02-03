"""
Hardware Integration Layer for Stage Classes
Bridges UI commands to actual GPIO/hardware operations
"""

import time
import threading
from typing import Callable, Optional, List
import logging

logger = logging.getLogger(__name__)


class MotorController:
    """High-level motor control with synchronization"""

    def __init__(self, hw_controller, motor_ids: List[str]):
        """
        Args:
            hw_controller: HardwareController instance
            motor_ids: List of motor IDs to control together
        """
        self.hw = hw_controller
        self.motor_ids = motor_ids
        self.is_running = False

    def jog_distance(self, distance_mm: float, rpm: float, direction: str, progress_callback: Optional[Callable] = None):
        """
        Jog motors for specific distance
        Args:
            distance_mm: Distance to move in mm
            rpm: RPM to use
            direction: 'FORWARD' or 'BACKWARD'
            progress_callback: callback(progress_fraction, status_msg)
        """
        self.is_running = True

        try:
            # Start all motors
            for motor_id in self.motor_ids:
                self.hw.motor_forward(motor_id, rpm) if direction == "FORWARD" else self.hw.motor_backward(motor_id, rpm)

            # Estimate time based on speed (requires calibration)
            estimated_time = (distance_mm / rpm) * 0.1  # Rough estimate
            start_time = time.time()

            # Simulate movement (TODO: integrate encoder feedback)
            while self.is_running:
                elapsed = time.time() - start_time
                progress = min(1.0, elapsed / estimated_time)

                if progress_callback:
                    progress_callback(
                        progress,
                        f"Moving {distance_mm}mm @ {rpm} RPM..."
                    )

                if progress >= 1.0:
                    break

                time.sleep(0.05)

            # Stop motors
            for motor_id in self.motor_ids:
                self.hw.motor_stop(motor_id)

            if progress_callback:
                progress_callback(1.0, "Movement complete")

        except Exception as e:
            logger.error(f"Motor jog error: {e}")
            self.stop()
            raise

        finally:
            self.is_running = False

    def jog_distance_async(self, distance_mm: float, rpm: float, direction: str, progress_callback: Optional[Callable] = None):
        """Async version of jog_distance"""
        thread = threading.Thread(
            target=self.jog_distance,
            args=(distance_mm, rpm, direction, progress_callback),
            daemon=True
        )
        thread.start()
        return thread

    def stop(self):
        """Stop all motors"""
        self.is_running = False
        for motor_id in self.motor_ids:
            self.hw.motor_stop(motor_id)


class DispenserControl:
    """Dispenser-specific hardware control"""

    def __init__(self, hw_controller):
        self.hw = hw_controller
        self.m001_controller = MotorController(hw_controller, ["M001"])

    def dispense_auto_sequence(self, measurements: List[dict], progress_callback: Optional[Callable] = None):
        """
        Execute automatic dispense sequence
        Args:
            measurements: List of {'distance': mm, 'unit': str}
            progress_callback: callback(progress_fraction, status_msg)
        """
        try:
            total_steps = len(measurements)

            for step, meas in enumerate(measurements):
                distance = float(meas.get("distance", 5))
                rpm = 100  # Default speed for auto mode

                progress = step / total_steps

                if progress_callback:
                    progress_callback(progress, f"Step {step + 1}/{total_steps}: Moving {distance}mm")

                self.m001_controller.jog_distance(distance, rpm, "FORWARD")
                time.sleep(0.5)  # Pause between steps

            if progress_callback:
                progress_callback(1.0, "Dispense sequence complete")

        except Exception as e:
            logger.error(f"Dispense sequence error: {e}")
            raise

    def jog_m001(self, distance: float, rpm: float, direction: str, progress_callback: Optional[Callable] = None):
        """Jog M001 motor"""
        self.m001_controller.jog_distance(distance, rpm, direction, progress_callback)

    def rapid_stop(self):
        """Rapid stop M001"""
        self.m001_controller.stop()


class VacuumControl:
    """Vacuum-specific hardware control"""

    def __init__(self, hw_controller):
        self.hw = hw_controller
        self.coupled_controller = MotorController(hw_controller, ["M01.1", "M01.2"])

    def vacuum_sequence(self, pressure_target: float = 80, progress_callback: Optional[Callable] = None):
        """
        Execute vacuum sequence with pressure monitoring
        Args:
            pressure_target: Target pressure in kPa
            progress_callback: callback(progress_fraction, status_msg)
        """
        try:
            # Start vacuum pump (coupled motors)
            rpm = 150
            self.coupled_controller.hw.motor_forward("M01.1", rpm)
            self.coupled_controller.hw.motor_forward("M01.2", rpm)

            # Monitor pressure
            start_time = time.time()
            timeout = 30  # seconds

            while time.time() - start_time < timeout:
                reading = self.hw.get_sensor_reading("pressure")

                if reading:
                    current_pressure = reading.value
                    progress = min(1.0, current_pressure / pressure_target)

                    if progress_callback:
                        progress_callback(
                            progress,
                            f"Pressure: {current_pressure:.1f}/{pressure_target} kPa"
                        )

                    if current_pressure >= pressure_target:
                        break

                time.sleep(0.1)

            # Stop vacuum
            self.coupled_controller.stop()

            if progress_callback:
                progress_callback(1.0, "Vacuum target reached")

        except Exception as e:
            logger.error(f"Vacuum sequence error: {e}")
            raise

    def jog_coupled(self, distance: float, rpm: float, direction: str, progress_callback: Optional[Callable] = None):
        """Jog coupled motors M01.1 + M01.2"""
        self.coupled_controller.jog_distance(distance, rpm, direction, progress_callback)


class HeatingControl:
    """Heating stage hardware control"""

    def __init__(self, hw_controller):
        self.hw = hw_controller
        self.motor_controller = MotorController(hw_controller, ["M02"])

    def heating_sequence(self, target_temp: float = 60, duration: int = 300, progress_callback: Optional[Callable] = None):
        """
        Execute heating sequence with temperature monitoring
        Args:
            target_temp: Target temperature in Celsius
            duration: Heating duration in seconds
            progress_callback: callback(progress_fraction, status_msg)
        """
        try:
            self.motor_controller.hw.motor_forward("M02", 100)

            start_time = time.time()
            elapsed = 0

            while elapsed < duration:
                reading = self.hw.get_sensor_reading("temperature")
                current_temp = reading.value if reading else 0

                progress = elapsed / duration
                remaining = duration - elapsed

                if progress_callback:
                    progress_callback(
                        progress,
                        f"Heating: {current_temp:.1f}°C (target: {target_temp}°C) - {remaining:.0f}s remaining"
                    )

                if current_temp >= target_temp:
                    break

                time.sleep(1)
                elapsed = time.time() - start_time

            self.motor_controller.stop()

            if progress_callback:
                progress_callback(1.0, "Heating complete")

        except Exception as e:
            logger.error(f"Heating sequence error: {e}")
            raise


class PackagingControl:
    """Packaging stage hardware control"""

    def __init__(self, hw_controller):
        self.hw = hw_controller
        self.motor_controller = MotorController(hw_controller, ["M03"])

    def packaging_sequence(self, cycles: int = 3, progress_callback: Optional[Callable] = None):
        """
        Execute packaging sequence
        Args:
            cycles: Number of packaging cycles
            progress_callback: callback(progress_fraction, status_msg)
        """
        try:
            for cycle in range(cycles):
                progress = cycle / cycles

                if progress_callback:
                    progress_callback(progress, f"Packaging cycle {cycle + 1}/{cycles}")

                self.motor_controller.hw.motor_forward("M03", 150)
                time.sleep(2)
                self.motor_controller.stop()
                time.sleep(1)

            if progress_callback:
                progress_callback(1.0, "Packaging complete")

        except Exception as e:
            logger.error(f"Packaging sequence error: {e}")
            raise


class SterilizationControl:
    """Sterilization stage hardware control"""

    def __init__(self, hw_controller):
        self.hw = hw_controller

    def sterilization_sequence(self, duration: int = 600, progress_callback: Optional[Callable] = None):
        """
        Execute sterilization sequence with temperature and pressure monitoring
        Args:
            duration: Sterilization duration in seconds (10 minutes default)
            progress_callback: callback(progress_fraction, status_msg)
        """
        try:
            start_time = time.time()
            elapsed = 0

            while elapsed < duration:
                progress = elapsed / duration

                temp_reading = self.hw.get_sensor_reading("temperature")
                pressure_reading = self.hw.get_sensor_reading("pressure")

                temp = temp_reading.value if temp_reading else 0
                pressure = pressure_reading.value if pressure_reading else 0

                remaining = duration - elapsed

                if progress_callback:
                    progress_callback(
                        progress,
                        f"Sterilizing: {temp:.1f}°C, {pressure:.1f}kPa - {remaining:.0f}s remaining"
                    )

                time.sleep(1)
                elapsed = time.time() - start_time

            if progress_callback:
                progress_callback(1.0, "Sterilization complete")

        except Exception as e:
            logger.error(f"Sterilization sequence error: {e}")
            raise
