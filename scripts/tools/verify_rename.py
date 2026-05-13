
import sys
import os

# Ensure the current directory is in sys.path
sys.path.append(os.getcwd())

try:
    print(f"Current working directory: {os.getcwd()}")
    
    import utils
    print(f"Successfully imported utils from: {utils.__file__}")
    
    from utils.camera import CameraHandler
    print("Successfully imported CameraHandler from utils.camera")
    
    # Check if old utils still exists/imports (shouldn't or should be different)
    try:
        import utils.camera
        print("WARNING: utils.camera still importable (might be system package or leftover)")
    except ImportError:
        print("Confirmed: utils.camera is no longer importable (expected)")

except ImportError as e:
    print(f"ImportError: {e}")
except Exception as e:
    print(f"An error occurred: {e}")
