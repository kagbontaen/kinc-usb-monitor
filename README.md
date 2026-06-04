# KINC USB Monitor

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

```bash
python -m nuitka --standalone --onefile --windows-icon-from-ico=src/icon.ico --include-data-file=src/icon.ico=src/icon.ico --windows-product-name="KINC USB Monitor" --product-version=1.0.0.0 --file-version=1.0.0.0 setupapi_usb_monitor.py
```

### Using PyInstaller

```bash
pyinstaller --onefile --icon=src/icon.ico --name="KINC USB Monitor" setupapi_usb_monitor.py
```

## License

MIT License - see LICENSE file for details

## Author

KINC <kinc7775@gmail.com>

## Notes

When building executables, ensure `src/icon.ico` is available in the resource path for notification icons to display properly.
