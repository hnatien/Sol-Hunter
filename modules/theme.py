class Theme:
    BG = "#0f0f12"
    SIDEBAR = "#09090b"
    CARD = "#16161a"
    ACCENT = "#a349a4"
    ACCENT_HOVER = "#8a3d8a"
    SUCCESS = "#10b981"
    ERROR = "#ef4444"
    ERROR_HOVER = "#b91c1c"
    TEXT_MAIN = "#ffffff"
    TEXT_SUB = "#94a3b8"
    BORDER = "#26262b"
    HOVER = "#27272a"
    INPUT_BG = "#09090b"
    CONSOLE_BG = "#050505"
    
    FONT_HEADER = ("Arial", 18, "bold")
    FONT_SUBHEADER = ("Arial", 12, "bold")
    FONT_BODY = ("Arial", 12)
    FONT_SMALL = ("Arial", 11)
    FONT_ICON = ("Arial", 13, "bold")

    @staticmethod
    def applyAppearance():
        import customtkinter as ctk
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")
