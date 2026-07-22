import os
import platform
import subprocess
import json
import psutil
import logging

try:
    import torch
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False

logger = logging.getLogger(__name__)

def run_powershell_json(command):
    """Executes a PowerShell command and returns the parsed JSON result."""
    try:
        # Prevent CMD flash window on Windows
        startupinfo = None
        if os.name == 'nt':
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW

        result = subprocess.run(
            ["powershell", "-NoProfile", "-Command", f"{command} | ConvertTo-Json -Compress"],
            capture_output=True,
            text=True,
            check=True,
            startupinfo=startupinfo,
            encoding='utf-8',
            errors='ignore'
        )
        output = result.stdout.strip()
        if not output:
            return None
        return json.loads(output)
    except Exception as e:
        logger.warning(f"PowerShell query failed: {e}")
        return None

def scan_hardware():
    """
    Scans the system hardware specifications, compares them against 
    minimum/recommended requirements, and returns a detailed report.
    """
    report = {
        "cpu": {},
        "gpu": {
            "devices": []
        },
        "ram": {},
        "storage": {},
        "os": {},
        "apis": {},
        "compatibility": {
            "score": 0,
            "result": "Does Not Meet Requirements",
            "suggestions": []
        }
    }

    # 1. Operating System Detection
    report["os"]["name"] = platform.system()
    report["os"]["version"] = platform.release()
    report["os"]["architecture"] = platform.machine()
    
    if os.name == 'nt':
        # Get more detailed OS info on Windows
        os_info = run_powershell_json("Get-CimInstance Win32_OperatingSystem | Select-Object Caption, Version, OSArchitecture")
        if os_info:
            # Handle list or single dict
            if isinstance(os_info, list):
                os_info = os_info[0]
            report["os"]["name"] = os_info.get("Caption", platform.system()).strip()
            report["os"]["version"] = os_info.get("Version", platform.release())
            report["os"]["architecture"] = os_info.get("OSArchitecture", platform.machine())

    # Assess OS
    is_windows_64bit = report["os"]["name"].startswith("Microsoft Windows") and "64" in report["os"]["architecture"]
    if is_windows_64bit or report["os"]["name"] == "Windows":
        report["os"]["status"] = "Pass"
        report["os"]["message"] = f"{report['os']['name']} ({report['os']['architecture']}) is fully supported."
    else:
        report["os"]["status"] = "Minimum"
        report["os"]["message"] = f"Running on {report['os']['name']}. Windows 10/11 64-bit is recommended."

    # 2. CPU Detection
    cpu_cores_physical = psutil.cpu_count(logical=False) or 1
    cpu_cores_logical = psutil.cpu_count(logical=True) or 1
    cpu_max_speed_mhz = 0
    cpu_name = platform.processor()

    if os.name == 'nt':
        cpu_info = run_powershell_json("Get-CimInstance Win32_Processor | Select-Object Name, MaxClockSpeed")
        if cpu_info:
            if isinstance(cpu_info, list):
                cpu_info = cpu_info[0]
            cpu_name = cpu_info.get("Name", cpu_name).strip()
            cpu_max_speed_mhz = cpu_info.get("MaxClockSpeed", 0)

    # Clean up duplicate spaces in CPU name
    cpu_name = " ".join(cpu_name.split())
    cpu_speed_ghz = round(cpu_max_speed_mhz / 1000.0, 1) if cpu_max_speed_mhz > 0 else 0.0

    report["cpu"] = {
        "model": cpu_name,
        "cores": cpu_cores_physical,
        "threads": cpu_cores_logical,
        "clock_speed_ghz": cpu_speed_ghz if cpu_speed_ghz > 0 else "Unknown"
    }

    # Evaluate CPU
    cpu_score = 0
    # Physical Cores
    if cpu_cores_physical >= 4:
        cpu_score += 35
    elif cpu_cores_physical >= 2:
        cpu_score += 20
    else:
        cpu_score += 5

    # Logical Threads
    if cpu_cores_logical >= 8:
        cpu_score += 35
    elif cpu_cores_logical >= 4:
        cpu_score += 20
    else:
        cpu_score += 5

    # Speed (GHz)
    if cpu_speed_ghz >= 3.0:
        cpu_score += 30
    elif cpu_speed_ghz >= 2.0 or cpu_speed_ghz == 0.0: # Fallback if speed detection fails
        cpu_score += 20
    else:
        cpu_score += 5

    if cpu_score >= 80:
        report["cpu"]["status"] = "Recommended"
        report["cpu"]["message"] = f"Powerful CPU with {cpu_cores_physical} cores / {cpu_cores_logical} threads. Excellent for multi-threaded AI processing."
    elif cpu_score >= 40:
        report["cpu"]["status"] = "Minimum"
        report["cpu"]["message"] = f"Meets minimum CPU requirements ({cpu_cores_physical} cores). Expect moderate detection frame rates."
    else:
        report["cpu"]["status"] = "Fail"
        report["cpu"]["message"] = f"CPU may be too weak ({cpu_cores_physical} cores). Video processing might stutter or lag."

    # 3. GPU Detection
    cuda_available = False
    cuda_device_name = ""
    cuda_vram_gb = 0.0

    if TORCH_AVAILABLE:
        cuda_available = torch.cuda.is_available()
        if cuda_available:
            cuda_device_name = torch.cuda.get_device_name(0)
            try:
                cuda_prop = torch.cuda.get_device_properties(0)
                cuda_vram_gb = round(cuda_prop.total_memory / (1024 ** 3), 1)
            except Exception:
                pass

    report["apis"]["cuda_available"] = cuda_available
    report["apis"]["cuda_version"] = torch.version.cuda if (TORCH_AVAILABLE and cuda_available) else "N/A"
    
    # Check WMI GPUs on Windows
    wmi_gpus = []
    if os.name == 'nt':
        gpu_info_list = run_powershell_json("Get-CimInstance Win32_VideoController | Select-Object Name, AdapterRAM")
        if gpu_info_list:
            if not isinstance(gpu_info_list, list):
                gpu_info_list = [gpu_info_list]
            for g in gpu_info_list:
                name = g.get("Name", "")
                if not name:
                    continue
                
                # Try to parse RAM
                ram_bytes = g.get("AdapterRAM", 0)
                # Convert to GB. Note: Win32_VideoController can report capped AdapterRAM
                vram = round(ram_bytes / (1024 ** 3), 1) if ram_bytes else 0.0

                wmi_gpus.append({
                    "name": name,
                    "vram_gb": vram
                })

    # Classify GPUs (Dedicated vs Integrated)
    dedicated_keywords = ["NVIDIA", "GeForce", "RTX", "GTX", "Quadro", "Tesla", "Radeon RX", "Radeon Pro", "Intel Arc", "Intel(R) Arc"]
    
    # If WMI didn't return anything, check if CUDA is available and use it as a fallback
    if not wmi_gpus and cuda_available:
        wmi_gpus.append({
            "name": cuda_device_name,
            "vram_gb": cuda_vram_gb
        })

    for wg in wmi_gpus:
        name = wg["name"]
        vram = wg["vram_gb"]

        # If it's the active CUDA device, use PyTorch's more accurate VRAM detection
        is_active = False
        if cuda_available and cuda_device_name.lower() in name.lower():
            is_active = True
            if cuda_vram_gb > 0:
                vram = cuda_vram_gb

        # Categorize
        is_dedicated = any(keyword.lower() in name.lower() for keyword in dedicated_keywords) or vram >= 1.5
        gpu_type = "Dedicated" if is_dedicated else "Integrated"

        report["gpu"]["devices"].append({
            "name": name,
            "type": gpu_type,
            "vram_gb": vram if vram > 0 else "Shared",
            "is_active_ai": is_active
        })

    # If PyTorch has CUDA active, but we didn't match it in the list (e.g. string mismatch)
    # let's make sure the CUDA device is flagged.
    if cuda_available and not any(d["is_active_ai"] for d in report["gpu"]["devices"]):
        # Find if it is in the list under a slightly different name
        matched = False
        for dev in report["gpu"]["devices"]:
            if "nvidia" in dev["name"].lower() or "geforce" in dev["name"].lower():
                dev["is_active_ai"] = True
                if cuda_vram_gb > 0:
                    dev["vram_gb"] = cuda_vram_gb
                matched = True
                break
        
        if not matched:
            # Add it as a dedicated active device
            report["gpu"]["devices"].append({
                "name": cuda_device_name,
                "type": "Dedicated",
                "vram_gb": cuda_vram_gb,
                "is_active_ai": True
            })

    # If no devices at all, show CPU fallback
    if not report["gpu"]["devices"]:
        report["gpu"]["devices"].append({
            "name": "Software Rasterizer / Generic Graphics Adapter",
            "type": "Integrated",
            "vram_gb": "Shared",
            "is_active_ai": False
        })

    # Evaluate GPU Status
    has_dedicated = any(d["type"] == "Dedicated" for d in report["gpu"]["devices"])
    active_ai_gpu = next((d for d in report["gpu"]["devices"] if d["is_active_ai"]), None)

    gpu_score = 0
    if active_ai_gpu:
        # CUDA Active GPU
        vram_val = active_ai_gpu["vram_gb"] if isinstance(active_ai_gpu["vram_gb"], (int, float)) else 0.0
        if vram_val >= 4.0:
            gpu_score = 100
            report["gpu"]["status"] = "Recommended"
            report["gpu"]["message"] = f"Dedicated GPU ({active_ai_gpu['name']}) with {vram_val}GB VRAM is active for hardware-accelerated AI inference."
        else:
            gpu_score = 75
            report["gpu"]["status"] = "Minimum"
            report["gpu"]["message"] = f"Dedicated GPU ({active_ai_gpu['name']}) is active but has low VRAM ({vram_val}GB). Performance may be limited."
    elif has_dedicated:
        # Dedicated GPU exists but is not running in PyTorch (e.g. AMD or NVIDIA without CUDA configuration)
        dedicated_gpu = next(d for d in report["gpu"]["devices"] if d["type"] == "Dedicated")
        gpu_score = 55
        report["gpu"]["status"] = "Minimum"
        report["gpu"]["message"] = f"Dedicated GPU ({dedicated_gpu['name']}) found but is not active for AI. The system will fall back to CPU."
    else:
        # Integrated GPU only
        integrated_gpu = report["gpu"]["devices"][0]
        gpu_score = 35
        report["gpu"]["status"] = "Minimum"
        report["gpu"]["message"] = f"Using Integrated Graphics ({integrated_gpu['name']}). AI will run on CPU, which will limit video frame rates."

    # 4. RAM Detection
    ram_total_bytes = psutil.virtual_memory().total
    ram_total_gb = round(ram_total_bytes / (1024 ** 3), 1)
    report["ram"]["total_gb"] = ram_total_gb

    # Evaluate RAM
    ram_score = 0
    if ram_total_gb >= 15.0:
        ram_score = 100
        report["ram"]["status"] = "Recommended"
        report["ram"]["message"] = f"{ram_total_gb} GB RAM is installed. Meets recommended requirements."
    elif ram_total_gb >= 8.0:
        ram_score = 60
        report["ram"]["status"] = "Minimum"
        report["ram"]["message"] = f"{ram_total_gb} GB RAM is installed. Meets minimum requirements."
    else:
        ram_score = 20
        report["ram"]["status"] = "Fail"
        report["ram"]["message"] = f"Only {ram_total_gb} GB RAM is installed. 8 GB is required; system may experience out-of-memory crashes."

    # 5. Storage Detection
    try:
        disk_info = psutil.disk_usage(os.getcwd())
        disk_total_gb = round(disk_info.total / (1024 ** 3), 1)
        disk_free_gb = round(disk_info.free / (1024 ** 3), 1)
    except Exception:
        disk_total_gb = 0.0
        disk_free_gb = 0.0

    report["storage"] = {
        "total_gb": disk_total_gb,
        "free_gb": disk_free_gb
    }

    # Evaluate Storage
    storage_score = 0
    if disk_free_gb >= 20.0:
        storage_score = 100
        report["storage"]["status"] = "Recommended"
        report["storage"]["message"] = f"{disk_free_gb} GB free disk space available. Plenty of space for capturing violations and storing records."
    elif disk_free_gb >= 5.0:
        storage_score = 60
        report["storage"]["status"] = "Minimum"
        report["storage"]["message"] = f"{disk_free_gb} GB free disk space. Clean up old videos if disk space falls below 5 GB."
    else:
        storage_score = 20
        report["storage"]["status"] = "Fail"
        report["storage"]["message"] = f"Critically low disk space ({disk_free_gb} GB). System requires at least 5 GB free to operate properly."

    # 6. DirectX / Graphics API support check
    # Estimate support
    apis_report = {
        "directx": "DirectX 12 (Supported)" if report["os"]["name"].startswith("Microsoft Windows") or "Windows" in report["os"]["name"] else "N/A",
        "opengl": "OpenGL 4.6 (Supported)" if has_dedicated or active_ai_gpu else "OpenGL 4.0+ (Supported)",
        "vulkan": "Vulkan 1.3 (Supported)" if (has_dedicated or active_ai_gpu) else "Vulkan Supported"
    }
    report["apis"]["directx"] = apis_report["directx"]
    report["apis"]["opengl"] = apis_report["opengl"]
    report["apis"]["vulkan"] = apis_report["vulkan"]

    # 7. Calculate Overall Compatibility
    # Weightings: CPU (25%), GPU (35%), RAM (25%), Storage (15%)
    overall_score = round(
        (cpu_score * 0.25) +
        (gpu_score * 0.35) +
        (ram_score * 0.25) +
        (storage_score * 0.15)
    )

    suggestions = []
    
    # Generate Suggestions
    if report["cpu"]["status"] == "Fail":
        suggestions.append("Upgrade your CPU to at least 4 physical cores to prevent video decoding and tracking lag.")
    elif report["cpu"]["status"] == "Minimum":
        suggestions.append("Consider closing other heavy background applications to free up CPU cycles for AI detection.")

    if not cuda_available:
        suggestions.append("Install an NVIDIA Graphics Card (GTX 1050 Ti or better) and install the CUDA Toolkit to enable real-time GPU-accelerated detection.")
    elif cuda_available and active_ai_gpu and isinstance(active_ai_gpu["vram_gb"], (int, float)) and active_ai_gpu["vram_gb"] < 4.0:
        suggestions.append("Consider upgrading to a GPU with at least 4GB VRAM to run larger, more accurate YOLO detection models.")

    if report["ram"]["status"] == "Fail":
        suggestions.append("Upgrade system RAM to 8 GB or 16 GB. Low memory will cause severe slowdowns and crashes.")
    elif report["ram"]["status"] == "Minimum":
        suggestions.append("Close web browser tabs or background processes when running the AI monitor to maximize available RAM.")

    if report["storage"]["status"] == "Fail":
        suggestions.append("Free up at least 10 GB of space on your drive by deleting unused files or archiving old violation records.")

    # Determine Result Group
    if report["ram"]["status"] == "Fail" or report["storage"]["status"] == "Fail" or report["cpu"]["status"] == "Fail":
        result = "Does Not Meet Requirements"
        # Capping score if a critical component fails
        overall_score = min(overall_score, 45)
    elif report["gpu"]["status"] == "Recommended" and report["ram"]["status"] == "Recommended" and report["cpu"]["status"] == "Recommended":
        result = "Fully Compatible"
    else:
        result = "Meets Minimum Requirements"

    report["compatibility"] = {
        "score": overall_score,
        "result": result,
        "suggestions": suggestions
    }

    return report
