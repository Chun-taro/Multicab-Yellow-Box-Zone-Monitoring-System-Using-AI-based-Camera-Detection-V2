
import sys
import os

# Ensure the current directory is in sys.path
sys.path.append(os.getcwd())

try:
    print(f"Current working directory: {os.getcwd()}")
    print(f"sys.path: {sys.path}")
    
    import utils.camera
    print("Successfully imported utils.camera")
    
    from utils.camera import CameraHandler
    print("Successfully imported CameraHandler from utils.camera")
    
except ImportError as e:
    print(f"ImportError: {e}")
except Exception as e:
    print(f"An error occurred: {e}")
