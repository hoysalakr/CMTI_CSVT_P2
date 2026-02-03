"""
Hardware Abstraction Layer (HAL)
Interfaces with GPIO, I2C sensors, and motor controllers via RPi 5
"""

import time
import threading
from typing import Dict, Callable, Optional
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)

# Try to import RPi GPIO library
try:
    import RPi.GPIO as GPIO
    HARDWARE_AVAILABLE = True
except ImportError:
    HARDWARE_AVAILABLE = False
    logger.warning("RPi.GPIO not available - running in simulation mode")

try:
    import board
    import busio
    # The code is importing the `AnalogIn` module from the `adafruit_ads1x15` package in Python. This
    # module is likely used for interacting with analog input devices connected to the ADS1x15
    # analog-to-digital converter from Adafruit.
    import adafruit_ads1x15.analog_in as AnalogIn
    from adafruit_ads1x15.ads1115 import ADS1115
    I2C_AVAILABLE = True
except ImportError:
    I2C_AVAILABLE = False
    logger.warning("Adafruit I2C libraries not available")

from hardware.gpio_config import MOTOR_CONFIG, SENSOR_CONFIG, ACTUATOR_CONFIG, PWM_BASE_FREQUENCY


@dataclass
class SensorReading:
    """Sensor data container"""
    sensor_name: str
    value: float
    unit: str
    timestamp: float


class Motor:
    """Motor controller with PWM speed control"""

    def __init__(self, motor_id: str, config: Dict):
        self.motor_id = motor_id
        self.name = config["name"]
        self.dir_pin1 = config["direction_pin1"]
        self.dir_pin2 = config["direction_pin2"]
        self.pwm_pin = config["pwm_pin"]
        self.max_rpm = config["max_rpm"]

        self.current_rpm = 0
        self.direction = "STOP"  # STOP, FORWARD, BACKWARD
        self.pwm = None
        self.runtime = 0
        self.start_time = None

        if HARDWARE_AVAILABLE:
            GPIO.setmode(GPIO.BCM)
            GPIO.setup(self.dir_pin1, GPIO.OUT)
            GPIO.setup(self.dir_pin2, GPIO.OUT)
            GPIO.setup(self.pwm_pin, GPIO.OUT)
            GPIO.output(self.dir_pin1, GPIO.LOW)
            GPIO.output(self.dir_pin2, GPIO.LOW)

            # Create PWM object
            self.pwm = GPIO.PWM(self.pwm_pin, config["pwm_frequency"])
            self.pwm.start(0)

    def set_speed(self, rpm: float, direction: str = "FORWARD"):
        """
        Set motor speed and direction
        Args:
            rpm: RPM (0 to max_rpm)
            direction: 'FORWARD', 'BACKWARD', 'STOP'
        """
        rpm = max(0, min(rpm, self.max_rpm))
        duty_cycle = (rpm / self.max_rpm) * 100

        if direction == "STOP" or rpm == 0:
            duty_cycle = 0
            direction = "STOP"

        self.current_rpm = rpm
        self.direction = direction

        if HARDWARE_AVAILABLE and self.pwm:
            if direction == "FORWARD":
                GPIO.output(self.dir_pin1, GPIO.HIGH)
                GPIO.output(self.dir_pin2, GPIO.LOW)
            elif direction == "BACKWARD":
                GPIO.output(self.dir_pin1, GPIO.LOW)
                GPIO.output(self.dir_pin2, GPIO.HIGH)
            else:  # STOP
                GPIO.output(self.dir_pin1, GPIO.LOW)
                GPIO.output(self.dir_pin2, GPIO.LOW)

            self.pwm.ChangeDutyCycle(max(5, min(95, duty_cycle)))

        if self.start_time is None and direction != "STOP":
            self.start_time = time.time()

        logger.info(f"{self.name}: {direction} @ {rpm:.0f} RPM")

    def stop(self):
        """Stop motor immediately"""
        self.set_speed(0, "STOP")

    def get_runtime(self) -> float:
        """Get runtime in seconds"""
        if self.start_time:
            return time.time() - self.start_time
        return 0

    def cleanup(self):
        """Cleanup GPIO"""
        if HARDWARE_AVAILABLE and self.pwm:
            self.pwm.stop()
            GPIO.output(self.dir_pin1, GPIO.LOW)
            GPIO.output(self.dir_pin2, GPIO.LOW)


