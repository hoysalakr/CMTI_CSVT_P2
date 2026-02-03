"""
Example: How to integrate hardware control into existing stage classes

This shows the pattern to follow for all stages.
"""

# BEFORE (Current code - stub only):
"""
def _send_command(self, cmd: dict, label: str):
    # Stub: replace with actual motor command
    self.snack(f"{label}: {cmd}")
"""

# AFTER (With hardware integration):
"""
from hardware import get_hardware_controller
from hardware.stage_integration import DispenserControl

class DispenserStage:
    def __init__(self, auto_mode: bool, snack, on_request_error=None, on_status=None):
        # ... existing code ...
        
        # Initialize hardware
        self.hw = get_hardware_controller()
        self.dispenser = DispenserControl(self.hw)
        
    def _send_command(self, cmd: dict, label: str):
        '''Send actual hardware command'''
        try:
            if cmd.get("cmd") == "move_distance":
                motor_id = cmd.get("motor")
                distance = cmd.get("distance")
                rpm = cmd.get("rpm")
                direction = cmd.get("direction", "FORWARD")
                
                # Execute with progress callback
                self.dispenser.jog_m001(
                    distance, 
                    rpm, 
                    direction,
                    progress_callback=self._on_motor_progress
                )
                
            elif cmd.get("cmd") == "auto_sequence":
                measurements = cmd.get("measurements", [])
                self.dispenser.dispense_auto_sequence(
                    measurements,
                    progress_callback=self._on_motor_progress
                )
                
            elif cmd.get("cmd") == "stop":
                self.dispenser.rapid_stop()
                
        except Exception as e:
            self.on_request_error(f"Hardware error: {str(e)}")
    
    def _on_motor_progress(self, progress: float, status_msg: str):
        '''Callback from hardware layer'''
        if self.on_status:
            self.on_status(progress, status_msg)
        self.snack(status_msg)
"""

print("Integration pattern documented in hardware/INTEGRATION_GUIDE.md")
