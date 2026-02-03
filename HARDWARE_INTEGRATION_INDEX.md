# CMTI Hardware Integration - Complete Documentation Index

## Quick Navigation

### 🚀 **Getting Started (5 minutes)**
1. Read: [IMPLEMENTATION_SUMMARY.md](./IMPLEMENTATION_SUMMARY.md) - Overview of what's been done
2. Understand: GPIO pins are assigned, hardware layer is ready
3. Next: Follow the "Integration Steps" in that document

### 📋 **For Setup on Raspberry Pi 5**
1. [RPI5_SETUP.md](./RPI5_SETUP.md) - Complete installation guide
   - System requirements
   - Installation steps
   - Hardware wiring diagrams
   - Testing procedures
   - Troubleshooting

### 📖 **For Reference & Examples**
1. [HARDWARE_REFERENCE.md](./HARDWARE_REFERENCE.md) - Quick reference
   - GPIO pin summary
   - Code examples
   - Usage patterns
   - Troubleshooting table

### 🔌 **For Wiring & Diagrams**
1. [PIN_DIAGRAM.md](./PIN_DIAGRAM.md) - Visual diagrams
   - RPi 5 GPIO layout
   - Motor driver connections
   - I2C sensor wiring
   - Power distribution
   - Cable specifications

### 🛠️ **For Development**
1. `hardware/gpio_config.py` - Pin assignments (27 GPIO pins)
2. `hardware/controller.py` - Hardware abstraction layer
3. `hardware/stage_integration.py` - Stage-specific controllers
4. `hardware/test_hardware.py` - Test script
5. `hardware/INTEGRATION_GUIDE.py` - Code patterns

### 📦 **For Project Setup**
1. `requirements.txt` - All Python dependencies

---

## File Structure

```
CMTI_CSVT_P2/
│
├── 📄 IMPLEMENTATION_SUMMARY.md      ← START HERE
├── 📄 RPI5_SETUP.md                 ← Setup guide
├── 📄 HARDWARE_REFERENCE.md          ← Quick ref
├── 📄 PIN_DIAGRAM.md                 ← Wiring
├── 📄 HARDWARE_INTEGRATION_STATUS.md ← Status
├── 📄 HARDWARE_INTEGRATION_INDEX.md  ← This file
├── 📄 requirements.txt               ← Dependencies
│
└── cmti_flet/
    ├── main.py
    ├── app.py
    ├── theme.py
    │
    ├── hardware/                     ← NEW
    │   ├── __init__.py
    │   ├── gpio_config.py            # Pin assignments
    │   ├── controller.py             # Hardware abstraction
    │   ├── stage_integration.py      # Stage control
    │   ├── test_hardware.py          # Test script
    │   └── INTEGRATION_GUIDE.py      # Code examples
    │
    ├── stages/
    │   ├── dashboard.py
    │   ├── dispenser.py              # TODO: integrate
    │   ├── vacuum.py                 # TODO: integrate
    │   ├── placeholder.py
    │   └── ... (other stages)
    │
    └── ui/
        └── sidebars.py
```

---

## What's Been Implemented

### ✅ Hardware Abstraction Layer

**Motor Control (`Motor` class)**
- Forward/backward direction
- PWM speed control (0-100%)
- Runtime tracking
- Safe start/stop

**Sensor Reading (`SensorReader` class)**
- I2C ADC (Pressure, Temperature)
- Digital inputs (Proximity sensors)
- Continuous polling in background thread
- Reading cache

**Actuator Control (`Actuator` class)**
- Digital outputs (Solenoid valve)
- Digital inputs (Emergency stop)
- State tracking

**Central Controller (`HardwareController` class)**
- Manages all motors, sensors, actuators
- Singleton pattern for easy access
- Graceful cleanup on shutdown
- Emergency stop functionality

### ✅ Stage-Specific Integrations

**DispenserControl**
- M001 motor jog control
- Auto sequence execution
- Progress callbacks

**VacuumControl**
- Coupled M01.1 + M01.2
- Pressure monitoring
- Vacuum sequence with feedback

**HeatingControl**
- M02 motor
- Temperature monitoring
- Heating sequences

**PackagingControl**
- M03 motor
- Cycle-based control

**SterilizationControl**
- Multi-sensor monitoring
- Long-duration sequences

### ✅ GPIO Assignment (27 pins)

```
Motors:        15 pins (5 motors × 3 pins each)
Sensors:        6 pins (I2C SDA/SCL + 4 digital)
Actuators:      2 pins (solenoid + emergency)
Reserved:       4 pins (unused for future)
```

---

## Step-by-Step Integration Guide

### Phase 1: Local Development
```bash
cd cmti_flet
python3 -c "from hardware import get_hardware_controller; print('✅ Hardware ready')"
```

### Phase 2: Update Dispenser Stage
1. Open `stages/dispenser.py`
2. Add: `from hardware import get_hardware_controller`
3. Add: `from hardware.stage_integration import DispenserControl`
4. In `__init__`: 
   ```python
   self.hw = get_hardware_controller()
   self.dispenser = DispenserControl(self.hw)
   ```
5. Replace `_send_command()` stub with actual hardware calls

### Phase 3: Update Vacuum Stage
Same pattern as Dispenser, but use `VacuumControl`

