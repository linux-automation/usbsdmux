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
    assert captured.err.startswith("usage: usbsdmux"), "Invalid help: does not start with 'usage: usbsdmux'"


def test_help_in_readme(capsys, mocker):
    "test that the help output matches the readme"
    mocker.patch("sys.argv", ["usbsdmux", "-h"])
    with pytest.raises(SystemExit):
        usbsdmux.__main__.main()
    captured = capsys.readouterr()
    assert captured.out.startswith("usage: usbsdmux"), "Invalid help: does not start with 'usage: usbsdmux'"
    assert captured.err == "", f"Execution of 'usbsdmux -h' failed: \n{captured.err}"

    readme_path = os.path.join(os.path.dirname(__file__), "../", "README.rst")
    readme_lines = None

    with open(readme_path) as readme:
        for line in readme.readlines():
            line = line.rstrip()
            if line == "   $ usbsdmux -h":
                readme_lines = []
            elif readme_lines is not None:
                if line and not line.startswith("   "):
                    break
                readme_lines.append(line)

    assert readme_lines is not None, "Bash command not found. Did you include '   $ usbsdmux -h'?"
    assert readme_lines, "No output lines found. Did you indent the output correctly?"

    # remove trailing empty lines
    while readme_lines and not readme_lines[-1]:
        readme_lines.pop()

    output_lines = [f"   {line}".rstrip() for line in captured.out.splitlines()]

    assert output_lines == readme_lines, "Output of 'usbsdmux -h' does not match output in README.rst"
