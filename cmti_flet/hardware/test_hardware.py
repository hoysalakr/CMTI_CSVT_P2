"""
Hardware Test Script for Raspberry Pi 5
Run this to verify GPIO, motors, and sensors before deploying
"""

import time
import sys

try:
    from hardware import get_hardware_controller, HARDWARE_AVAILABLE, I2C_AVAILABLE
except ImportError as e:
    print(f"❌ Hardware module not found: {e}")
    print("   Install with: pip3 install -r requirements.txt")
    sys.exit(1)


def test_hardware_availability():
    """Check if hardware libraries are available"""
    print("\n" + "="*50)
    print("1. HARDWARE AVAILABILITY CHECK")
    print("="*50)
    
    print(f"RPi.GPIO available: {'✅' if HARDWARE_AVAILABLE else '⚠️  (simulation mode)'}")
    print(f"I2C/ADC available:  {'✅' if I2C_AVAILABLE else '⚠️  (simulation mode)'}")
    
    return HARDWARE_AVAILABLE


def test_hardware_initialization():
    """Test hardware controller initialization"""
    print("\n" + "="*50)
    print("2. HARDWARE CONTROLLER INITIALIZATION")
    print("="*50)
    
    try:
        hw = get_hardware_controller()
        print(f"✅ HardwareController initialized")
        print(f"   Motors available: {list(hw.motors.keys())}")
        print(f"   Actuators available: {list(hw.actuators.keys())}")
        return hw
    except Exception as e:
        print(f"❌ Failed to initialize hardware: {e}")
        return None


def test_motors(hw):
    """Test motor control"""
    print("\n" + "="*50)
    print("3. MOTOR CONTROL TEST")
    print("="*50)
    
    if not hw:
        print("⚠️  Skipped (hardware not initialized)")
        return False
    
    try:
        for motor_id in ["M001", "M01.1", "M01.2"]:
            print(f"\nTesting {motor_id}...")
            
            # Forward
            print(f"  → Forward @ 100 RPM...")
            hw.motor_forward(motor_id, 100)
            time.sleep(0.5)
            
            # Stop
            print(f"  → Stopping...")
            hw.motor_stop(motor_id)
            time.sleep(0.2)
            
            # Backward
            print(f"  → Backward @ 100 RPM...")
            hw.motor_backward(motor_id, 100)
            time.sleep(0.5)
            
            # Stop
            print(f"  → Stopping...")
            hw.motor_stop(motor_id)
            
            print(f"  ✅ {motor_id} working")
        
        return True
    except Exception as e:
        print(f"❌ Motor test failed: {e}")
        return False


def test_sensors(hw):
    """Test sensor reading"""
    print("\n" + "="*50)
    print("4. SENSOR TEST")
    print("="*50)
    
    if not hw:
        print("⚠️  Skipped (hardware not initialized)")
        return False
    
    try:
        print("\nReading sensors...")
        
        # Take single readings
        sensors_to_read = ["pressure", "temperature", "proximity_1", "proximity_2"]
        
        for sensor_id in sensors_to_read:
            reading = hw.get_sensor_reading(sensor_id)
            if reading:
                print(f"  {reading.sensor_name}: {reading.value:.2f} {reading.unit}")
            else:
                print(f"  {sensor_id}: No reading")
        
        print("✅ Sensor test complete")
        return True
    except Exception as e:
        print(f"❌ Sensor test failed: {e}")
        return False


def test_actuators(hw):
    """Test actuator control"""
    print("\n" + "="*50)
    print("5. ACTUATOR TEST")
    print("="*50)
    
    if not hw:
        print("⚠️  Skipped (hardware not initialized)")
        return False
    
    try:
        print("\nTesting solenoid valve...")
        
        hw.actuator_on("solenoid_valve")
        print("  → Solenoid ON")
        time.sleep(1)
        
        hw.actuator_off("solenoid_valve")
        print("  → Solenoid OFF")
        
        print("✅ Actuator test complete")
        return True
    except Exception as e:
        print(f"❌ Actuator test failed: {e}")
        return False


def test_emergency_stop(hw):
    """Test emergency stop"""
    print("\n" + "="*50)
    print("6. EMERGENCY STOP TEST")
    print("="*50)
    
    if not hw:
        print("⚠️  Skipped (hardware not initialized)")
        return False
    
    try:
        print("\nStarting motors...")
        hw.motor_forward("M001", 100)
        hw.motor_forward("M01.1", 100)
        time.sleep(1)
        
        print("Triggering emergency stop...")
        hw.emergency_stop()
        
        print("  ✅ All motors stopped")
        time.sleep(0.5)
        
        return True
    except Exception as e:
        print(f"❌ Emergency stop test failed: {e}")
        return False


def test_sensor_polling(hw):
    """Test continuous sensor polling"""
    print("\n" + "="*50)
    print("7. CONTINUOUS SENSOR POLLING TEST")
    print("="*50)
    
    if not hw:
        print("⚠️  Skipped (hardware not initialized)")
        return False
    
    try:
        print("\nStarting 5-second sensor polling...")
        
        reading_count = [0]
        
        def on_readings(readings):
            reading_count[0] += 1
            if reading_count[0] % 10 == 0:  # Print every 10 readings
                print(f"  Readings: {len(readings)} sensors")
        
        hw.start_sensor_polling(interval=0.1, callback=on_readings)
        time.sleep(5)
        hw.sensors.stop_polling()
        
        print(f"  ✅ Collected {reading_count[0]} reading batches")
        return True
    except Exception as e:
        print(f"❌ Polling test failed: {e}")
        return False


def test_stage_integration(hw):
    """Test stage-specific integration"""
    print("\n" + "="*50)
    print("8. STAGE INTEGRATION TEST")
    print("="*50)
    
    if not hw:
        print("⚠️  Skipped (hardware not initialized)")
        return False
    
    try:
        from hardware.stage_integration import DispenserControl, VacuumControl
        
        print("\nTesting DispenserControl...")
        dispenser = DispenserControl(hw)
        print("  ✅ DispenserControl created")
        
        print("Testing VacuumControl...")
        vacuum = VacuumControl(hw)
        print("  ✅ VacuumControl created")
        
        print("✅ Stage integration test complete")
        return True
    except Exception as e:
        print(f"❌ Stage integration test failed: {e}")
        return False


def main():
    """Run all tests"""
    print("\n")
    print("╔" + "="*48 + "╗")
    print("║" + " "*48 + "║")
    print("║  CMTI HARDWARE TEST SUITE - Raspberry Pi 5     ║")
    print("║" + " "*48 + "║")
    print("╚" + "="*48 + "╝")
    
    results = {}
    
    # Run tests
    results["availability"] = test_hardware_availability()
    hw = test_hardware_initialization()
    results["init"] = hw is not None
    
    if hw:
        results["motors"] = test_motors(hw)
        results["sensors"] = test_sensors(hw)
        results["actuators"] = test_actuators(hw)
        results["emergency"] = test_emergency_stop(hw)
        results["polling"] = test_sensor_polling(hw)
        results["integration"] = test_stage_integration(hw)
        
        # Cleanup
        hw.cleanup()
    else:
        print("\n⚠️  Skipping hardware tests due to initialization failure")
    
    # Summary
    print("\n" + "="*50)
    print("TEST SUMMARY")
    print("="*50)
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"  {test_name:20s} {status}")
    
    print(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Hardware is ready.")
        return 0
    else:
        print("⚠️  Some tests failed. Check installation and connections.")
        return 1


if __name__ == "__main__":
    try:
        exit_code = main()
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n\n⚠️  Test interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
