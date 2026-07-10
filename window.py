#!/usr/bin/env python3
"""BWV 772a — standalone native window (480×360, not browser / Cursor)."""
import os
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
# PyInstaller onefile: data next to exe or in _MEIPASS
if getattr(sys, "frozen", False):
    ROOT = getattr(sys, "_MEIPASS", os.path.dirname(sys.executable))
    # Prefer index beside the exe (easier to update without rebuild)
    beside = os.path.join(os.path.dirname(sys.executable), "index.html")
    if os.path.isfile(beside):
        ROOT = os.path.dirname(sys.executable)

INDEX = os.path.join(ROOT, "index.html")
CANVAS_W, CANVAS_H = 480, 360


def ensure_webview():
    try:
        import webview  # noqa: F401
        return
    except ImportError:
        pass
    import subprocess

    flags = subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0
    subprocess.check_call(
        [sys.executable, "-m", "pip", "install", "pywebview", "-q"],
        creationflags=flags,
    )


class Api:
    def __init__(self):
        self._window = None

    def quit(self):
        if self._window is not None:
            self._window.destroy()


def main():
    if not os.path.isfile(INDEX):
        raise SystemExit(f"missing: {INDEX}")

    os.chdir(ROOT)
    ensure_webview()
    import webview

    api = Api()
    window = webview.create_window(
        "BWV 772a",
        INDEX,
        width=CANVAS_W,
        height=CANVAS_H,
        resizable=False,
        frameless=True,
        easy_drag=True,
        background_color="#333333",
        js_api=api,
    )
    api._window = window

    def on_loaded():
        try:
            window.resize(CANVAS_W, CANVAS_H)
            window.evaluate_js(
                """
                (function () {
                  document.documentElement.style.cssText =
                    'margin:0;padding:0;overflow:hidden;width:480px;height:360px;';
                  document.body.style.cssText =
                    'margin:0;padding:0;overflow:hidden;width:480px;height:360px;background:#333;';
                  if (!window.__bwvEsc) {
                    window.__bwvEsc = true;
                    document.addEventListener('keydown', function (e) {
                      if (e.key === 'Escape' && window.pywebview && window.pywebview.api)
                        window.pywebview.api.quit();
                    });
                  }
                  return true;
                })()
                """
            )
        except Exception:
            pass

    window.events.loaded += on_loaded
    webview.start()


if __name__ == "__main__":
    main()
