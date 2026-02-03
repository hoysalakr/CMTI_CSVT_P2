"""
GPIO Pin Configuration for Raspberry Pi 5 - CMTI System
========================================================

Motor Control:
  - M001 (Dispenser):     GPIO 17, 27 (Direction), GPIO 22 (PWM Speed)
  - M01.1 (Vacuum Left):  GPIO 23, 24 (Direction), GPIO 25 (PWM Speed)
  - M01.2 (Vacuum Right): GPIO 10, 9  (Direction), GPIO 11 (PWM Speed)
  - M02 (Heating):        GPIO 6,  5  (Direction), GPIO 12 (PWM Speed)
  - M03 (Packaging):      GPIO 19, 26 (Direction), GPIO 13 (PWM Speed)

Sensor Inputs:
  - Pressure Sensor (Vacuum): GPIO 14 (ADC/I2C)
  - Temperature Sensor:       GPIO 15 (ADC/I2C)
  - Proximity Sensors:        GPIO 20, 21 (Digital)

Actuators:
  - Solenoid Valve:           GPIO 16 (Digital)
  - Emergency Stop:           GPIO 8  (Digital Input)

PWM Configuration:
  - Frequency: 1000 Hz (standard for motor control)
  - Duty Cycle: 0-100%
"""

# ============ MOTOR GPIO PINS ============
MOTOR_CONFIG = {
    "M001": {
        "name": "Dispenser Motor",
        "direction_pin1": 17,  # Forward
        "direction_pin2": 27,  # Backward
        "pwm_pin": 22,         # PWM for speed
        "pwm_frequency": 1000,
        "max_rpm": 3000,
    },
    "M01.1": {
        "name": "Vacuum Motor Left",
        "direction_pin1": 23,
        "direction_pin2": 24,
        "pwm_pin": 25,
        "pwm_frequency": 1000,
        "max_rpm": 3000,
    },
    "M01.2": {
        "name": "Vacuum Motor Right",
        "direction_pin1": 10,
        "direction_pin2": 9,
        "pwm_pin": 11,
        "pwm_frequency": 1000,
        "max_rpm": 3000,
    },
    "M02": {
        "name": "Heating Motor",
        "direction_pin1": 6,
        "direction_pin2": 5,
        "pwm_pin": 12,
        "pwm_frequency": 1000,
        "max_rpm": 2000,
    },
    "M03": {
        "name": "Packaging Motor",
        "direction_pin1": 19,
        "direction_pin2": 26,
        "pwm_pin": 13,
        "pwm_frequency": 1000,
        "max_rpm": 2500,
    },
}

# ============ SENSOR GPIO PINS ============
SENSOR_CONFIG = {
    "pressure": {
        "name": "Pressure Sensor",
        "pin": 14,
        "type": "analog",  # I2C ADC
        "i2c_address": 0x48,
        "min_value": 0,
        "max_value": 100,  # kPa
    },
    "temperature": {
        "name": "Temperature Sensor",
        "pin": 15,
        "type": "analog",  # I2C ADC
        "i2c_address": 0x48,
        "min_value": -20,
        "max_value": 120,  # Celsius
    },
    "proximity_1": {
        "name": "Proximity Sensor 1",
        "pin": 20,
        "type": "digital",
    },
    "proximity_2": {
        "name": "Proximity Sensor 2",
        "pin": 21,
        "type": "digital",
    },
}

# ============ ACTUATOR GPIO PINS ============
ACTUATOR_CONFIG = {
    "solenoid_valve": {
        "name": "Solenoid Valve",
        "pin": 16,
        "type": "digital_output",
        "default": "off",
    },
    "emergency_stop": {
        "name": "Emergency Stop Button",
        "pin": 8,
        "type": "digital_input",
        "pull_up": True,
    },
}

# ============ I2C CONFIGURATION ============
I2C_CONFIG = {
    "bus": 1,  # RPi 5: /dev/i2c-1 (pins GPIO 2=SDA, GPIO 3=SCL)
    "frequency": 100000,  # 100 kHz
}

# ============ SPI CONFIGURATION (if needed) ============
SPI_CONFIG = {
    "bus": 0,  # CE0
    "device": 0,
    "speed": 1000000,  # 1 MHz
}

# ============ PWM CONFIGURATION ============
PWM_BASE_FREQUENCY = 1000  # Hz
PWM_MIN_DUTY = 5  # Minimum duty cycle to prevent motor stalling
PWM_MAX_DUTY = 95  # Maximum duty cycle (leave headroom)

# ============ SAFETY LIMITS ============
SAFETY_CONFIG = {
    "max_motor_runtime": 300,  # seconds (5 minutes)
    "emergency_stop_timeout": 5,  # seconds
    "sensor_read_interval": 0.1,  # seconds (100ms)
}
