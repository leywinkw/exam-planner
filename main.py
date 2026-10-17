import tkinter as tk
from pathlib import Path

from planner.storage import Storage
from ui.app import App


def main():
    root = tk.Tk()
    root.title("Планировщик подготовки к экзаменам")
    root.geometry("1240x860")
    root.minsize(1100, 760)
    App(root, Storage(Path(__file__).parent / "data"))
    root.mainloop()


if __name__ == "__main__":
    main()
