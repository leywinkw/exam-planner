"""Делает скриншоты окна для презентации и отчёта прямо из программы.

    python3 screenshots.py

Скрипт открывает настоящее окно с примерными данными, проходит короткий сценарий и сохраняет
каждый шаг в docs/screens/ (PNG, только окно). Окно снимает сама программа через оконный сервер
macOS, поэтому разрешение на запись экрана не нужно. Только macOS.
"""
import ctypes
import ctypes.util
import sys
import tempfile
import time
import tkinter as tk
from datetime import date, timedelta
from pathlib import Path

from demo import find_notebook, sample_planner
from planner.scheduler import Planner
from planner.storage import Storage
from ui.app import App
from ui.dialogs import MultiTopicDialog

OUT = Path(__file__).parent / "docs" / "screens"


class CGRect(ctypes.Structure):
    _fields_ = [("x", ctypes.c_double), ("y", ctypes.c_double), ("w", ctypes.c_double), ("h", ctypes.c_double)]


_objc = ctypes.cdll.LoadLibrary(ctypes.util.find_library("objc"))
_objc.objc_getClass.restype = ctypes.c_void_p
_objc.objc_getClass.argtypes = [ctypes.c_char_p]
_objc.sel_registerName.restype = ctypes.c_void_p
_objc.sel_registerName.argtypes = [ctypes.c_char_p]
_cg = ctypes.CDLL("/System/Library/Frameworks/ApplicationServices.framework/ApplicationServices")
_cf = ctypes.CDLL(ctypes.util.find_library("CoreFoundation"))
_io = ctypes.CDLL("/System/Library/Frameworks/ImageIO.framework/ImageIO")


def _send(obj, selector, restype=ctypes.c_void_p):
    _objc.objc_msgSend.restype = restype
    _objc.objc_msgSend.argtypes = [ctypes.c_void_p, ctypes.c_void_p]
    return _objc.objc_msgSend(obj, _objc.sel_registerName(selector))


def front_window_number(prefer_key=False):
    """Number of the window that is main (or key, for dialogs) in this application."""
    app = _send(_objc.objc_getClass(b"NSApplication"), b"sharedApplication")
    first, second = (b"keyWindow", b"mainWindow") if prefer_key else (b"mainWindow", b"keyWindow")
    window = _send(app, first) or _send(app, second)
    return _send(window, b"windowNumber", ctypes.c_long)


def save_window_png(window_number, path):
    """Saves one window of this application (with its title bar) as PNG; returns True on success."""
    _cg.CGWindowListCreateImage.restype = ctypes.c_void_p
    _cg.CGWindowListCreateImage.argtypes = [CGRect, ctypes.c_uint32, ctypes.c_uint32, ctypes.c_uint32]
    everything = CGRect(float("inf"), float("inf"), 0.0, 0.0)
    image = _cg.CGWindowListCreateImage(everything, 8, window_number, 1 | 8)  # this window only, best resolution
    if not image:
        return False
    _cf.CFStringCreateWithCString.restype = ctypes.c_void_p
    _cf.CFStringCreateWithCString.argtypes = [ctypes.c_void_p, ctypes.c_char_p, ctypes.c_uint32]
    _cf.CFURLCreateFromFileSystemRepresentation.restype = ctypes.c_void_p
    _cf.CFURLCreateFromFileSystemRepresentation.argtypes = [ctypes.c_void_p, ctypes.c_char_p, ctypes.c_long, ctypes.c_bool]
    _io.CGImageDestinationCreateWithURL.restype = ctypes.c_void_p
    _io.CGImageDestinationCreateWithURL.argtypes = [ctypes.c_void_p, ctypes.c_void_p, ctypes.c_size_t, ctypes.c_void_p]
    _io.CGImageDestinationAddImage.argtypes = [ctypes.c_void_p, ctypes.c_void_p, ctypes.c_void_p]
    _io.CGImageDestinationFinalize.restype = ctypes.c_bool
    _io.CGImageDestinationFinalize.argtypes = [ctypes.c_void_p]
    kind = _cf.CFStringCreateWithCString(None, b"public.png", 0x08000100)
    raw = str(path).encode()
    url = _cf.CFURLCreateFromFileSystemRepresentation(None, raw, len(raw), False)
    destination = _io.CGImageDestinationCreateWithURL(url, kind, 1, None)
    _io.CGImageDestinationAddImage(destination, image, None)
    return bool(_io.CGImageDestinationFinalize(destination))


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    today = date.today()
    storage = Storage(tempfile.mkdtemp(prefix="exam_planner_shots_"))

    root = tk.Tk()
    root.title("Планировщик подготовки к экзаменам")
    root.geometry("1240x860+40+40")
    app = App(root, storage)

    def settle(seconds=0.4):
        root.update()
        time.sleep(seconds)
        root.update()

    def shot(name, prefer_key=False):
        settle()
        ok = save_window_png(front_window_number(prefer_key), OUT / name)
        print(("saved  " if ok else "FAILED ") + name)
        return ok

    def load(planner):
        app.planner = planner
        app._changed()

    # 1. empty window: hints inside the fields
    shot("s1_empty.png")

    # 2. exams and topics entered: calendar of workload, day selected
    load(sample_planner(today))
    app.select_day(today + timedelta(days=2))
    shot("01_calendar.png")

    # 3. Gantt chart
    notebook = find_notebook(root)
    notebook.select(1)
    shot("02_gantt.png")

    # 4. not enough time: lower the daily limit, the warning and red rows appear
    planner = sample_planner(today)
    planner.set_daily_limit(2)
    load(planner)
    shot("s4_risk_gantt.png")
    notebook.select(0)
    shot("s4_risk_calendar.png")

    # 5. dialog for several topics
    load(sample_planner(today))
    event = "Программирование на Python"
    app.topic_exam.set(event)
    app.update_dropdowns()
    dialog = MultiTopicDialog(root, event, ["Основы Python"])
    for _name, var in dialog.vars[:3]:
        var.set(True)
    dialog.extra.insert(0, "Работа с файлами")
    dialog.lift()
    dialog.focus_force()
    shot("03_dialog.png", prefer_key=True)
    dialog.destroy()

    root.destroy()


if __name__ == "__main__":
    if sys.platform != "darwin":
        sys.exit("screenshots.py works on macOS only")
    main()
