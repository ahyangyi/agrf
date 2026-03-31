from agrf.strings import label_printable


def test_label_printable_basic():
    assert label_printable(b"A\x00 ") == "A0 "


def test_label_printable_mixed():
    assert label_printable(bytes([0x1B, 0x7F, 0x20, 0x41])) == "1B\x7f A"
