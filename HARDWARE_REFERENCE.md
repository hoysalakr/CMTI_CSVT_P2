# CMTI Hardware Integration - Quick Reference

## GPIO Pin Assignments Summary

### Motor Control (5 Motors with L298N Drivers)

```
M001 (Dispenser):
  └─ Dir1: GPIO 17, Dir2: GPIO 27, PWM: GPIO 22

M01.1 (Vacuum Left):
  └─ Dir1: GPIO 23, Dir2: GPIO 24, PWM: GPIO 25

M01.2 (Vacuum Right):
  └─ Dir1: GPIO 10, Dir2: GPIO 9, PWM: GPIO 11

M02 (Heating):
  └─ Dir1: GPIO 6, Dir2: GPIO 5, PWM: GPIO 12

M03 (Packaging):
  └─ Dir1: GPIO 19, Dir2: GPIO 26, PWM: GPIO 13
```

### Sensors (I2C ADS1115 ADC @ 0x48)

```
Analog Inputs:
  ├─ A0: Pressure Sensor (0-100 kPa)
  ├─ A1: Temperature Sensor (-20 to +120°C)
  ├─ A2: Reserved
  └─ A3: Reserved

I2C Pins:
  ├─ GPIO 2: SDA
  ├─ GPIO 3: SCL
  └─ Address: 0x48
```

### Digital I/O

```
Inputs:
  ├─ GPIO 20: Proximity Sensor 1 (Digital)
  ├─ GPIO 21: Proximity Sensor 2 (Digital)
  └─ GPIO 8: Emergency Stop Button

Outputs:
  └─ GPIO 16: Solenoid Valve Relay
```

## Usage Examples

### Basic Motor Control
```python
from hardware import get_hardware_controller

hw = get_hardware_controller()

# Run motor forward at 100 RPM
hw.motor_forward("M001", 100)

# Stop motor
hw.motor_stop("M001")

# Run backward
hw.motor_backward("M001", 50)
```

### Sensor Reading
```python
# Get single reading
pressure = hw.get_sensor_reading("pressure")
if pressure:
    print(f"Pressure: {pressure.value} {pressure.unit}")

# Start continuous polling
def on_sensor_data(readings):
    for sensor_id, reading in readings.items():
        print(f"{reading.sensor_name}: {reading.value} {reading.unit}")

hw.start_sensor_polling(callback=on_sensor_data)
```

### Dispenser Stage
```python
from hardware.stage_integration import DispenserControl

dispenser = DispenserControl(hw)

# Jog M001
dispenser.jog_m001(
    distance=10,  # mm
    rpm=150,
    direction="FORWARD",
    progress_callback=lambda p, msg: print(f"{p*100:.0f}%: {msg}")
)

# Auto sequence
measurements = [
    {"distance": 5, "unit": "mm"},
    {"distance": 10, "unit": "mm"},
]
dispenser.dispense_auto_sequence(measurements)
```

### Vacuum Stage
```python
from hardware.stage_integration import VacuumControl

vacuum = VacuumControl(hw)

# Jog coupled motors
vacuum.jog_coupled(15, 200, "FORWARD")

# Vacuum sequence with pressure monitoring
vacuum.vacuum_sequence(pressure_target=80)
```

### Heating Stage
```python
from hardware.stage_integration import HeatingControl

heating = HeatingControl(hw)

# Heat to 60°C for 5 minutes
heating.heating_sequence(target_temp=60, duration=300)
```

### Packaging Stage
```python
from hardware.stage_integration import PackagingControl

packaging = PackagingControl(hw)

# Execute 5 packaging cycles
packaging.packaging_sequence(cycles=5)
```

### Sterilization Stage
```python
from hardware.stage_integration import SterilizationControl

sterilization = SterilizationControl(hw)

# Sterilize for 10 minutes with monitoring
sterilization.sterilization_sequence(duration=600)
```

### Emergency Stop
```python
# Stop all motors and actuators immediately
hw.emergency_stop()
```

## Troubleshooting

| Issue | Solution |
|-------|----------|
| GPIO Permission Denied | `sudo usermod -a -G gpio $USER` |
| I2C Not Found | `i2cdetect -y 1` (check 0x48) |
| Motor Not Running | Check L298N power + GPIO direction pins |
| Sensor Reading = 0 | Check I2C connections, verify address |
| Flet Display Issues | Run with: `DISPLAY=:0 python3 main.py` |

## File Structure

```
cmti_flet/
├── main.py                    # Entry point
├── app.py                     # Main app controller
├── theme.py                   # UI theme constants
├── requirements.txt           # Python dependencies
│
├── hardware/                  # NEW: Hardware layer
│   ├── __init__.py
│   ├── gpio_config.py        # Pin assignments
│   ├── controller.py         # Hardware abstraction
│   ├── stage_integration.py  # Stage-specific control
│   └── INTEGRATION_GUIDE.py  # Integration examples
│
├── stages/
│   ├── dashboard.py
│   ├── dispenser.py          # TODO: Add hardware calls
│   ├── vacuum.py             # TODO: Add hardware calls
│   ├── heating.py            # TODO: Create with hardware
│   ├── packaging.py          # TODO: Create with hardware
│   └── sterilization.py      # TODO: Create with hardware
│
└── ui/
    └── sidebars.py
```

## Configuration Options

Edit `hardware/gpio_config.py` to customize:

- **Motor pin assignments** (MOTOR_CONFIG)
- **Sensor pins** (SENSOR_CONFIG)
- **Actuator pins** (ACTUATOR_CONFIG)
- **PWM frequency** (PWM_BASE_FREQUENCY)
- **Safety limits** (SAFETY_CONFIG)
- **I2C address** (I2C_CONFIG)

## Safety Features Enabled

✓ Emergency Stop button (GPIO 8)
✓ Motor runtime limits (300s default)
✓ Soft PWM ramp-up
✓ Continuous sensor monitoring
✓ Thread-safe operations
✓ Graceful cleanup on shutdown

## Next Steps

1. ✓ GPIO pins assigned
2. ✓ Hardware abstraction layer created
3. ✓ Stage integration templates ready
4. ✓ RPi 5 setup documentation complete
5. → **TODO: Integrate hardware into stage classes**
6. → **TODO: Add encoder/distance feedback**
7. → **TODO: Implement data logging**
8. → **TODO: Add sensor calibration UI**

## Contacts for Support

For hardware issues:
- Check [RPI5_SETUP.md](../RPI5_SETUP.md) for detailed setup
- Review [hardware/INTEGRATION_GUIDE.py](./hardware/INTEGRATION_GUIDE.py) for patterns
- Test components individually using examples above
