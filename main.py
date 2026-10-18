import threading
import time
import tkinter as tk
from tkinter import ttk

from pynput import keyboard, mouse

DEFAULT_HOTKEY = keyboard.Key.f6
PICK_DELAY_SECONDS = 3
BUTTONS = {
    "Left": mouse.Button.left,
    "Right": mouse.Button.right,
    "Middle": mouse.Button.middle,
}
KEYBOARD_CHOICE = "Keyboard key"

BG = "#eef1f5"
CARD = "#ffffff"
TEXT = "#15181d"
MUTED = "#6b7280"
LINE = "#d8dde5"
ACCENT = "#2563eb"
ACCENT_DOWN = "#1d4ed8"
DANGER = "#dc2626"
DANGER_DOWN = "#b91c1c"
GREEN = "#16a34a"

FONT = "Segoe UI"


def parse_interval(text):
    """Milliseconds string -> seconds float, or None if unparseable."""
    try:
        return max(1, int(text)) / 1000.0
    except ValueError:
        return None


def key_label(key):
    return getattr(key, "char", None) or key.name


def hotkey_label(key):
    return key_label(key).upper()


def release_all(held):
    """Release every held input, even if one of them throws."""
    for item in held:
        try:
            item["up"]()
        except Exception:
            pass


class AutoClickerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Autoclicker")
        self.root.configure(bg=BG)
        self.root.resizable(False, False)

        self.mouse_controller = mouse.Controller()
        self.keyboard_controller = keyboard.Controller()
        self.running = threading.Event()
        self.inputs = []
        self.held = []

        self.target_pos = None
        self.target_key = None
        self.hotkey = DEFAULT_HOTKEY
        self.capturing_key = False
        self.capturing_hotkey = False
        self.interval_ms = tk.StringVar(value="100")
        self.press_choice = tk.StringVar(value="Left")
        self.mode_choice = tk.StringVar(value="Repeat")
        self.status_text = tk.StringVar(value="Stopped")
        self.position_text = tk.StringVar(value="Live cursor position")
        self.key_text = tk.StringVar(value="no key recorded")
        self.hotkey_text = tk.StringVar(value=hotkey_label(DEFAULT_HOTKEY))
        self.hint_text = tk.StringVar(value="")

        self._build_style()
        self._build_ui()
        self._start_hotkey_listener()
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

    def _build_style(self):
        style = ttk.Style()
        style.theme_use("clam")
        style.configure(".", background=CARD, foreground=TEXT, font=(FONT, 9))
        style.configure("Card.TFrame", background=CARD)
        style.configure("Bg.TFrame", background=BG)
        style.configure("Bg.TLabel", background=BG, foreground=TEXT)
        style.configure("Title.TLabel", background=BG, foreground=TEXT, font=(FONT, 15, "bold"))
        style.configure("Section.TLabel", background=CARD, foreground=TEXT, font=(FONT, 10, "bold"))
        style.configure("Field.TLabel", background=CARD, foreground=MUTED)
        style.configure("Value.TLabel", background=CARD, foreground=TEXT)
        style.configure("Status.TLabel", background=BG, foreground=MUTED, font=(FONT, 9, "bold"))
        style.configure("Hint.TLabel", background=BG, foreground=MUTED, font=(FONT, 8))
        style.configure("Card.TRadiobutton", background=CARD, foreground=TEXT)
        style.map("Card.TRadiobutton", background=[("active", CARD)])
        style.configure("TButton", padding=(10, 5), background="#f1f3f7", borderwidth=1)
        style.map("TButton", background=[("active", "#e2e6ee")])
        style.configure("Add.TButton", padding=(10, 6), font=(FONT, 9, "bold"))
        style.configure(
            "Treeview",
            background=CARD,
            fieldbackground=CARD,
            rowheight=26,
            borderwidth=0,
            font=(FONT, 9),
        )
        style.configure(
            "Treeview.Heading", background="#f1f3f7", foreground=MUTED, font=(FONT, 8, "bold")
        )
        style.map("Treeview", background=[("selected", "#dbe4fb")], foreground=[("selected", TEXT)])
        style.configure("TEntry", fieldbackground=CARD, bordercolor=LINE, padding=4)
        style.configure("TCombobox", fieldbackground=CARD, bordercolor=LINE, padding=3)

    def _card(self, parent, title):
        wrapper = tk.Frame(parent, bg=LINE, padx=1, pady=1)
        card = ttk.Frame(wrapper, style="Card.TFrame", padding=12)
        card.pack(fill="both", expand=True)
        ttk.Label(card, text=title, style="Section.TLabel").grid(
            row=0, column=0, columnspan=4, sticky="w", pady=(0, 8)
        )
        return wrapper, card

    def _build_ui(self):
        outer = ttk.Frame(self.root, style="Bg.TFrame", padding=14)
        outer.grid(row=0, column=0, sticky="nsew")

        header = ttk.Frame(outer, style="Bg.TFrame")
        header.grid(row=0, column=0, sticky="we", pady=(0, 12))
        header.columnconfigure(1, weight=1)
        ttk.Label(header, text="Autoclicker", style="Title.TLabel").grid(row=0, column=0, sticky="w")
        self.status_dot = tk.Label(header, text="●", bg=BG, fg=MUTED, font=(FONT, 11))
        self.status_dot.grid(row=0, column=2, sticky="e")
        ttk.Label(header, textvariable=self.status_text, style="Status.TLabel").grid(
            row=0, column=3, sticky="e", padx=(4, 0)
        )

        wrapper, editor = self._card(outer, "Add an input")
        wrapper.grid(row=1, column=0, sticky="we")

        ttk.Label(editor, text="Action", style="Field.TLabel").grid(row=1, column=0, sticky="w", pady=4)
        ttk.Combobox(
            editor,
            textvariable=self.press_choice,
            values=[f"{name} click" for name in BUTTONS] + [KEYBOARD_CHOICE],
            state="readonly",
            width=16,
        ).grid(row=1, column=1, sticky="w")
        self.record_button = ttk.Button(editor, text="Record Key", command=self.record_key)
        self.record_button.grid(row=1, column=2, sticky="we", padx=(8, 6))
        ttk.Label(editor, textvariable=self.key_text, style="Field.TLabel").grid(
            row=1, column=3, sticky="w"
        )

        ttk.Label(editor, text="Mode", style="Field.TLabel").grid(row=2, column=0, sticky="w", pady=4)
        modes = ttk.Frame(editor, style="Card.TFrame")
        modes.grid(row=2, column=1, columnspan=3, sticky="w")
        ttk.Radiobutton(
            modes,
            text="Repeat every",
            value="Repeat",
            variable=self.mode_choice,
            style="Card.TRadiobutton",
            command=self._sync_mode,
        ).grid(row=0, column=0, sticky="w")
        self.interval_entry = ttk.Entry(modes, textvariable=self.interval_ms, width=7, justify="right")
        self.interval_entry.grid(row=0, column=1, padx=(6, 4))
        ttk.Label(modes, text="ms", style="Field.TLabel").grid(row=0, column=2, sticky="w")
        ttk.Radiobutton(
            modes,
            text="Hold down the whole time",
            value="Hold",
            variable=self.mode_choice,
            style="Card.TRadiobutton",
            command=self._sync_mode,
        ).grid(row=1, column=0, columnspan=3, sticky="w", pady=(4, 0))

        ttk.Label(editor, text="At", style="Field.TLabel").grid(row=3, column=0, sticky="w", pady=4)
        ttk.Label(editor, textvariable=self.position_text, style="Value.TLabel").grid(
            row=3, column=1, columnspan=3, sticky="w"
        )
        self.pick_button = ttk.Button(editor, text="Pick Location", command=self.pick_location)
        self.pick_button.grid(row=4, column=1, sticky="we", pady=(2, 0))
        ttk.Button(editor, text="Use Live Cursor", command=self.clear_location).grid(
            row=4, column=2, columnspan=2, sticky="we", padx=(8, 0), pady=(2, 0)
        )
        ttk.Button(editor, text="+  Add Input", style="Add.TButton", command=self.add_input).grid(
            row=5, column=0, columnspan=4, sticky="we", pady=(12, 0)
        )

        wrapper, listing = self._card(outer, "Inputs")
        wrapper.grid(row=2, column=0, sticky="we", pady=(12, 0))
        self.list_title = listing.grid_slaves(row=0, column=0)[0]

        self.tree = ttk.Treeview(
            listing, columns=("action", "mode", "at"), show="headings", height=5, selectmode="browse"
        )
        for col, title, width in (("action", "ACTION", 130), ("mode", "MODE", 120), ("at", "AT", 150)):
            self.tree.heading(col, text=title)
            self.tree.column(col, width=width, anchor="w")
        self.tree.tag_configure("odd", background="#f7f9fc")
        self.tree.grid(row=1, column=0, columnspan=4, sticky="we")
        self.tree.bind("<Delete>", lambda _event: self.remove_selected())
        self.tree.bind("<Double-1>", lambda _event: self.remove_selected())

        self.empty_label = ttk.Label(
            listing,
            text="No inputs yet — the form above runs as a single input.",
            style="Field.TLabel",
        )
        self.empty_label.grid(row=2, column=0, columnspan=4, sticky="w", pady=(8, 0))

        list_buttons = ttk.Frame(listing, style="Card.TFrame")
        list_buttons.grid(row=3, column=0, columnspan=4, sticky="we", pady=(10, 0))
        ttk.Button(list_buttons, text="Remove Selected", command=self.remove_selected).grid(
            row=0, column=0
        )
        ttk.Button(list_buttons, text="Clear All", command=self.clear_inputs).grid(
            row=0, column=1, padx=8
        )
        ttk.Label(list_buttons, text="Del or double-click removes a row", style="Field.TLabel").grid(
            row=0, column=2, sticky="w", padx=(4, 0)
        )

        hotkey_row = ttk.Frame(outer, style="Bg.TFrame")
        hotkey_row.grid(row=3, column=0, sticky="we", pady=(12, 0))
        ttk.Label(hotkey_row, text="Start/stop hotkey:", style="Bg.TLabel").grid(row=0, column=0)
        ttk.Label(hotkey_row, textvariable=self.hotkey_text, style="Status.TLabel").grid(
            row=0, column=1, padx=(6, 8)
        )
        self.hotkey_button = ttk.Button(hotkey_row, text="Change", command=self.change_hotkey)
        self.hotkey_button.grid(row=0, column=2)

        self.toggle_button = tk.Button(
            outer,
            text=self._toggle_label(),
            command=self.toggle,
            bg=ACCENT,
            fg="white",
            activebackground=ACCENT_DOWN,
            activeforeground="white",
            font=(FONT, 11, "bold"),
            relief="flat",
            bd=0,
            pady=10,
            cursor="hand2",
        )
        self.toggle_button.grid(row=4, column=0, sticky="we", pady=(10, 6))

        self.hotkey_hint = ttk.Label(outer, text="", style="Hint.TLabel")
        self.hotkey_hint.grid(row=5, column=0, sticky="w")
        ttk.Label(outer, textvariable=self.hint_text, style="Hint.TLabel").grid(
            row=6, column=0, sticky="w"
        )
        self._sync_hotkey_labels()

        self._sync_mode()

    def _toggle_label(self):
        action = "STOP" if self.running.is_set() else "START"
        return f"{action}   ({hotkey_label(self.hotkey)})"

    def _sync_hotkey_labels(self):
        name = hotkey_label(self.hotkey)
        self.hotkey_text.set(name)
        self.hotkey_button.config(text="Change")
        self.toggle_button.config(text=self._toggle_label())
        self.hotkey_hint.config(
            text=f"{name} starts and stops everything, even while another window is focused."
        )

    def change_hotkey(self):
        self.capturing_hotkey = True
        self.hotkey_button.config(text="Press a key...")
        self._set_status("Listening for a new hotkey", ACCENT)

    def _sync_mode(self):
        hold = self.mode_choice.get() == "Hold"
        self.interval_entry.config(state="disabled" if hold else "normal")

    def _set_status(self, text, color=MUTED):
        self.status_text.set(text)
        self.status_dot.config(fg=color)

    def _idle_status(self):
        running = self.running.is_set()
        self._set_status("Running" if running else "Stopped", GREEN if running else MUTED)

    def record_key(self):
        self.capturing_key = True
        self.press_choice.set(KEYBOARD_CHOICE)
        self.record_button.config(text="Press a key...")
        self._set_status("Listening for a key", ACCENT)

    def pick_location(self):
        def countdown():
            for remaining in range(PICK_DELAY_SECONDS, 0, -1):
                self.pick_button.config(text=f"Capturing in {remaining}...")
                time.sleep(1)
            self.target_pos = self.mouse_controller.position
            self.position_text.set(f"Fixed at x={self.target_pos[0]}, y={self.target_pos[1]}")
            self.pick_button.config(text="Pick Location")
            self._idle_status()

        self._set_status("Move the mouse to your target", ACCENT)
        threading.Thread(target=countdown, daemon=True).start()

    def clear_location(self):
        self.target_pos = None
        self.position_text.set("Live cursor position")

    def _form_input(self):
        """Current form as an input dict, or None (status explains why)."""
        mode = self.mode_choice.get()
        interval = parse_interval(self.interval_ms.get())
        if mode == "Repeat" and interval is None:
            self._set_status("Interval must be a number", DANGER)
            return None

        choice = self.press_choice.get()
        if choice == KEYBOARD_CHOICE:
            if self.target_key is None:
                self._set_status("Record a key first", DANGER)
                return None
            key = self.target_key
            press = lambda: self.keyboard_controller.tap(key)
            down = lambda: self.keyboard_controller.press(key)
            up = lambda: self.keyboard_controller.release(key)
            label = f"Key {key_label(key)}"
        else:
            button = BUTTONS[choice.removesuffix(" click")]
            press = lambda: self.mouse_controller.click(button, 1)
            down = lambda: self.mouse_controller.press(button)
            up = lambda: self.mouse_controller.release(button)
            label = choice

        return {
            "label": label,
            "mode": mode,
            "interval": interval,
            "pos": self.target_pos,
            "press": press,
            "down": down,
            "up": up,
        }

    def add_input(self):
        item = self._form_input()
        if item is None:
            return
        self.inputs.append(item)
        mode = "held down" if item["mode"] == "Hold" else f"every {int(item['interval'] * 1000)} ms"
        at = (
            f"x={item['pos'][0]}, y={item['pos'][1]}" if item["pos"] else "live cursor"
        )
        tag = "odd" if len(self.inputs) % 2 else "even"
        self.tree.insert("", "end", values=(item["label"], mode, at), tags=(tag,))
        self._refresh_list_state()
        self._idle_status()
        if self.running.is_set():
            self.hint_text.set("Added — restart with F6 to include it.")

    def remove_selected(self):
        for item_id in self.tree.selection():
            del self.inputs[self.tree.index(item_id)]
            self.tree.delete(item_id)
        self._refresh_list_state()

    def clear_inputs(self):
        self.inputs.clear()
        self.tree.delete(*self.tree.get_children())
        self._refresh_list_state()

    def _refresh_list_state(self):
        count = len(self.inputs)
        self.list_title.config(text=f"Inputs ({count})" if count else "Inputs")
        if count:
            self.empty_label.grid_remove()
        else:
            self.empty_label.grid()

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
        self.hint_text.set("")
        self.toggle_button.config(text=self._toggle_label(), bg=DANGER, activebackground=DANGER_DOWN)

        # ponytail: inputs run independently, so two position-locked inputs fight
        # over the cursor. No arbitration by design.
        self.held = [item for item in items if item["mode"] == "Hold"]
        for item in self.held:
            if item["pos"] is not None:
                self.mouse_controller.position = item["pos"]
            item["down"]()

        repeating = [item for item in items if item["mode"] == "Repeat"]
        for item in repeating:
            threading.Thread(target=self._loop, args=(item,), daemon=True).start()

        parts = []
        if repeating:
            parts.append(f"{len(repeating)} repeating")
        if self.held:
            parts.append(f"{len(self.held)} held")
        self._set_status("Running: " + ", ".join(parts), GREEN)

    def _loop(self, item):
        while self.running.is_set():
            if item["pos"] is not None:
                self.mouse_controller.position = item["pos"]
            item["press"]()
            time.sleep(item["interval"])

    def stop(self):
        self.running.clear()
        release_all(self.held)
        self.held = []
        self._set_status("Stopped", MUTED)
        self.toggle_button.config(text=self._toggle_label(), bg=ACCENT, activebackground=ACCENT_DOWN)

    def on_close(self):
        self.stop()
        self.root.destroy()

    def _start_hotkey_listener(self):
        def on_press(key):
            if self.capturing_hotkey:
                self.capturing_hotkey = False
                self.hotkey = key
                self.root.after(0, self._hotkey_recorded)
                return
            if self.capturing_key:
                self.capturing_key = False
                self.target_key = key
                self.root.after(0, self._key_recorded)
                return
            if key == self.hotkey:
                self.root.after(0, self.toggle)

        listener = keyboard.Listener(on_press=on_press)
        listener.daemon = True
        listener.start()

    def _hotkey_recorded(self):
        self._sync_hotkey_labels()
        self._idle_status()

    def _key_recorded(self):
        self.key_text.set(f"recorded: {key_label(self.target_key)}")
        self.record_button.config(text="Record Key")
        self._idle_status()


def main():
    root = tk.Tk()
    AutoClickerApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