### Phase 4: Deploy to RPi 5
```bash
# On Raspberry Pi 5:
pip3 install -r requirements.txt
python3 main.py
```

### Phase 5: Test & Calibrate
```bash
python3 hardware/test_hardware.py
```

---

## GPIO Pin Reference (Quick)

| GPIO | Purpose | Motor/Stage |
|------|---------|-------------|
| 2, 3 | I2C Bus | All sensors |
| 5, 6, 12 | M02 (Heating) | Heating stage |
| 8 | Emergency Stop | Safety |
| 9, 10, 11 | M01.2 (Vacuum R) | Vacuum stage |
| 13 | M03 PWM | Packaging |
| 14, 15 | Reserved | - |
| 16 | Solenoid | Vacuum |
| 17, 22, 27 | M001 (Dispenser) | Dispenser |
| 19, 20, 21, 26 | M03, Proximity | Packaging, Sensors |
| 23, 24, 25 | M01.1 (Vacuum L) | Vacuum |

**See PIN_DIAGRAM.md for complete details**

---

## Testing Sequence

1. **Test GPIO** (5 min)
   ```bash
   python3 hardware/test_hardware.py
   ```

2. **Test Individual Motors** (10 min)
   ```python
   from hardware import get_hardware_controller
   hw = get_hardware_controller()
   hw.motor_forward("M001", 100)
   ```

3. **Test Sensors** (10 min)
   ```python
   reading = hw.get_sensor_reading("pressure")
   print(reading.value)
   ```

4. **Test Stage Integration** (5 min)
   ```python
   from hardware.stage_integration import DispenserControl
   dispenser = DispenserControl(hw)
   ```

5. **Test Full App** (ongoing)
   ```bash
   python3 main.py
   ```

---

## Common Tasks

### Task: Run Motors
```python
hw.motor_forward("M001", 150)  # RPM
time.sleep(2)
hw.motor_stop("M001")
```

### Task: Read Pressure
```python
p = hw.get_sensor_reading("pressure")
print(f"{p.value} {p.unit}")
```

### Task: Execute Dispense Sequence
```python
dispenser = DispenserControl(hw)
dispenser.dispense_auto_sequence(
    [{"distance": 5, "unit": "mm"}],
    progress_callback=callback_fn
)
```

### Task: Emergency Stop
```python
hw.emergency_stop()  # Stops all motors
```

---

## Dependencies

**Install with:**
```bash
pip3 install -r requirements.txt
```

**Main packages:**
- `RPi.GPIO` - GPIO control
- `adafruit-circuitpython-ads1x15` - I2C ADC
- `flet` - UI framework
- Others: numpy, scipy, requests, etc.

---

## Troubleshooting Quick Links

| Problem | Solution |
|---------|----------|
| GPIO permission denied | [RPI5_SETUP.md](./RPI5_SETUP.md#testing-hardware) |
| I2C sensor not found | [PIN_DIAGRAM.md](./PIN_DIAGRAM.md#troubleshooting-connection-issues) |
| Motor won't run | [HARDWARE_REFERENCE.md](./HARDWARE_REFERENCE.md#troubleshooting) |
| Import errors | [requirements.txt](./requirements.txt) → `pip3 install` |

---

## Support Resources

- **GPIO Layout**: See [PIN_DIAGRAM.md](./PIN_DIAGRAM.md)
- **Wiring Guide**: See [RPI5_SETUP.md](./RPI5_SETUP.md)
- **Code Examples**: See [HARDWARE_REFERENCE.md](./HARDWARE_REFERENCE.md)
- **Implementation Details**: See [hardware/INTEGRATION_GUIDE.py](./cmti_flet/hardware/INTEGRATION_GUIDE.py)

---

## Status & Next Steps

### ✅ Complete
- GPIO pin assignment (27 pins)
- Hardware abstraction layer
- I2C sensor integration
- Motor PWM control
- Emergency stop
- Safety features
- Full documentation

### ⏳ To Do
1. **Integrate hardware calls into UI classes** (dispenser.py, vacuum.py)
2. **Test on actual Raspberry Pi 5**
3. **Add encoder feedback** for precise distance control
4. **Implement data logging** module

### 📅 Timeline
- **Week 1**: Integration & testing (20-30 hours)
- **Week 2**: Encoder & logging (10-15 hours)
- **Week 3**: Fine-tuning & deployment (10-15 hours)

---

## Questions?

1. **How do I run the test?**
   - `python3 cmti_flet/hardware/test_hardware.py`

2. **How do I integrate motors?**
   - See [IMPLEMENTATION_SUMMARY.md](./IMPLEMENTATION_SUMMARY.md) → Integration Steps

3. **Which GPIO pins do I use?**
   - See [PIN_DIAGRAM.md](./PIN_DIAGRAM.md) → GPIO Allocation Map

4. **How do I set up on RPi 5?**
   - Follow [RPI5_SETUP.md](./RPI5_SETUP.md) step-by-step

5. **How do I connect sensors?**
   - See [PIN_DIAGRAM.md](./PIN_DIAGRAM.md) → I2C Sensor Connection

---

**Last Updated**: February 3, 2026
**Status**: ✅ Hardware layer complete, ready for stage integration
**Next Phase**: UI integration with hardware calls
