"""
Hardware module initialization
"""

try:
    from .gpio_config import (
        MOTOR_CONFIG,
        SENSOR_CONFIG,
        ACTUATOR_CONFIG,
        I2C_CONFIG,
        SPI_CONFIG,
        PWM_BASE_FREQUENCY,
        SAFETY_CONFIG,
    )
    from .controller import (
        HardwareController,
        Motor,
        SensorReader,
        Actuator,
        SensorReading,
        get_hardware_controller,
        HARDWARE_AVAILABLE,
        I2C_AVAILABLE,
    )
except ImportError:  # Fallback if package not resolved relatively
    from hardware.gpio_config import (  # type: ignore
        MOTOR_CONFIG,
        SENSOR_CONFIG,
        ACTUATOR_CONFIG,
        I2C_CONFIG,
        SPI_CONFIG,
        PWM_BASE_FREQUENCY,
        SAFETY_CONFIG,
    )
    from hardware.controller import (  # type: ignore
        HardwareController,
        Motor,
        SensorReader,
        Actuator,
        SensorReading,
        get_hardware_controller,
        HARDWARE_AVAILABLE,
        I2C_AVAILABLE,
    )

__all__ = [
    "MOTOR_CONFIG",
    "SENSOR_CONFIG",
    "ACTUATOR_CONFIG",
    "I2C_CONFIG",
    "SPI_CONFIG",
    "PWM_BASE_FREQUENCY",
    "SAFETY_CONFIG",
    "HardwareController",
    "Motor",
    "SensorReader",
    "Actuator",
    "SensorReading",
    "get_hardware_controller",
    "HARDWARE_AVAILABLE",
    "I2C_AVAILABLE",
]
