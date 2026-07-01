# KINC USB Monitor
<img width="981" height="516" alt="Screenshot 2026-06-05 144723" src="https://github.com/user-attachments/assets/4dcbda3a-ea35-43c7-9ed3-cf7c1f0a9c27" />
A fast USB device monitor for Windows using the SetupAPI (no WMI, no libusb dependencies).

## Features

- **Fast & Lightweight**: Uses Windows SetupAPI directly without WMI overhead
- **Real-time Monitoring**: Detects USB device connections and disconnections
- **Notifications**: Desktop notifications for device events (requires `plyer`)
- **Callbacks**: Custom callbacks for `on_connect` and `on_disconnect` events
- **Standalone Executable**: Can be compiled to a standalone .exe with PyInstaller or Nuitka

## Requirements

- Windows OS
- Python 3.7+
- `plyer` (optional, for desktop notifications)

## Installation

```bash
pip install -r requirements.txt
```

## Usage

### As a Module

```python
from setupapi_usb_monitor import SetupAPIUSBMonitor

def on_connect(hwid, name):
    print(f"Device connected: {name}")

def on_disconnect(hwid, name):
    print(f"Device disconnected: {name}")

monitor = SetupAPIUSBMonitor()
monitor.start(on_connect=on_connect, on_disconnect=on_disconnect)
```

### As a Standalone Script

```bash
python setupapi_usb_monitor.py
```

Press `Ctrl+C` to stop monitoring.

## Building Standalone Executable

### Using Nuitka

```cmd
python -m nuitka --standalone --onefile --windows-icon-from-ico=icon.ico --include-data-file=icon.ico=icon.ico --windows-product-name="KINC USB Monitor" --product-version=1.1.0.0 --file-version=1.1.0.0 setupapi_usb_monitor.py
```

### Using PyInstaller

```cmd
pyinstaller --onefile --icon=src/icon.ico --name="KINC USB Monitor" setupapi_usb_monitor.py
```
### Running the Standalone Version

```cmd
start /min setupapi_usb_monitor.exe
```

## License

MIT License - see LICENSE file for details

## Author

KINC <kinc7775@gmail.com>

## Notes

When building executables, ensure `src/icon.ico` is available in the resource path for notification icons to display properly.
