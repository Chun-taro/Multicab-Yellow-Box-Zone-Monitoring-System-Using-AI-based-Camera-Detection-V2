import time
import sys
import os
import logging

# Add current directory to path
sys.path.append(os.getcwd())

def test_startup_performance():
    print("Testing System Startup Performance...")
    start_time = time.time()
    
    # Import monitoring service - this previously triggered blocking model load
    from utils.monitoring_service import monitoring_service
    
    end_time = time.time()
    startup_duration = end_time - start_time
    
    print(f"Startup/Import Duration: {startup_duration:.4f} seconds")
    
    if startup_duration < 1.0:
        print("✓ SUCCESS: System initialized instantly (Non-blocking)")
    else:
        print(f"✗ WARNING: Startup took {startup_duration:.2f}s. Expected < 1s.")

    # Check AI loading status
    print(f"AI Loading Status: {'Loading...' if monitoring_service.ai_loading else 'Ready/Error'}")
    print(f"Detector Available: {monitoring_service.detector is not None}")
    
    # Wait a bit for AI to load in background
    print("Waiting 5 seconds for background AI model load...")
    time.sleep(5)
    print(f"AI Loading Status after wait: {'Loading...' if monitoring_service.ai_loading else 'Ready/Error'}")
    print(f"Detector Available after wait: {monitoring_service.detector is not None}")
    
    # Check Camera connection status
    print("Testing Camera non-blocking connection...")
    monitoring_service.start()
    print(f"Monitoring Running: {monitoring_service.is_running}")
    
    # Check if camera is opening
    if hasattr(monitoring_service.camera, '_is_opening'):
        print(f"Camera Opening in background: {monitoring_service.camera._is_opening}")
    
    # Wait a bit for camera to fail/connect
    print("Waiting 3 seconds for camera connection attempt...")
    time.sleep(3)
    if hasattr(monitoring_service.camera, '_is_opening'):
        print(f"Camera Opening status after wait: {monitoring_service.camera._is_opening}")
    
    monitoring_service.stop()
    print("Test complete.")

if __name__ == "__main__":
    test_startup_performance()
