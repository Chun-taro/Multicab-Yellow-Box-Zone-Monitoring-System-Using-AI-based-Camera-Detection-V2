
import sys
import os

# Ensure the current directory is in sys.path
sys.path.append(os.getcwd())

try:
    import utils
    print(f"Imported utils from: {utils.__file__}")
    print(f"utils package path: {utils.__path__}")
    
    import utils.camera
    print(f"Imported utils.camera from: {utils.camera.__file__}")

except ImportError as e:
    print(f"ImportError: {e}")
except Exception as e:
    print(f"An error occurred: {e}")
