# CMTI Hardware - Pin Diagram & Connections

## Raspberry Pi 5 GPIO Pin Layout

```
    ┌─────────────────────────────────────────┐
    │  RASPBERRY PI 5 GPIO HEADER             │
    ├─────────────────────────────────────────┤
    │                                         │
    │  3V3  ┌─┬─┐ 5V          [Power pins]   │
    │  GPIO2┼─┼─┼─GPIO3       [I2C SDA/SCL] │
    │  GPIO4├─┼─┤─GND                       │
    │  GPIO17├┼┤─GPIO27       [M001 Dir]    │
    │  GPIO22├┼┤─GND          [M001 PWM]    │
    │  GPIO10├┼┤─GPIO9        [M01.2 Dir]   │
    │  GPIO11├┼┤─GND          [M01.2 PWM]   │
    │  GPIO5 ├┼┤─GPIO6        [M02 Dir]     │
    │  GPIO12├┼┤─GND          [M02 PWM]     │
    │  GPIO13├┼┤─GPIO19       [M03 PWM/Dir]│
    │  GPIO26├┼┤─GND          [M03 Dir]     │
    │  GPIO20├┼┤─GPIO21       [Proximity]  │
    │  GPIO16├┼┤─GND          [Solenoid]   │
    │  GPIO23├┼┤─GPIO24       [M01.1 Dir]  │
    │  GPIO25├┼┤─GND          [M01.1 PWM]  │
    │  GPIO8 ├┼┤─GPIO14       [Em-Stop/ADC]│
    │  GPIO15├┼┤─GND          [Temp/ADC]   │
    │        │ │              │             │
    │  +5V   └─┴─┘ GND                      │
    └─────────────────────────────────────────┘
```

## Motor Driver L298N Wiring (Per Motor)

```
    ┌───────────────────────────────────────┐
    │   MOTOR (12V DC with gearbox)         │
    │                                       │
    │       ┌─────────────────────┐         │
    │       │                     │         │
    │  OUT1 ├─────────┬───────────┤ OUT2    │
    │       │         │           │         │
    └─────────────────────────────────────┘
           │         │           │
           │ ┌─────────────────┐ │
           └─┤ L298N           ├─┘
             │ Motor Driver    │
             └──┬────────┬─────┘
                │        │
      IN1 (Dir1)├────┐  ┌┤ IN2 (Dir2)
      ENA (PWM) ├────┐  ┌┤ ENB (PWM)
        GND ────┼────────┤─ GND

RPi GPIO        L298N           Power Supply
─────────────────────────────────────────
GPIO17  ────→  IN1    M001
GPIO27  ────→  IN2
GPIO22  ────→  ENA (PWM ~1000Hz)

        12V   ←────── +12V Supply
        GND   ←────── GND (shared with RPi)
```

## I2C Sensor Connection (ADS1115 ADC Module)

```
Raspberry Pi               ADS1115 ADC             Sensors
───────────────────────────────────────────────────────

GPIO2 (SDA) ────────────→ SDA
GPIO3 (SCL) ────────────→ SCL
3.3V        ────────────→ VDD
GND         ────────────→ GND

                         A0  ←───────── Pressure Sensor
                                       (0-3.3V analog)
                         A1  ←───────── Temperature Sensor
                                       (0-3.3V analog)
                         A2
                         A3

I2C Address: 0x48 (set by ADDR pin floating)
```

## Complete GPIO Allocation Map

```
PIN  │ GPIO │ Function              │ Stage        │ Hardware
─────┼──────┼───────────────────────┼──────────────┼─────────────
 1   │ 3V3  │ Power +3.3V           │              │ Power
 2   │ 5V   │ Power +5V             │              │ Power
 3   │  2   │ I2C SDA               │ All          │ I2C ADC
 4   │  3   │ I2C SCL               │ All          │ I2C ADC
 5   │  4   │ Unused                │              │
 6   │ GND  │ Ground                │              │
 7   │ 17   │ M001 Dir Forward      │ Dispenser    │ L298N
 8   │ 27   │ M001 Dir Backward     │ Dispenser    │ L298N
 9   │ 22   │ M001 Speed PWM        │ Dispenser    │ L298N
10   │ GND  │ Ground                │              │
11   │ 10   │ M01.2 Dir Forward     │ Vacuum       │ L298N
12   │  9   │ M01.2 Dir Backward    │ Vacuum       │ L298N
13   │ 11   │ M01.2 Speed PWM       │ Vacuum       │ L298N
14   │ GND  │ Ground                │              │
15   │  5   │ M02 Dir Forward       │ Heating      │ L298N
16   │  6   │ M02 Dir Backward      │ Heating      │ L298N
17   │ 12   │ M02 Speed PWM         │ Heating      │ L298N
18   │ GND  │ Ground                │              │
19   │ 19   │ M03 Dir Forward       │ Packaging    │ L298N
20   │ 26   │ M03 Dir Backward      │ Packaging    │ L298N
21   │ 13   │ M03 Speed PWM         │ Packaging    │ L298N
22   │ GND  │ Ground                │              │
23   │ 23   │ M01.1 Dir Forward     │ Vacuum       │ L298N
24   │ 24   │ M01.1 Dir Backward    │ Vacuum       │ L298N
25   │ 25   │ M01.1 Speed PWM       │ Vacuum       │ L298N
26   │ GND  │ Ground                │              │
27   │ 20   │ Proximity Sensor 1    │ All          │ Digital Input
28   │ 21   │ Proximity Sensor 2    │ All          │ Digital Input
29   │ GND  │ Ground                │              │
30   │ 16   │ Solenoid Valve Relay  │ Vacuum       │ Relay Output
31   │  8   │ Emergency Stop Button │ Safety       │ Digital Input
32   │ GND  │ Ground                │              │
33   │ 14   │ Reserved (ADC)        │              │
34   │ GND  │ Ground                │              │
35   │ 15   │ Reserved (ADC)        │              │
36   │ GND  │ Ground                │              │
```

