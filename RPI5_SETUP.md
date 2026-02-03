# Raspberry Pi 5 Hardware Setup Guide

## System Requirements

- **Raspberry Pi 5** (8GB recommended)
- **OS**: Raspberry Pi OS (64-bit) - Latest
- **Python**: 3.9+
- **GPIO**: BCM numbering (default)

## Installation Steps

### 1. Update System
```bash
sudo apt-get update
sudo apt-get upgrade -y
```

### 2. Enable I2C Interface
```bash
sudo raspi-config
# Navigate to: Interface Options → I2C → Enable
# Reboot
sudo reboot
```

### 3. Install Python GPIO Libraries

**RPi.GPIO (for motor PWM/direction control):**
```bash
sudo apt-get install python3-rpi.gpio
# OR
pip3 install RPi.GPIO
```

**Adafruit I2C Libraries (for sensors):**
```bash
pip3 install adafruit-circuitpython-ads1x15
pip3 install adafruit-circuitpython-busio
```

**Flet Framework:**
```bash
pip3 install flet
```

**Other dependencies:**
```bash
pip3 install numpy scipy requests
```

### 4. Complete Installation Script
```bash
#!/bin/bash
sudo apt-get update
sudo apt-get upgrade -y
sudo apt-get install -y python3-pip python3-rpi.gpio i2c-tools

pip3 install --upgrade pip
pip3 install flet
pip3 install RPi.GPIO
pip3 install adafruit-circuitpython-ads1x15
pip3 install adafruit-circuitpython-busio
pip3 install board

# Test GPIO access
python3 -c "import RPi.GPIO; print('RPi.GPIO OK')"
echo "Installation complete!"
```

## Hardware Wiring Diagram

### Motor Connections (L298N Motor Driver)
```
Motor Pins ← L298N ← Raspberry Pi GPIO

M001 (Dispenser):
  - Direction 1: GPIO 17 → L298N IN1
  - Direction 2: GPIO 27 → L298N IN2
  - PWM Speed:   GPIO 22 → L298N ENA

M01.1 (Vacuum Left):
  - Direction 1: GPIO 23 → L298N IN1
  - Direction 2: GPIO 24 → L298N IN2
  - PWM Speed:   GPIO 25 → L298N ENB

M01.2 (Vacuum Right):
  - Direction 1: GPIO 10 → L298N IN1
  - Direction 2: GPIO 9  → L298N IN2
  - PWM Speed:   GPIO 11 → L298N ENB

(Same pattern for M02, M03...)

Power:
  - L298N +12V ← Power Supply
  - L298N GND  ← Power Supply GND (shared with RPi)
  - RPi GND    ← Power Supply GND
```

### I2C Sensor Connections
```
Raspberry Pi Pins:
  - GPIO 2 (SDA) → ADS1115 SDA
  - GPIO 3 (SCL) → ADS1115 SCL
  - GND          → ADS1115 GND
  - 3.3V         → ADS1115 VDD

ADS1115 Analog Inputs:
  - A0: Pressure Sensor (0-100 kPa)
  - A1: Temperature Sensor (-20 to +120°C)
  - A2: (Reserved)
  - A3: (Reserved)
```

### Digital Sensor Connections
```
Proximity Sensors:
  - GPIO 20 → Sensor 1 (Digital Output)
  - GPIO 21 → Sensor 2 (Digital Output)

Solenoid Valve (Relay Module):
  - GPIO 16 → Relay IN (drives solenoid)
  - GPIO 8  → Emergency Stop Button (pull-up input)
```

## Pin Allocation Summary

