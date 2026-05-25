import sys
import uuid
import tkinter as tk
from tkinter import ttk
import json
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

COLORS = {
    "bg": "#F7FAFC",
    "text": "#1F2937",
    "muted": "#4B5563",
    "accent": "#2C5AA0",
    "accent_dark": "#20457A",
    "info_bg": "#E9F2FF",
    "info_border": "#B6D4FE",
}

class TelemetryConsentDialog:
    """One-time usage consent popup dialog"""
    
    def __init__(self, config_path: Path = None):
        self.config_path = config_path or Path.home() / '.p4mcp_telemetry_consent.json'
        self.result = {}
        self.root = None
        self.consent_var = None
    
    def _setup_window(self):
        """Initialize and configure the main window"""
        if sys.platform.startswith("win"):
            self._enable_windows_dpi_awareness()
        self.root = tk.Tk()
        # Scale Tk to actual DPI (1.0 == 72 DPI)
        try:
            dpi = self.root.winfo_fpixels('1i')  # pixels per inch
            self.root.tk.call('tk', 'scaling', dpi / 72.0)
        except Exception:
            pass

        self.root.configure(bg=COLORS["bg"])
        self.root.title("P4 MCP - Usage Consent")

        # DPI-aware, screen-relative geometry
        sw, sh = self.root.winfo_screenwidth(), self.root.winfo_screenheight()
        win_w = max(700, min(720, int(sw * 0.35)))
        win_h = max(400, min(720, int(sh * (0.42 if sys.platform.startswith("win") else 0.40))))
        self.root.geometry(f"{win_w}x{win_h}")
        self.root.minsize(650, 400)
        self.root.resizable(True, True)
        
        # Set custom icon
        try:
            if getattr(sys, 'frozen', False):
                icon_path = Path(sys.executable).parent.parent / "icons" / "logo-p4mcp-icon.png"
            else:
                icon_path = Path(__file__).parent.parent.parent / "icons" / "logo-p4mcp-icon.png"
            icon_img = tk.PhotoImage(file=str(icon_path))
            self.root.iconphoto(True, icon_img)
        except Exception as e:
            logger.error(f"Could not set custom icon: {e}")

        self._init_styles()
    
    def _enable_windows_dpi_awareness(self):
        if not sys.platform.startswith("win"):
            return
        try:
            import ctypes
            ctypes.windll.shcore.SetProcessDpiAwareness(2)  # per-monitor DPI aware
        except Exception:
            try:
                ctypes.windll.user32.SetProcessDPIAware()   # fallback
            except Exception:
                pass

    def _center_window(self):
        self.root.update_idletasks()
        w = self.root.winfo_width() or self.root.winfo_reqwidth()
        h = self.root.winfo_height() or self.root.winfo_reqheight()
        try:
            if sys.platform.startswith("win"):
                import ctypes, ctypes.wintypes as wintypes
                user32 = ctypes.windll.user32
                pt = wintypes.POINT()
                user32.GetCursorPos(ctypes.byref(pt))
                monitor = user32.MonitorFromPoint(pt, 2)  # NEAREST
                class RECT(ctypes.Structure):
                    _fields_ = [("left", ctypes.c_long), ("top", ctypes.c_long),
                                ("right", ctypes.c_long), ("bottom", ctypes.c_long)]
                class MONITORINFO(ctypes.Structure):
                    _fields_ = [("cbSize", ctypes.c_ulong),
                                ("rcMonitor", RECT), ("rcWork", RECT),
                                ("dwFlags", ctypes.c_ulong)]
                mi = MONITORINFO()
                mi.cbSize = ctypes.sizeof(MONITORINFO)
                user32.GetMonitorInfoW(monitor, ctypes.byref(mi))
                work_w = mi.rcWork.right - mi.rcWork.left
                work_h = mi.rcWork.bottom - mi.rcWork.top
                x = mi.rcWork.left + max(0, (work_w - w) // 2)
                y = mi.rcWork.top + max(0, (work_h - h) // 2)
            else:
                sw, sh = self.root.winfo_screenwidth(), self.root.winfo_screenheight()
                x = max(0, (sw - w) // 2)
                y = max(0, (sh - h) // 2)
        except Exception:
            sw, sh = self.root.winfo_screenwidth(), self.root.winfo_screenheight()
            x = max(0, (sw - w) // 2)
            y = max(0, (sh - h) // 2)
        self.root.geometry(f"{w}x{h}+{x}+{y}")
    
    def _init_styles(self):
        self.style = ttk.Style(self.root)
        try:
            self.style.theme_use("clam")
        except Exception:
            pass

        self.style.configure(
            "Accent.TButton",
            background=COLORS["accent"],
            foreground="white",
            font=("Arial", 12, "bold"),
            padding=(12, 6),
            borderwidth=0,
            focusthickness=0,
        )
        self.style.map(
            "Accent.TButton",
            background=[("active", COLORS["accent_dark"]), ("pressed", COLORS["accent_dark"])],
            foreground=[("disabled", "#9CA3AF")],
        )
    
    def _create_widgets(self):
        """Create and layout all widgets"""
        # Main frame with padding and bg
        main_frame = tk.Frame(self.root, padx=12, pady=10, bg=COLORS["bg"])
        main_frame.pack(fill="both", expand=True)

        # Product image
        try:
            if getattr(sys, 'frozen', False):
                product_image = tk.PhotoImage(file=Path(sys.executable).parent.parent / "icons" / "logo-p4mcp-reg.png")
            else:
                product_image = tk.PhotoImage(file=str(Path(__file__).parent.parent.parent / "icons" / "logo-p4mcp-reg.png"))
            product_image = product_image.subsample(2, 2)
        except Exception as e:
            logger.error(f"Could not load product image: {e}")
            product_image = None
        product_image_label = tk.Label(main_frame, image=product_image, bg=COLORS["bg"])
        product_image_label.image = product_image
        product_image_label.pack(pady=(0, 4))

        # Accent header
        header = tk.Frame(main_frame, bg=COLORS["accent"])
        header.pack(fill="x", pady=(4, 12))
        title_label = tk.Label(
            header,
            text="P4 MCP Usage Data Opt In",
            font=("Arial", 16, "bold"),
            bg=COLORS["accent"],
            fg="white",
        )
        title_label.pack(padx=14, pady=10)

        # Set font size based on platform
        if sys.platform.startswith("win"):
            message_font = 10
        else:
            message_font = 14

        # Description message
        message_text = """Perforce would like to collect anonymous usage & error data to help improve P4 MCP.

    Data collected includes:
    • Usage statistics and feature analytics
    • Performance metrics
    • Error reports

    All collected data is:
    • Anonymous and privacy compliant
    • Non-intrusive to your workflow
    • Used only for product improvement purposes

    Change your preference anytime by setting server args "--allow-usage" """

        # Info panel with subtle border and accent bar
        desc_container = tk.Frame(
            main_frame,
            bg=COLORS["info_bg"],
            highlightbackground=COLORS["info_border"],
            highlightthickness=1,
            bd=0,
        )
        desc_container.pack(fill="x", padx=8, pady=(0, 10))

        accent_bar = tk.Frame(desc_container, bg=COLORS["accent"], width=6)
        accent_bar.pack(side="left", fill="y")

        desc_inner = tk.Frame(desc_container, bg=COLORS["info_bg"])
        desc_inner.pack(side="left", fill="both", expand=True)

        message_label = tk.Label(
            desc_inner,
            text=message_text,
            font=("Arial", message_font),
            justify="left",
            wraplength=650,
            anchor="w",
            bg=COLORS["info_bg"],
            fg=COLORS["text"],
        )
        message_label.pack(anchor="w", padx=12, pady=10, fill="x")

        # Button frame
        self.style.configure(
            "Accent.TButton",
            background=COLORS["accent"],
            foreground="white",
            font=("Arial", message_font, "bold"), 
            padding=(8, 4),    
            borderwidth=0,
            focusthickness=0,
        )

        button_frame = tk.Frame(main_frame, bg=COLORS["bg"], )
        button_frame.pack(fill="x")

        button_container = tk.Frame(button_frame, bg=COLORS["bg"])
        button_container.pack(anchor="center", expand=True, fill="y")

        ok_button = ttk.Button(
            button_container,
            text="OK", 
            command=self._save_consent_and_close,
            style="Accent.TButton",
            cursor="hand2",
            takefocus=True,
            width=10,  # reduced width (in characters)
        )

        ok_button.pack(padx=0, pady=(5, 10))
        ok_button.focus_set()

    def _save_consent_and_close(self):
        """Save user's consent choice and close dialog"""

        self.result.update({
            'user_id': str(uuid.uuid4()).upper(),
            'dialog_shown': True
        })
        
        # Save to config file
        try:
            with open(self.config_path, 'w') as f:
                json.dump(self.result, f, indent=2)
        except IOError:
            logger.error("Could not save telemetry consent preference!")

        self.root.quit()
        
    def _decline_and_close(self):
        """Decline consent and close dialog"""
        self._save_consent_and_close()
    
    def _on_closing(self):
        """Handle window close event (treat as decline)"""
        self._decline_and_close()
    
    def show_dialog(self) -> dict:
        """Show the consent dialog and return the result"""
        self._setup_window()
        self._create_widgets()

        if not sys.platform.startswith("win"):
            self.root.after_idle(self._center_window)
        
        # Handle window close event
        self.root.protocol("WM_DELETE_WINDOW", self._on_closing)
        
        # Show dialog and wait for response
        self.root.mainloop()
        self.root.destroy()
        
        return self.result

def main():
    """Check if user has consented to telemetry collection"""
    dialog = TelemetryConsentDialog(config_path=Path.home() / '.p4mcp_telemetry_consent.json')
    consent_data = dialog.show_dialog()
    return consent_data.get('telemetry_consent', False)

if __name__ == "__main__":
    try:
        main()  
    except Exception as e:
        logger.error(f"Error in telemetry consent dialog: {e}")
        sys.exit(1)
