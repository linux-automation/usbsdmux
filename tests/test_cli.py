import os

import pytest

import usbsdmux.__main__


def test_usage(capsys, mocker):
    "test that the usage output include the command name"
    mocker.patch("sys.argv", ["usbsdmux"])
    with pytest.raises(SystemExit):
        usbsdmux.__main__.main()
    captured = capsys.readouterr()
    assert captured.out == ""
    assert captured.err.startswith("usage: usbsdmux")


def test_help_in_readme(capsys, mocker):
    "test that the help output matches the readme"
    mocker.patch("sys.argv", ["usbsdmux", "-h"])
    with pytest.raises(SystemExit):
        usbsdmux.__main__.main()
    captured = capsys.readouterr()
    assert captured.out.startswith("usage: usbsdmux")
    assert captured.err == ""

    readme_path = os.path.join(os.path.dirname(__file__), "../", "README.rst")
    readme_lines = None
    for line in open(readme_path).readlines():
        line = line.rstrip()
        if line == "   $ usbsdmux -h":
            readme_lines = []
        elif readme_lines is not None:
            if line and not line.startswith("   "):
                break
            readme_lines.append(line)

    assert readme_lines is not None
    del readme_lines[-1]  # remove trailing empty line

    output_lines = [f"   {line}".rstrip() for line in captured.out.splitlines()]

    assert output_lines == readme_lines