class SensorReader:
    """Reads analog and digital sensors"""

    def __init__(self):
        self.readings: Dict[str, SensorReading] = {}
        self.i2c = None
        self.ads = None
        self.running = False

        if I2C_AVAILABLE:
            try:
                self.i2c = busio.I2C(board.SCL, board.SDA)
                self.ads = ADS1115(self.i2c)
                logger.info("I2C ADC initialized")
            except Exception as e:
                logger.error(f"Failed to initialize I2C: {e}")

        if HARDWARE_AVAILABLE:
            GPIO.setmode(GPIO.BCM)
            # Setup digital sensor pins
            for sensor_id, config in SENSOR_CONFIG.items():
                if config["type"] == "digital":
                    GPIO.setup(config["pin"], GPIO.IN)

    def read_pressure(self) -> Optional[float]:
        """Read pressure from I2C sensor"""
        if not self.ads:
            return None

        try:
            channel = AnalogIn.AnalogIn(self.ads, AnalogIn.P0)
            # Convert voltage to pressure (0-100 kPa)
            pressure = (channel.voltage / 3.3) * 100
            return max(0, min(100, pressure))
        except Exception as e:
            logger.error(f"Pressure read error: {e}")
            return None

    def read_temperature(self) -> Optional[float]:
        """Read temperature from I2C sensor"""
        if not self.ads:
            return None

        try:
            channel = AnalogIn.AnalogIn(self.ads, AnalogIn.P1)
            # Simple linear conversion: 0V = -20°C, 3.3V = 120°C
            temp = -20 + (channel.voltage / 3.3) * 140
            return max(-20, min(120, temp))
        except Exception as e:
            logger.error(f"Temperature read error: {e}")
            return None

    def read_proximity(self, sensor_num: int) -> Optional[bool]:
        """Read digital proximity sensor"""
        if not HARDWARE_AVAILABLE:
            return None

        pin = SENSOR_CONFIG[f"proximity_{sensor_num}"]["pin"]
        try:
            return bool(GPIO.input(pin))
        except Exception as e:
            logger.error(f"Proximity sensor {sensor_num} read error: {e}")
            return None

    def update_readings(self):
        """Update all sensor readings"""
        readings_dict = {}

        # Pressure
        pressure = self.read_pressure()
        if pressure is not None:
            readings_dict["pressure"] = SensorReading(
                "Pressure Sensor",
                pressure,
                "kPa",
                time.time()
            )

        # Temperature
        temp = self.read_temperature()
        if temp is not None:
            readings_dict["temperature"] = SensorReading(
                "Temperature Sensor",
                temp,
                "°C",
                time.time()
            )

        # Proximity sensors
        for i in [1, 2]:
            prox = self.read_proximity(i)
            if prox is not None:
                readings_dict[f"proximity_{i}"] = SensorReading(
                    f"Proximity Sensor {i}",
                    float(prox),
                    "bool",
                    time.time()
                )

        self.readings = readings_dict
        return self.readings

    def get_reading(self, sensor_id: str) -> Optional[SensorReading]:
        """Get latest reading for a sensor"""
        return self.readings.get(sensor_id)

    def start_polling(self, interval: float = 0.1, callback: Optional[Callable] = None):
        """Start continuous sensor polling"""
        self.running = True

        def poll():
            while self.running:
                self.update_readings()
                if callback:
                    callback(self.readings)
                time.sleep(interval)

        thread = threading.Thread(target=poll, daemon=True)
        thread.start()

    def stop_polling(self):
        """Stop sensor polling"""
        self.running = False

    def cleanup(self):
        """Cleanup I2C and GPIO"""
        self.stop_polling()
        if self.i2c:
            self.i2c.deinit()


