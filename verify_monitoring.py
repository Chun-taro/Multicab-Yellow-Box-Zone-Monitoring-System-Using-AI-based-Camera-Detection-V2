import time
import sys
import os

# Add current directory to path
sys.path.append(os.getcwd())

# Force CAMERA_SOURCE to 0 for local webcam testing if needed, 
# or just use the default configured RTSP (it will use placeholder if it fails)
from app_utils.monitoring_service import monitoring_service
from config.config import config

def test_monitoring_service():
    print("Testing Monitoring Service...")
    
    # Use a small IDLE_TIMEOUT for testing if possible or just wait
    print(f"Is running initially: {monitoring_service.is_running}")
    
    # Request a frame - should start the service
    print("Requesting frame...")
    frame = monitoring_service.get_frame()
    
    # Give it a moment to start the thread
    time.sleep(2)
    print(f"Is running after request: {monitoring_service.is_running}")
    
    if monitoring_service.is_running:
        print("✓ Monitoring Service started successfully on demand")
    else:
        print("✗ Monitoring Service failed to start")
        return

    # Check for idle timeout (we configured 10s)
    print("Waiting for idle timeout (12 seconds)...")
    time.sleep(12)
    
    # Trigger one more check (the thread loop checks at start of loop)
    # The monitoring thread will exit on its own if idle.
    time.sleep(1) 
    
    if not monitoring_service.is_running:
        print("✓ Monitoring Service automatically paused after being idle (Power Saving active)")
    else:
        # Check if the thread is actually stopped
        print(f"Still running after timeout? {monitoring_service.is_running}")
        print("Note: The thread might still be releasing resources or the timeout loop is pending.")

if __name__ == "__main__":
    test_monitoring_service()
