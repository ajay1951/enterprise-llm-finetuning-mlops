from forgellm.hardware.detector import HardwareDetector

def test_hardware_detection():
    hw = HardwareDetector.detect()
    assert hw.os_name is not None
    assert hw.ram_gb > 0
    # Depending on runner, pytorch might be installed or not, but we just verify it doesn't crash
