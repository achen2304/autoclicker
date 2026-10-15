import threading
import time
import tkinter as tk
from tkinter import ttk

from pynput import keyboard, mouse

HOTKEY = keyboard.Key.f6
PICK_DELAY_SECONDS = 3


class AutoClickerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Autoclicker")
        self.root.resizable(False, False)

        self.mouse_controller = mouse.Controller()
        self.keyboard_controller = keyboard.Controller()
        self.running = threading.Event()
        self.click_thread = None

        self.target_pos = None
        self.target_key = None
        self.capturing_key = False
        self.interval_ms = tk.StringVar(value="100")
        self.button_choice = tk.StringVar(value="Left")
        self.status_text = tk.StringVar(value="Stopped")
        self.position_text = tk.StringVar(value="Not set (using live cursor position)")
        self.key_text = tk.StringVar(value="Not set")

        self._build_ui()
        self._start_hotkey_listener()

    def _build_ui(self):
        pad = {"padx": 10, "pady": 6}
        frame = ttk.Frame(self.root)
        frame.grid(row=0, column=0, sticky="nsew", **pad)

        ttk.Label(frame, text="Click interval (ms):").grid(row=0, column=0, sticky="w")
        ttk.Entry(frame, textvariable=self.interval_ms, width=10).grid(row=0, column=1, sticky="w")

        ttk.Label(frame, text="Press:").grid(row=1, column=0, sticky="w")
        ttk.Combobox(
            frame,
            textvariable=self.button_choice,
            values=["Left", "Right", "Middle", "Keyboard key"],
            state="readonly",
            width=14,
        ).grid(row=1, column=1, sticky="w")

        ttk.Label(frame, text="Keyboard key:").grid(row=2, column=0, sticky="w")
        ttk.Label(frame, textvariable=self.key_text).grid(row=2, column=1, sticky="w", columnspan=2)

        ttk.Button(frame, text="Record Key", command=self.record_key).grid(
            row=3, column=0, columnspan=2, sticky="we", pady=(4, 8)
        )

        ttk.Label(frame, text="Click location:").grid(row=4, column=0, sticky="w")
        ttk.Label(frame, textvariable=self.position_text).grid(row=4, column=1, sticky="w", columnspan=2)

        ttk.Button(frame, text="Pick Location (3s delay)", command=self.pick_location).grid(
            row=5, column=0, columnspan=2, sticky="we", pady=(4, 4)
        )
        ttk.Button(frame, text="Use Live Cursor Position", command=self.clear_location).grid(
            row=6, column=0, columnspan=2, sticky="we"
        )

        ttk.Separator(frame).grid(row=7, column=0, columnspan=3, sticky="we", pady=8)

        self.toggle_button = ttk.Button(frame, text="Start (F6)", command=self.toggle)
        self.toggle_button.grid(row=8, column=0, columnspan=2, sticky="we")

        ttk.Label(frame, text="Status:").grid(row=9, column=0, sticky="w", pady=(8, 0))
        ttk.Label(frame, textvariable=self.status_text).grid(row=9, column=1, sticky="w", pady=(8, 0))

        ttk.Label(
            frame,
            text="Press F6 anytime (even while Roblox is focused) to start/stop.",
            foreground="gray",
        ).grid(row=10, column=0, columnspan=3, sticky="w", pady=(10, 0))

    def record_key(self):
        self.capturing_key = True
        self.status_text.set("Press any key to record...")

    def pick_location(self):
        self.status_text.set(f"Move mouse to target... capturing in {PICK_DELAY_SECONDS}s")

        def countdown():
            for remaining in range(PICK_DELAY_SECONDS, 0, -1):
                self.status_text.set(f"Capturing position in {remaining}...")
                time.sleep(1)
            pos = self.mouse_controller.position
            self.target_pos = pos
            self.position_text.set(f"Fixed at {pos}")
            self.status_text.set("Stopped")

        threading.Thread(target=countdown, daemon=True).start()

    def clear_location(self):
        self.target_pos = None
        self.position_text.set("Not set (using live cursor position)")

    def toggle(self):
        if self.running.is_set():
            self.stop()
        else:
            self.start()

    def start(self):
        try:
            interval = max(1, int(self.interval_ms.get())) / 1000.0
        except ValueError:
            self.status_text.set("Invalid interval - enter a number")
            return

        choice = self.button_choice.get()
        if choice == "Keyboard key":
            if self.target_key is None:
                self.status_text.set("No key recorded - click Record Key")
                return
            key = self.target_key
            press = lambda: self.keyboard_controller.tap(key)
        else:
            button = {"Left": mouse.Button.left, "Right": mouse.Button.right,
                      "Middle": mouse.Button.middle}[choice]
            press = lambda: self.mouse_controller.click(button, 1)

        self.running.set()
        self.status_text.set("Running")
        self.toggle_button.config(text="Stop (F6)")

        def click_loop():
            while self.running.is_set():
                if self.target_pos is not None:
                    self.mouse_controller.position = self.target_pos
                press()
                time.sleep(interval)

        self.click_thread = threading.Thread(target=click_loop, daemon=True)
        self.click_thread.start()

    def stop(self):
        self.running.clear()
        self.status_text.set("Stopped")
        self.toggle_button.config(text="Start (F6)")

    def _start_hotkey_listener(self):
        def on_press(key):
            if self.capturing_key:
                self.capturing_key = False
                self.target_key = key
                name = getattr(key, "char", None) or key.name
                self.root.after(0, lambda: (self.key_text.set(name), self.status_text.set("Stopped")))
                return
            if key == HOTKEY:
                self.root.after(0, self.toggle)

        listener = keyboard.Listener(on_press=on_press)
        listener.daemon = True
        listener.start()


def main():
    root = tk.Tk()
    AutoClickerApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
