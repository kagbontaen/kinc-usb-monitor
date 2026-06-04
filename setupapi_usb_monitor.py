#!/usr/bin/env python3
"""
setupapi_usb_monitor.py
Fast USB monitor using Windows SetupAPI (no WMI, no libusb).

Copyright (c) 2024-2026 KINC
Author: KINC <kinc7775@gmail.com>
License: MIT
Created: 2024-01-01
Last-Modified: 2026-06-04

This module exposes `SetupAPIUSBMonitor` which watches for USB connect
and disconnect events by querying the Windows SetupAPI device list.

Notes:
- When building a standalone executable with PyInstaller or Nuitka,
  include the `src/icon.ico` resource so notification icons work.
  python -m nuitka --standalone --onefile --windows-icon-from-ico=src/icon.ico --include-data-file=src/icon.ico=src/icon.ico --windows-product-name="KINC USB Monitor" src/setupapi_usb_monitor.py
"""

import ctypes
import time
import os
import sys

from ctypes import wintypes
try:
    from plyer import notification
    plyer_available = True
except ImportError:
    plyer_available = False


def _resource_path(relative_path):
    """Return the path to a resource, handling frozen bundles."""
    if getattr(sys, "frozen", False):
        base_path = getattr(sys, "_MEIPASS", os.path.dirname(sys.executable))
    else:
        base_path = os.path.dirname(__file__)
    return os.path.join(base_path, relative_path)


icon_path = None
for candidate in ("icon.ico", os.path.join("src", "icon.ico")):
    path = _resource_path(candidate)
    if os.path.exists(path):
        icon_path = path
        break
app = "KINC USB Monitor"


class SetupAPIUSBMonitor:
    """
    Fast USB monitor using Windows SetupAPI (no WMI, no libusb).
    """

    DIGCF_PRESENT = 0x02
    DIGCF_ALLCLASSES = 0x04

    SPDRP_DEVICEDESC = 0x00000000
    SPDRP_HARDWAREID = 0x00000001

    INVALID_HANDLE_VALUE = -1

    class SP_DEVINFO_DATA(ctypes.Structure):
        _fields_ = [
            ("cbSize", wintypes.DWORD),
            ("ClassGuid", ctypes.c_byte * 16),
            ("DevInst", wintypes.DWORD),
            ("Reserved", ctypes.c_void_p),
        ]

    def __init__(self):
        self.stop_event = False

        self.setupapi = ctypes.WinDLL("setupapi")

        self.setupapi.SetupDiGetClassDevsW.restype = wintypes.HANDLE
        self.setupapi.SetupDiGetClassDevsW.argtypes = [
            ctypes.c_void_p,
            wintypes.LPCWSTR,
            wintypes.HWND,
            wintypes.DWORD
        ]

        self.setupapi.SetupDiEnumDeviceInfo.restype = wintypes.BOOL
        self.setupapi.SetupDiEnumDeviceInfo.argtypes = [
            wintypes.HANDLE,
            wintypes.DWORD,
            ctypes.POINTER(self.SP_DEVINFO_DATA)
        ]

        self.setupapi.SetupDiGetDeviceRegistryPropertyW.restype = wintypes.BOOL
        self.setupapi.SetupDiGetDeviceRegistryPropertyW.argtypes = [
            wintypes.HANDLE,
            ctypes.POINTER(self.SP_DEVINFO_DATA),
            wintypes.DWORD,
            ctypes.POINTER(wintypes.DWORD),
            ctypes.c_void_p,
            wintypes.DWORD,
            ctypes.POINTER(wintypes.DWORD)
        ]

        self.setupapi.SetupDiDestroyDeviceInfoList.restype = wintypes.BOOL
        self.setupapi.SetupDiDestroyDeviceInfoList.argtypes = [wintypes.HANDLE]

    def _get_devices(self):
        devices = {}

        device_info_set = self.setupapi.SetupDiGetClassDevsW(
            None,
            "USB",
            None,
            self.DIGCF_PRESENT | self.DIGCF_ALLCLASSES,
        )

        if device_info_set == self.INVALID_HANDLE_VALUE or device_info_set == 0:
            return devices

        try:
            index = 0

            while True:
                devinfo = self.SP_DEVINFO_DATA()
                devinfo.cbSize = ctypes.sizeof(self.SP_DEVINFO_DATA)

                if not self.setupapi.SetupDiEnumDeviceInfo(device_info_set, index, ctypes.byref(devinfo)):
                    break

                index += 1

                name_buf = ctypes.create_unicode_buffer(512)
                hwid_buf = ctypes.create_unicode_buffer(1024)
                required = wintypes.DWORD()

                self.setupapi.SetupDiGetDeviceRegistryPropertyW(
                    device_info_set,
                    ctypes.byref(devinfo),
                    self.SPDRP_DEVICEDESC,
                    None,
                    ctypes.cast(name_buf, ctypes.c_void_p),
                    ctypes.sizeof(name_buf),
                    ctypes.byref(required),
                )

                self.setupapi.SetupDiGetDeviceRegistryPropertyW(
                    device_info_set,
                    ctypes.byref(devinfo),
                    self.SPDRP_HARDWAREID,
                    None,
                    ctypes.cast(hwid_buf, ctypes.c_void_p),
                    ctypes.sizeof(hwid_buf),
                    ctypes.byref(required),
                )

                name = name_buf.value
                hwid = hwid_buf.value

                if hwid:
                    devices[hwid] = name
        finally:
            self.setupapi.SetupDiDestroyDeviceInfoList(device_info_set)

        return devices

    def start(self, on_connect=None, on_disconnect=None, interval=0.1):
        print("[*] SetupAPI USB monitor started")
        if plyer_available:
            notification.notify(
                title="USB Monitor Started",
                message="Monitoring USB devices connected...",
                app_icon=icon_path if icon_path else None,
                app_name=app,
                timeout=5,
            )

        prev = self._get_devices()
        if len(prev) > 0:
            i = 0
            while i < 1:
                print(f"[*] Initial devices: {len(prev)}")

                for hwid, name in prev.items():
                    print(f"[+] CONNECTED {name} | {hwid}")
                    i += 1

        while not self.stop_event:
            time.sleep(interval)

            curr = self._get_devices()

            # CONNECTED
            for hwid, name in curr.items():
                if hwid not in prev:
                    print(f"[+] CONNECTED: {name} | {hwid}")
                    if plyer_available:
                        notification.notify(
                            title="USB Device Connected",
                            message=f"{name}\n{hwid}",
                            app_icon=icon_path if icon_path else None,
                            app_name=app,
                            timeout=5,
                        )
                    if on_connect:
                        on_connect(hwid, name)

            # DISCONNECTED
            for hwid, name in prev.items():
                if hwid not in curr:
                    print(f"[-] DISCONNECTED: {name} | {hwid}")
                    if plyer_available:
                        notification.notify(
                            title="USB Device Disconnected",
                            message=f"{name}\n{hwid}",
                            app_icon=icon_path if icon_path else None,
                            app_name=app,
                            timeout=5,
                        )
                    if on_disconnect:
                        on_disconnect(hwid, name)

            prev = curr

    def stop(self):
        self.stop_event = True


# =========================
# Example usage
# =========================
if __name__ == "__main__":
    monitor = SetupAPIUSBMonitor()

    try:
        monitor.start()
    except KeyboardInterrupt:
        monitor.stop()
        print("\n[✓] Stopped")
        if plyer_available:
            notification.notify(
                title="USB Monitor Stopped",
                message="Stopped monitoring USB devices.",
                app_icon=icon_path if icon_path else None,
                app_name=app,
                timeout=5,
            )
