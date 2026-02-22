# How to Run the Multicab Yellow Box Zone Monitoring System

This guide will walk you through the steps to set up and run the system on your machine.

## Prerequisites
1. **Python**: Ensure you have Python 3.8 or newer installed on your Windows machine. You can download it from [python.org](https://www.python.org/downloads/windows/).
2. **Camera Source**: The system uses a camera feed (like OBS Virtual Camera or a physical webcam) for live monitoring.

## Step 1: Set Up the Virtual Environment

It is highly recommended to use a Python virtual environment to manage the project dependencies.

1. Open **Command Prompt** or **PowerShell**.
2. Navigate to the project folder:
   ```cmd
   cd "C:\Users\micha\OneDrive\Desktop\Multicab Yellow Box Zone Monitoring System Using AI based Camera Detection"
   ```
   *(Adjust the path above if you move the folder).*
3. Create a virtual environment named `.venv` (if it doesn't already exist):
   ```cmd
   python -m venv .venv
   ```
4. Activate the virtual environment:
   ```cmd
   .venv\Scripts\activate
   ```
   *You should see `(.venv)` at the beginning of your terminal prompt indicating it is active.*

## Step 2: Install Dependencies

With your virtual environment activated, install the required packages:

```cmd
pip install -r requirements.txt
```
*Note: This may take several minutes as it installs heavy Computer Vision and AI libraries like PyTorch, OpenCV, and Ultralytics (YOLO).*

## Step 3: Run the System

You can run the system in two different ways depending on how you prefer to view the monitoring dashboard. Ensure your virtual environment is activated before running.

### Option A: Web Browser Mode (Recommended for testing)
This runs the backend server and you view the interface through your web browser.

1. Run the main app script:
   ```cmd
   python app.py
   ```
2. Open your web browser (Chrome, Edge, Firefox) and navigate to:
   **http://127.0.0.1:5000**

### Option B: Desktop App Mode
This packages the web interface into a standalone desktop window using `pywebview`.

1. Run the desktop application script:
   ```cmd
   python run_desktop.py
   ```
2. A separate desktop window will open automatically, displaying the Live Dashboard.

## Troubleshooting

- **Performance Issues / Slow Video**: By default, the system is configured to process every single frame for extreme accuracy (30 FPS). If the video feed looks slow or laggy on your computer, you can optimize this! Open `config/config.py` and change `FRAME_SKIP` from `1` to `2` or `3` to make the AI process fewer frames and speed up the video stream.
- **"Camera error: Unable to open source"**: Check `config/config.py` in the project folder and modify the `CAMERA_SOURCE` variable. It typically defaults to `0` for a laptop webcam, or `1` for an external or virtual camera (like OBS).
- **Missing AI Weights**: The system uses YOLOv8 (`yolov8s.pt`). If the file is missing from the `ai_model` directory, the `ultralytics` package should automatically download it on the first run. Ensure you have an active internet connection.
- **Port 5000 in use**: If you get an error that the address is already in use, make sure you don't have another instance of `app.py` running in the background.