| GPIO | Function | Component | Notes |
|------|----------|-----------|-------|
| 2 | I2C SDA | ADS1115 ADC | Shared I2C |
| 3 | I2C SCL | ADS1115 ADC | Shared I2C |
| 5 | Dir M02 | Motor 02 | Heating |
| 6 | Dir M02 | Motor 02 | Heating |
| 8 | Digital Input | Emergency Stop | Pull-up |
| 9 | Dir M01.2 | Motor 01.2 | Vacuum Right |
| 10 | Dir M01.2 | Motor 01.2 | Vacuum Right |
| 11 | PWM M01.2 | Motor 01.2 | ~1000 Hz |
| 12 | PWM M02 | Motor 02 | ~1000 Hz |
| 13 | PWM M03 | Motor 03 | ~1000 Hz |
| 14 | I2C ADC | Pressure | Via I2C |
| 15 | I2C ADC | Temperature | Via I2C |
| 16 | Digital Out | Solenoid | Relay driver |
| 17 | Dir M001 | Motor 001 | Dispenser |
| 19 | Dir M03 | Motor 03 | Packaging |
| 20 | Digital In | Proximity 1 | Sensor input |
| 21 | Digital In | Proximity 2 | Sensor input |
| 22 | PWM M001 | Motor 001 | ~1000 Hz |
| 23 | Dir M01.1 | Motor 01.1 | Vacuum Left |
| 24 | Dir M01.1 | Motor 01.1 | Vacuum Left |
| 25 | PWM M01.1 | Motor 01.1 | ~1000 Hz |
| 26 | Dir M03 | Motor 03 | Packaging |
| 27 | Dir M001 | Motor 001 | Dispenser |

## Running the Application

### 1. Start the GUI
```bash
cd ~/cmti_flet
python3 main.py
```

### 2. Enable Full GPIO Access
If you get permission errors:
```bash
sudo usermod -a -G gpio $USER
# Logout and login for changes to take effect
```

### 3. Autostart on Boot
Create `/home/pi/cmti_start.sh`:
```bash
#!/bin/bash
cd /home/pi/CMTI_CSVT_P2/cmti_flet
python3 main.py
```

Make executable and add to crontab:
```bash
chmod +x ~/cmti_start.sh
crontab -e
# Add: @reboot /home/pi/cmti_start.sh
```

## Testing Hardware

### Test GPIO
```bash
python3 << 'EOF'
import RPi.GPIO as GPIO
import time

GPIO.setmode(GPIO.BCM)
GPIO.setup(17, GPIO.OUT)

# Blink LED on GPIO 17
for i in range(10):
    GPIO.output(17, GPIO.HIGH)
    time.sleep(0.5)
    GPIO.output(17, GPIO.LOW)
    time.sleep(0.5)

GPIO.cleanup()
print("GPIO test complete!")
EOF
```

### Test I2C
```bash
i2cdetect -y 1
# Should show address 0x48 if ADS1115 is connected
```

### Test Motor
```bash
python3 << 'EOF'
from hardware import get_hardware_controller

hw = get_hardware_controller()
hw.motor_forward("M001", 100)
time.sleep(2)
hw.motor_stop("M001")
print("Motor test complete!")
EOF
```

## Troubleshooting

### I2C Not Found
```bash
# Check devices
sudo i2cdetect -y 1

# Check if i2c-dev is enabled
ls -la /dev/i2c-*

# Verify I2C address jumpers on ADS1115
```

### GPIO Permission Denied
```bash
# Run with sudo (not recommended)
sudo python3 main.py

# OR add user to GPIO group
sudo usermod -a -G gpio $USER
```

### Motors Not Running
- Check L298N power connections
- Verify GPIO pins in `gpio_config.py`
- Test GPIO direction pins individually
- Check PWM frequency/duty cycle

### Sensors Not Reading
- Verify I2C address (`i2cdetect -y 1`)
- Check SDA/SCL connections
- Verify pull-up resistors on I2C bus
- Check ADS1115 configuration

## Safety Features

- **Emergency Stop (GPIO 8)**: Pull LOW to stop all motors
- **Motor Runtime Limits**: 300s max per motor (configurable)
- **Sensor Monitoring**: Continuous pressure/temperature tracking
- **Soft Start**: PWM ramp-up to prevent mechanical shock

## Configuration Files

- `hardware/gpio_config.py` - All pin assignments
- `hardware/controller.py` - Hardware abstraction layer
- `hardware/stage_integration.py` - Stage-specific hardware control

## Performance Notes

- **PWM Frequency**: 1000 Hz (good for stepper motor control)
- **I2C Speed**: 100 kHz (standard for sensor reading)
- **Sensor Update Rate**: 100ms (adjustable)
- **Motor Response**: <10ms

## Power Requirements

- **Raspberry Pi 5**: 27W (5V/5.1A)
- **Motors (5x)**: ~50W total (12V supply)
- **Sensors**: <2W
- **Solenoid Valve**: ~10W (when active)

**Total**: ~90W @ 12V + 5V dual supply recommended
