import subprocess
import sys

usbsdmux_help = subprocess.run(["usbsdmux", "-h"], capture_output=True).stdout
usbsdmux_help = usbsdmux_help.decode("utf-8")

# Convert to the indentation we have in the README.rst
usbsdmux_help = "$ usbsdmux -h\n" + usbsdmux_help
usbsdmux_help = "\n".join(("    " + line) if line.strip() != "" else "" for line in usbsdmux_help.split("\n"))

readme_help = open("README.rst").read()

if usbsdmux_help not in readme_help:
    print("The help text in the README.rst is not up to date.")
    print("Update the README.rst with the following content:")
    print("")
    print(".. code-block:: text")
    print("")
    print(usbsdmux_help)

    sys.exit(1)
