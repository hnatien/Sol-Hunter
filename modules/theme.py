class Theme:
    """
    Centralized theme configuration for Sol Hunter.
    Cyber/Dark aesthetic with high contrast accents.
    """
    # Colors
    BG = "#0f0f12"
    SIDEBAR = "#09090b"
    CARD = "#16161a"
    ACCENT = "#a349a4"  # Glitched Purple
    ACCENT_HOVER = "#8a3d8a"
    SUCCESS = "#10b981" # Vibrant Green
    ERROR = "#ef4444"   # Red
    ERROR_HOVER = "#b91c1c"
    TEXT_MAIN = "#ffffff"
    TEXT_SUB = "#94a3b8"
    BORDER = "#26262b"
    HOVER = "#27272a"
    INPUT_BG = "#09090b"
    CONSOLE_BG = "#050505"
    
    # Fonts
    FONT_HEADER = ("Arial", 18, "bold")
    FONT_SUBHEADER = ("Arial", 12, "bold")
    FONT_BODY = ("Arial", 12)
    FONT_SMALL = ("Arial", 11)
    FONT_ICON = ("Arial", 13, "bold")

    @staticmethod
    def apply_appearance():
        import customtkinter as ctk
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue") # We override manual colors mostly
