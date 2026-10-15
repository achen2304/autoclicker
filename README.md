# Autoclicker

A simple Windows autoclicker with a GUI: set an interval, pick what gets pressed
(left/right/middle mouse button or any keyboard key), and an optional fixed screen
position, then toggle on/off with `F6` (works even while another window like Roblox
is focused).

## Setup

```
pip install -r requirements.txt
python main.py
```

## Usage

1. Set the interval in milliseconds and pick what to press. For "Keyboard key",
   click "Record Key" and press the key you want repeated.
2. Either leave it on "live cursor position" (clicks wherever your mouse currently
   is) or click "Pick Location", then within 3 seconds move your mouse to the spot
   you want clicked (e.g. a Roblox button) — it will lock to that screen position.
3. Press `F6` or click "Start" to begin clicking; press `F6` again to stop.

## Notes

- Some games and anti-cheat systems treat autoclickers as macros/cheats, which can
  violate their Terms of Service — check the rules of whatever you're farming
  before relying on this to avoid a ban.
- To make a standalone `.exe` (no Python required to run it), install `pyinstaller`
  and run: `pyinstaller --onefile --windowed main.py`. The executable will be in
  `dist/main.exe`.
