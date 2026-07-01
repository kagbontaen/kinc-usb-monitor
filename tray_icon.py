import threading
import os
try:
    from pystray import Icon, MenuItem, Menu
    from pystray._util import win32 as pystray_win32
    from PIL import Image
except Exception as e:
    # Import errors are handled by caller; keep module importable
    Icon = None
    MenuItem = None
    Menu = None
    Image = None
    pystray_win32 = None

WM_LBUTTONDBLCLK = 0x0203


class TrayIcon(Icon):
    def __init__(self, *args, toggle_callback=None, **kwargs):
        self._toggle_callback = toggle_callback
        super(TrayIcon, self).__init__(*args, **kwargs)

    def _on_notify(self, wparam, lparam):
        if lparam == WM_LBUTTONDBLCLK:
            if callable(self._toggle_callback):
                try:
                    self._toggle_callback()
                except Exception:
                    pass
        else:
            return super(TrayIcon, self)._on_notify(wparam, lparam)


class TrayNotifier:
    """Simple system tray icon that delegates notifications to plyer.

    Requires `pystray` and `Pillow` to show a persistent tray icon.
    The notifier will call the provided `on_quit` callback when the user
    selects Exit from the tray menu.
    """

    def __init__(self, icon_path=None, app_name="App", on_quit=None):
        if Icon is None or Image is None:
            raise ImportError("pystray and Pillow are required for TrayNotifier")
        self.icon_path = icon_path
        self.app_name = app_name
        self.on_quit = on_quit
        self.icon = None
        self._thread = None

    def _create_image(self):
        if self.icon_path and os.path.exists(self.icon_path):
            try:
                return Image.open(self.icon_path)
            except Exception:
                pass
        # fallback solid square
        img = Image.new("RGBA", (64, 64), (0, 128, 255, 255))
        return img

    def _on_quit(self, icon, item):
        if callable(self.on_quit):
            try:
                self.on_quit()
            except Exception:
                pass
        try:
            icon.stop()
        except Exception:
            pass

    def _get_console_hwnd(self):
        try:
            import ctypes
            kernel32 = ctypes.WinDLL("kernel32")
            user32 = ctypes.WinDLL("user32")
            GetConsoleWindow = kernel32.GetConsoleWindow
            GetConsoleWindow.restype = ctypes.c_void_p
            hwnd = GetConsoleWindow()
            return hwnd
        except Exception:
            return None

    def _show_console(self):
        """Show the Windows console window and bring it to the foreground."""
        try:
            import ctypes
            hwnd = self._get_console_hwnd()
            if not hwnd:
                return
            SW_SHOW = 5
            user32 = ctypes.WinDLL("user32")
            user32.ShowWindow(hwnd, SW_SHOW)
            user32.SetForegroundWindow(hwnd)
        except Exception:
            pass

    def _hide_console(self):
        """Hide the Windows console window."""
        try:
            import ctypes
            hwnd = self._get_console_hwnd()
            if not hwnd:
                return
            SW_HIDE = 0
            user32 = ctypes.WinDLL("user32")
            user32.ShowWindow(hwnd, SW_HIDE)
        except Exception:
            pass

    def _is_console_visible(self):
        try:
            import ctypes
            hwnd = self._get_console_hwnd()
            if not hwnd:
                return False
            user32 = ctypes.WinDLL("user32")
            IsWindowVisible = user32.IsWindowVisible
            IsWindowVisible.restype = ctypes.c_bool
            return bool(IsWindowVisible(hwnd))
        except Exception:
            return False

    def _toggle_console(self):
        """Toggle the Windows console window visibility."""
        try:
            import ctypes
            hwnd = self._get_console_hwnd()
            if not hwnd:
                return
            SW_HIDE = 0
            SW_SHOW = 5
            user32 = ctypes.WinDLL("user32")
            IsWindowVisible = user32.IsWindowVisible
            IsWindowVisible.restype = ctypes.c_bool
            visible = IsWindowVisible(hwnd)
            if visible:
                user32.ShowWindow(hwnd, SW_HIDE)
            else:
                user32.ShowWindow(hwnd, SW_SHOW)
                user32.SetForegroundWindow(hwnd)
        except Exception:
            pass

    def _get_toggle_label(self):
        return "Hide Window" if self._is_console_visible() else "Show Window"

    def _refresh_menu(self):
        if self.icon is None:
            return
        self.icon.menu = self._create_menu()
        try:
            self.icon.update_menu()
        except Exception:
            pass

    def _on_toggle_console(self, icon, item):
        try:
            self._toggle_console()
        except Exception:
            pass
        self._refresh_menu()

    def _create_menu(self):
        return Menu(
            MenuItem(self._get_toggle_label(), self._on_toggle_console),
            MenuItem("Exit", self._on_quit),
        )

    def _setup_icon(self):
        image = self._create_image()
        self.icon = TrayIcon(
            self.app_name,
            image,
            self.app_name,
            menu=self._create_menu(),
            toggle_callback=self._toggle_console,
        )

    def _run(self):
        self._setup_icon()
        try:
            self.icon.run()
        except Exception:
            pass

    def start(self):
        if self.icon is not None:
            return
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def stop(self):
        if self.icon is None:
            return
        try:
            self.icon.stop()
        except Exception:
            pass

    def notify(self, title, message, app_icon=None, timeout=5):
        # Use plyer if available for system notification popups
        try:
            from plyer import notification
            notification.notify(title=title, message=message, app_icon=app_icon, app_name=self.app_name, timeout=timeout)
        except Exception:
            pass
