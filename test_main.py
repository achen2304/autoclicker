from pynput import keyboard

from main import BUTTONS, key_label, parse_interval, release_all


def test():
    assert parse_interval("100") == 0.1
    assert parse_interval("0") == 0.001, "interval floors at 1ms, never 0"
    assert parse_interval("abc") is None
    assert set(BUTTONS) == {"Left", "Right", "Middle"}
    assert key_label(keyboard.Key.f6) == "f6"
    assert key_label(keyboard.KeyCode.from_char("e")) == "e"

    released = []
    def boom():
        raise RuntimeError("controller died")
    release_all([
        {"up": boom},
        {"up": lambda: released.append("second")},
    ])
    assert released == ["second"], "a failed release must not leave later keys stuck down"
    print("ok")


if __name__ == "__main__":
    test()
