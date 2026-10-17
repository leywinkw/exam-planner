from tkinter import ttk

FONT = "Helvetica Neue"

BG = "#eef2f7"        # window background
CARD = "#ffffff"      # cards
BORDER = "#dbe3ee"
TEXT = "#0f172a"
MUTED = "#64748b"
ACCENT = "#4f46e5"    # indigo
ACCENT_DARK = "#4338ca"
ACCENT_SOFT = "#e0e7ff"
HEADER = "#1e1b4b"
DANGER = "#b91c1c"
WARN_BG = "#fef2f2"


def font(size=12, weight="normal"):
    return (FONT, size, weight)


def apply_style(root):
    style = ttk.Style(root)
    style.theme_use("clam")
    root.configure(bg=BG)
    style.configure(".", background=CARD, foreground=TEXT, font=font(12), bordercolor=BORDER,
                    focuscolor=CARD)
    style.configure("TFrame", background=CARD)
    style.configure("Page.TFrame", background=BG)
    style.configure("Header.TFrame", background=HEADER)
    style.configure("TLabel", background=CARD, foreground=TEXT)
    style.configure("Muted.TLabel", foreground=MUTED, font=font(11))
    style.configure("H.TLabel", font=font(15, "bold"))
    style.configure("Section.TLabel", font=font(12, "bold"), foreground=ACCENT)
    style.configure("Title.TLabel", background=HEADER, foreground="white", font=font(20, "bold"))
    style.configure("Sub.TLabel", background=HEADER, foreground="#c7d2fe", font=font(12))
    style.configure("Status.TLabel", background=CARD, foreground=MUTED, font=font(12))

    style.configure("TButton", padding=(12, 6), background="#f1f5f9", foreground=TEXT,
                    bordercolor=BORDER, relief="flat")
    style.map("TButton", background=[("active", "#e2e8f0")])
    style.configure("Accent.TButton", background=ACCENT, foreground="white", bordercolor=ACCENT,
                    font=font(12, "bold"))
    style.map("Accent.TButton", background=[("active", ACCENT_DARK)])
    style.configure("Danger.TButton", foreground=DANGER)

    style.configure("TEntry", fieldbackground="white", bordercolor=BORDER, padding=5)
    style.configure("TCombobox", fieldbackground="white", bordercolor=BORDER, padding=5,
                    arrowcolor=MUTED)
    style.map("TCombobox", fieldbackground=[("readonly", "white")],
              selectbackground=[("readonly", "white")], selectforeground=[("readonly", TEXT)])
    style.configure("TSpinbox", fieldbackground="white", bordercolor=BORDER, padding=4)

    style.configure("Treeview", rowheight=28, background="white", fieldbackground="white",
                    bordercolor=BORDER, borderwidth=1, font=font(12))
    style.map("Treeview", background=[("selected", ACCENT_SOFT)],
              foreground=[("selected", TEXT)])
    style.configure("Treeview.Heading", background="#f8fafc", foreground=MUTED,
                    font=font(11, "bold"), relief="flat", padding=(6, 5))

    style.configure("TNotebook", background=CARD, borderwidth=0, tabmargins=(0, 0, 0, 0))
    style.configure("TNotebook.Tab", padding=(18, 9), background="#f1f5f9", foreground=MUTED,
                    font=font(12, "bold"), borderwidth=0)
    style.map("TNotebook.Tab", background=[("selected", CARD)], foreground=[("selected", ACCENT)])
    style.configure("Horizontal.TScrollbar", background="#e2e8f0", troughcolor=CARD)
    style.configure("Vertical.TScrollbar", background="#e2e8f0", troughcolor=CARD)