## Power Distribution

```
┌──────────────────────────────────────────────┐
│        POWER SUPPLY RACK                     │
├──────────────────────────────────────────────┤
│                                              │
│  +12V DC Supply (5A min)    +5V USB Supply   │
│  │                          │                │
│  ├─────┬─────┬─────┬────────┤────────┐      │
│  │     │     │     │        │        │      │
│  ▼     ▼     ▼     ▼        ▼        ▼      │
│ L298N L298N L298N L298N   Relay    RPi 5   │
│ M001  M01.1 M01.2 M02/M03 Solenoid (27W)   │
│ (12W) (12W) (12W) (15W)   (10W)            │
│  │     │     │     │        │        │      │
│  └─────┴─────┴─────┴────────┴────────┘      │
│           (shared GND)                      │
│                                              │
│ Total Power: ~89W @ 12V + 5V                │
│ Recommended: Dual supply PSU                │
└──────────────────────────────────────────────┘
```

## Cable Specifications

```
Component              │ Cable Type        │ Length  │ Gauge
────────────────────────┼──────────────────┼─────────┼──────
Motor Power (12V)       │ Shielded Twisted  │ 1m      │ 18 AWG
Motor Control (GPIO)    │ Cat6 w/ shielding │ 2m      │ 24 AWG
I2C Bus (SDA/SCL)       │ Twisted Pair      │ 1m      │ 24 AWG
Sensor Analog          │ Shielded          │ 2m      │ 24 AWG
Sensor Digital         │ Twisted Pair      │ 1.5m    │ 22 AWG
Emergency Stop (GND)    │ Multi-strand      │ 0.5m    │ 16 AWG
```

## Connector Guide

```
Motor Connectors (to L298N Motor Driver):
  ├─ Motor Power: XT60 or Anderson PowerPole (12V, high current)
  ├─ Control Lines: 2.54mm dupont headers (GPIO signals)
  └─ GND: 3.5mm banana connectors (safety)

I2C Connectors:
  ├─ SDA/SCL: 2.54mm dupont headers
  ├─ Pull-ups: 4.7kΩ resistors on SDA/SCL
  └─ Sensor: I2C JST SM 4-pin connectors

Digital Inputs (Emergency Stop, Sensors):
  └─ 2.54mm dupont headers with pull-up resistors

Relay (Solenoid Valve):
  └─ 5V relay module with GPIO control pin
```

## Terminal Block Layout (Control Panel)

```
┌───────────────────────────────────────────────────┐
│  CMTI CONTROL PANEL - Terminal Block Layout       │
├───────────────────────────────────────────────────┤
│                                                   │
│  ┌─ MOTOR CONNECTIONS ─────────────────┐         │
│  │  M001  (Dispenser)    ─→ OUT 1,2    │         │
│  │  M01.1 (Vacuum Left)  ─→ OUT 3,4    │         │
│  │  M01.2 (Vacuum Right) ─→ OUT 5,6    │         │
│  │  M02   (Heating)      ─→ OUT 7,8    │         │
│  │  M03   (Packaging)    ─→ OUT 9,10   │         │
│  └─────────────────────────────────────┘         │
│                                                   │
│  ┌─ SENSOR CONNECTIONS ────────────────┐         │
│  │  Pressure Sensor      ─→ IN 1       │         │
│  │  Temperature Sensor   ─→ IN 2       │         │
│  │  Proximity Sensor 1   ─→ IN 3       │         │
│  │  Proximity Sensor 2   ─→ IN 4       │         │
│  └─────────────────────────────────────┘         │
│                                                   │
│  ┌─ CONTROL CONNECTIONS ──────────────┐         │
│  │  Emergency Stop Button ─→ IN 5      │         │
│  │  Solenoid Valve Relay  ─→ OUT 11    │         │
│  │  Power Supply (12V)    ─→ +12V      │         │
│  │  Power Return (GND)    ─→ GND       │         │
│  └─────────────────────────────────────┘         │
│                                                   │
└───────────────────────────────────────────────────┘
```

## Troubleshooting Connection Issues

| Problem | Check | Solution |
|---------|-------|----------|
| Motor won't spin | L298N power, GPIO dir pins | Verify 12V and GPIO connections |
| I2C sensor not found | GPIO2/3, address jumpers | `i2cdetect -y 1` test |
| Emergency stop not working | GPIO8 pull-up, button | Test with `GPIO.input(8)` |
| PWM noise | Shielding, frequency | Use shielded twisted pair cables |
| Sensor reading = 0 | I2C termination, VDD | Check 4.7kΩ pull-ups on SDA/SCL |
| GPIO permission denied | User group membership | `sudo usermod -a -G gpio $USER` |

---

**Remember**: All GNDs must be tied together (RPi, L298N drivers, power supply)