class Actuator:
    """Digital actuator (solenoid valve, relay, etc.)"""

    def __init__(self, actuator_id: str, config: Dict):
        self.actuator_id = actuator_id
        self.name = config["name"]
        self.pin = config["pin"]
        self.is_output = config["type"] == "digital_output"
        self.state = False

        if HARDWARE_AVAILABLE:
            GPIO.setmode(GPIO.BCM)
            if self.is_output:
                GPIO.setup(self.pin, GPIO.OUT)
                GPIO.output(self.pin, GPIO.LOW)
            else:
                GPIO.setup(self.pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)

    def activate(self):
        """Turn on actuator"""
        if self.is_output and HARDWARE_AVAILABLE:
            GPIO.output(self.pin, GPIO.HIGH)
        self.state = True
        logger.info(f"{self.name}: ON")

    def deactivate(self):
        """Turn off actuator"""
        if self.is_output and HARDWARE_AVAILABLE:
            GPIO.output(self.pin, GPIO.LOW)
        self.state = False
        logger.info(f"{self.name}: OFF")

    def get_state(self) -> bool:
        """Read actuator state"""
        if not HARDWARE_AVAILABLE:
            return self.state

        return bool(GPIO.input(self.pin)) if not self.is_output else self.state

    def cleanup(self):
        """Cleanup GPIO"""
        if self.is_output:
            self.deactivate()


class HardwareController:
    """Main hardware control interface"""

    def __init__(self):
        self.motors: Dict[str, Motor] = {}
        self.sensors = SensorReader()
        self.actuators: Dict[str, Actuator] = {}

        # Initialize motors
        for motor_id, config in MOTOR_CONFIG.items():
            self.motors[motor_id] = Motor(motor_id, config)

        # Initialize actuators
        for actuator_id, config in ACTUATOR_CONFIG.items():
            self.actuators[actuator_id] = Actuator(actuator_id, config)

        logger.info("HardwareController initialized")

    def motor_forward(self, motor_id: str, rpm: float):
        """Run motor forward"""
        if motor_id in self.motors:
            self.motors[motor_id].set_speed(rpm, "FORWARD")

    def motor_backward(self, motor_id: str, rpm: float):
        """Run motor backward"""
        if motor_id in self.motors:
            self.motors[motor_id].set_speed(rpm, "BACKWARD")

    def motor_stop(self, motor_id: str):
        """Stop motor"""
        if motor_id in self.motors:
            self.motors[motor_id].stop()

    def motor_jog(self, motor_id: str, distance_mm: float, rpm: float, direction: str):
        """Jog motor for specific distance (stub - needs encoder integration)"""
        if motor_id not in self.motors:
            return

        motor = self.motors[motor_id]
        motor.set_speed(rpm, direction)
        logger.info(f"Jogging {motor_id}: {distance_mm}mm @ {rpm} RPM {direction}")
        # TODO: Integrate encoder or step counter for distance measurement

    def actuator_on(self, actuator_id: str):
        """Turn on actuator"""
        if actuator_id in self.actuators:
            self.actuators[actuator_id].activate()

    def actuator_off(self, actuator_id: str):
        """Turn off actuator"""
        if actuator_id in self.actuators:
            self.actuators[actuator_id].deactivate()

    def get_sensor_reading(self, sensor_id: str) -> Optional[SensorReading]:
        """Get sensor reading"""
        return self.sensors.get_reading(sensor_id)

    def start_sensor_polling(self, callback: Optional[Callable] = None):
        """Start continuous sensor monitoring"""
        self.sensors.start_polling(callback=callback)

    def emergency_stop(self):
        """Emergency stop - stop all motors"""
        logger.critical("EMERGENCY STOP activated")
        for motor_id in self.motors:
            self.motor_stop(motor_id)
        for actuator_id in self.actuators:
            self.actuator_off(actuator_id)

    def cleanup(self):
        """Cleanup all hardware"""
        logger.info("Cleaning up hardware...")
        for motor in self.motors.values():
            motor.cleanup()
        for actuator in self.actuators.values():
            actuator.cleanup()
        self.sensors.cleanup()
        if HARDWARE_AVAILABLE:
            GPIO.cleanup()


# Global hardware controller instance
_hw_controller = None


def get_hardware_controller() -> HardwareController:
    """Get or create hardware controller singleton"""
    global _hw_controller
    if _hw_controller is None:
        _hw_controller = HardwareController()
    return _hw_controller
