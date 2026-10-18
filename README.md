# Autoclicker

A simple Windows autoclicker with a GUI: set an interval, pick what gets pressed
(left/right/middle mouse button or any keyboard key), and an optional fixed screen
position, then toggle on/off with `F6` (works even while another window like Roblox
is focused).

## Download

Grab `Autoclicker.exe` from the [latest release](https://github.com/achen2304/autoclicker/releases/latest)
and run it — no Python needed. Windows SmartScreen may warn about an unsigned exe;
choose "More info" then "Run anyway", or build it yourself (below).

## Setup (from source)

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

## Build a standalone .exe

No Python needed to run the result. From the project root:

```
pip install pyinstaller
pyinstaller --noconfirm Autoclicker.spec
```

The executable lands at `dist/Autoclicker.exe`. `Autoclicker.spec` is the build
config (one-file, no console window); to build without it:

```
pyinstaller --onefile --windowed --name Autoclicker main.py
```

If PyInstaller fails with `WinError 5` on `dist/Autoclicker.exe`, close any running
copy of the app and delete the old exe, then rebuild.

## Notes

- Some games and anti-cheat systems treat autoclickers as macros/cheats, which can
  violate their Terms of Service — check the rules of whatever you're farming
  before relying on this to avoid a ban.
