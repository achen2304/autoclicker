# Autoclicker

A Windows autoclicker with a GUI. Build up a list of inputs — mouse clicks or
keyboard keys, each either repeating on its own interval or held down the whole
time — and toggle them all on/off with one hotkey (`F6` by default, rebindable to
any key) that works even while another window like Roblox is focused.

## Download

**[⬇ Download Autoclicker.exe](https://github.com/achen2304/autoclicker/releases/latest/download/Autoclicker.exe)**
— no Python needed, just run it. That link always serves the newest build; all
versions are on the [releases page](https://github.com/achen2304/autoclicker/releases/latest).

Windows SmartScreen may warn about an unsigned exe; choose "More info" then
"Run anyway", or build it yourself (below).

## Setup (from source)

```
pip install -r requirements.txt
python main.py
```

## Usage

1. **Action** — pick a left/right/middle click, or choose "Keyboard key" and click
   "Record Key", then press the key you want.
2. **Mode** — "Repeat every N ms", or "Hold down the whole time" (the key or button
   stays pressed from start until stop, e.g. holding `c` while the rest of the loop
   keeps clicking).
3. **At** — leave it on live cursor position, or click "Pick Location" and move your
   mouse to the target within 3 seconds to lock that screen position.
4. Click **Add Input** and repeat for as many inputs as you want. They all run
   concurrently, each on its own timing. `Del` or double-click removes a row.
5. Press `F6` or **START** to run everything; `F6` again stops and releases any held
   keys. Closing the window also releases them.
6. To use a different hotkey, click **Change** next to "Start/stop hotkey" and press
   the key you want. Pick one that isn't also an input, or you'll trigger both.

With no inputs added, the form itself runs as a single input, so simple one-click
use needs no setup.

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

- Only inputs added *before* you start are included; add one while running and
  tap `F6` twice to pick it up.
- Two inputs both locked to a fixed position will fight over the cursor — mixing one
  position-locked click with keyboard inputs works fine.
- Some games and anti-cheat systems treat autoclickers as macros/cheats, which can
  violate their Terms of Service — check the rules of whatever you're farming
  before relying on this to avoid a ban.
