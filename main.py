import threading
import time
import tkinter as tk
from tkinter import ttk

from pynput import keyboard, mouse

HOTKEY = keyboard.Key.f6
PICK_DELAY_SECONDS = 3
BUTTONS = {
    "Left": mouse.Button.left,
    "Right": mouse.Button.right,
    "Middle": mouse.Button.middle,
}
KEYBOARD_CHOICE = "Keyboard key"


def parse_interval(text):
    """Milliseconds string -> seconds float, or None if unparseable."""
    try:
        return max(1, int(text)) / 1000.0
    except ValueError:
        return None


def key_label(key):
    return getattr(key, "char", None) or key.name


class AutoClickerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Autoclicker")
        self.root.resizable(False, False)

        self.mouse_controller = mouse.Controller()
        self.keyboard_controller = keyboard.Controller()
        self.running = threading.Event()
        self.threads = []
        self.inputs = []

        self.target_pos = None
        self.target_key = None
        self.capturing_key = False
        self.interval_ms = tk.StringVar(value="100")
        self.press_choice = tk.StringVar(value="Left")
        self.status_text = tk.StringVar(value="Stopped")
        self.position_text = tk.StringVar(value="Live cursor position")
        self.key_text = tk.StringVar(value="Not set")

        self._build_ui()
        self._start_hotkey_listener()

    def _build_ui(self):
        frame = ttk.Frame(self.root)
        frame.grid(row=0, column=0, sticky="nsew", padx=10, pady=8)

        editor = ttk.LabelFrame(frame, text="New input")
        editor.grid(row=0, column=0, sticky="we")

        ttk.Label(editor, text="Press:").grid(row=0, column=0, sticky="w", padx=6, pady=4)
        ttk.Combobox(
            editor,
            textvariable=self.press_choice,
            values=list(BUTTONS) + [KEYBOARD_CHOICE],
            state="readonly",
            width=14,
        ).grid(row=0, column=1, sticky="w")
        ttk.Button(editor, text="Record Key", command=self.record_key).grid(row=0, column=2, padx=6)
        ttk.Label(editor, textvariable=self.key_text, width=10).grid(row=0, column=3, sticky="w")

        ttk.Label(editor, text="Every (ms):").grid(row=1, column=0, sticky="w", padx=6, pady=4)
        ttk.Entry(editor, textvariable=self.interval_ms, width=10).grid(row=1, column=1, sticky="w")

        ttk.Label(editor, text="At:").grid(row=2, column=0, sticky="w", padx=6, pady=4)
        ttk.Label(editor, textvariable=self.position_text).grid(row=2, column=1, columnspan=3, sticky="w")
        ttk.Button(editor, text="Pick Location (3s)", command=self.pick_location).grid(
            row=3, column=1, sticky="we", pady=(0, 6)
        )
        ttk.Button(editor, text="Use Live Cursor", command=self.clear_location).grid(
            row=3, column=2, columnspan=2, sticky="we", padx=6, pady=(0, 6)
        )
        ttk.Button(editor, text="Add Input", command=self.add_input).grid(
            row=4, column=0, columnspan=4, sticky="we", padx=6, pady=(0, 6)
        )

        self.tree = ttk.Treeview(
            frame, columns=("press", "interval", "at"), show="headings", height=5
        )
        for col, title, width in (("press", "Press", 110), ("interval", "Every", 80), ("at", "At", 150)):
            self.tree.heading(col, text=title)
            self.tree.column(col, width=width, anchor="w")
        self.tree.grid(row=1, column=0, sticky="we", pady=(8, 4))

        buttons = ttk.Frame(frame)
        buttons.grid(row=2, column=0, sticky="we")
        ttk.Button(buttons, text="Remove Selected", command=self.remove_selected).grid(row=0, column=0)
        ttk.Button(buttons, text="Clear All", command=self.clear_inputs).grid(row=0, column=1, padx=6)

        ttk.Separator(frame).grid(row=3, column=0, sticky="we", pady=8)

        self.toggle_button = ttk.Button(frame, text="Start (F6)", command=self.toggle)
        self.toggle_button.grid(row=4, column=0, sticky="we")

        status = ttk.Frame(frame)
        status.grid(row=5, column=0, sticky="we", pady=(8, 0))
        ttk.Label(status, text="Status:").grid(row=0, column=0, sticky="w")
        ttk.Label(status, textvariable=self.status_text).grid(row=0, column=1, sticky="w", padx=6)

        ttk.Label(
            frame,
            text="F6 starts/stops every input at once, even while another window is focused.\n"
            "With no inputs added, the form above is used as a single input.",
            foreground="gray",
            justify="left",
        ).grid(row=6, column=0, sticky="w", pady=(10, 0))

    def record_key(self):
        self.capturing_key = True
        self.status_text.set("Press any key to record...")

    def pick_location(self):
        def countdown():
            for remaining in range(PICK_DELAY_SECONDS, 0, -1):
                self.status_text.set(f"Capturing position in {remaining}...")
                time.sleep(1)
            self.target_pos = self.mouse_controller.position
            self.position_text.set(f"Fixed at {self.target_pos}")
            self.status_text.set("Stopped")

        threading.Thread(target=countdown, daemon=True).start()

    def clear_location(self):
        self.target_pos = None
        self.position_text.set("Live cursor position")

    def _form_input(self):
        """Current form as an input dict, or None (status explains why)."""
        interval = parse_interval(self.interval_ms.get())
        if interval is None:
            self.status_text.set("Invalid interval - enter a number")
            return None

        choice = self.press_choice.get()
        if choice == KEYBOARD_CHOICE:
            if self.target_key is None:
                self.status_text.set("No key recorded - click Record Key")
                return None
            key = self.target_key
            press = lambda: self.keyboard_controller.tap(key)
            label = f"Key: {key_label(key)}"
        else:
            button = BUTTONS[choice]
            press = lambda: self.mouse_controller.click(button, 1)
            label = f"{choice} click"

        return {"press": press, "interval": interval, "pos": self.target_pos, "label": label}

    def add_input(self):
        item = self._form_input()
        if item is None:
            return
        self.inputs.append(item)
        at = f"{item['pos']}" if item["pos"] else "live cursor"
        self.tree.insert("", "end", values=(item["label"], f"{int(item['interval'] * 1000)} ms", at))
        self.status_text.set("Stopped" if not self.running.is_set() else "Running")

    def remove_selected(self):
        for item_id in self.tree.selection():
            del self.inputs[self.tree.index(item_id)]
            self.tree.delete(item_id)

    def clear_inputs(self):
        self.inputs.clear()
        self.tree.delete(*self.tree.get_children())

    def toggle(self):
        if self.running.is_set():
            self.stop()
        else:
            self.start()

    def start(self):
        items = self.inputs
        if not items:
            single = self._form_input()
            if single is None:
                return
            items = [single]

        self.running.set()
        self.status_text.set(f"Running ({len(items)} input{'s' if len(items) > 1 else ''})")
        self.toggle_button.config(text="Stop (F6)")

        # ponytail: inputs run independently, so two position-locked inputs fight
        # over the cursor. Add a shared lock + per-input position restore if that
        # combination ever needs to work.
        self.threads = [
            threading.Thread(target=self._loop, args=(item,), daemon=True) for item in items
        ]
        for thread in self.threads:
            thread.start()

    def _loop(self, item):
        while self.running.is_set():
            if item["pos"] is not None:
                self.mouse_controller.position = item["pos"]
            item["press"]()
            time.sleep(item["interval"])

    def stop(self):
        self.running.clear()
        self.status_text.set("Stopped")
        self.toggle_button.config(text="Start (F6)")

    def _start_hotkey_listener(self):
        def on_press(key):
            if self.capturing_key:
                self.capturing_key = False
                self.target_key = key
                self.root.after(
                    0, lambda: (self.key_text.set(key_label(key)), self.status_text.set("Stopped"))
                )
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
