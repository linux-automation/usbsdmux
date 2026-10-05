===============================================================================
                       USB-SD-MUX macOS Driver Extension
===============================================================================

This README documents the macOS emulation layer for the usb-sd-mux utility.
Because macOS handles USB Mass Storage devices and the SCSI architecture
fundamentally differently than Linux, a specialized Bulk-Only Transport (BOT)
user-space pass-through driver was implemented via PyUSB.

-------------------------------------------------------------------------------
1. OPERATIONAL DIFFERENCES & MACOS USAGE
-------------------------------------------------------------------------------

* CLI Argument Substitution (/dev/null):
  Under Linux, the utility operates directly on a SCSI generic character device
  (e.g., `/dev/sg0`). On macOS, this device node does not exist.
  The macOS backend handles hardware discovery automatically via USB Vendor/Product
  IDs (0x0424:0x4041 or 0x0424:0x2642).

  Therefore, pass `/dev/null` as a dummy argument:

  $ sudo usbsdmux /dev/null host
  $ sudo usbsdmux /dev/null dut
  $ sudo usbsdmux /dev/null get

* Root Privileges (sudo):
  To bypass the kernel-level mass storage drivers (`IOUSBMassStorageDriver`)
  and execute low-level USB interface claiming, the tool MUST be run with
  root privileges via `sudo`.

* Dynamic Drive Discovery (Finding the card on macOS):
  Unlike Linux, where partition names are highly predictable (e.g., `/dev/sdX`),
  macOS uses a dynamic disk enumeration system. Whenever the multiplexer
  switches to `host`, a hardware reset is triggered, and the OS dynamically
  assigns a BSD disk identifier.

  To locate the newly mounted µSD card, use the following commands:

  1. Overview of all storage devices:
     $ diskutil list
     (Look for the size matching your µSD card, e.g., /dev/disk4)

  2. Filter explicitly for external physical storage:
     $ diskutil list external physical

  3. Show file system mounting points:
     $ df -h

* Safe Disconnection Warning:
  When switching the multiplexer from `host` to `dut` (or `off`), macOS will
  warn you that the disk was "not ejected properly." This is normal behavior,
  as the relay cuts off power/lines instantly. To prevent file system corruption,
  unmount the card cleanly before switching away from the host:

  $ diskutil eject /dev/diskX  # Replace X with your actual disk number

-------------------------------------------------------------------------------
2. BUILD ENVIRONMENT & DEVELOPMENT SETUP
-------------------------------------------------------------------------------

This tool requires Python 3.10+ and native `libusb` headers. Follow the steps
below based on your preferred package manager.

--- OPTION A: Using MacPorts ---
1. Install Python and libusb:
   $ sudo port install python312 libusb
   $ sudo port select --set python python312

2. Initialize your virtual environment inside the repository:
   $ python -m venv .venv
   $ source .venv/bin/activate

3. Install dependencies and the package in editable/development mode:
   $ pip install --upgrade pip
   $ pip install -e .

4. To ensure the symlink in `/opt/local/bin/` works seamlessly:
   MacPorts uses `/opt/local/bin` as its primary binary path. You can create
   a managed symlink to your script executable so it is available system-wide:

   $ sudo ln -s $(pwd)/.venv/bin/usbsdmux /opt/local/bin/usbsdmux

--- OPTION B: Using Homebrew ---
1. Install Python and libusb:
   $ brew install python@3.12 libusb

2. Initialize your virtual environment inside the repository:
   $ python3.12 -m venv .venv
   $ source .venv/bin/activate

3. Install dependencies and the package:
   $ pip install --upgrade pip
   $ pip install -e .

4. Global execution setup for Homebrew systems:
   Homebrew usually prefixes binaries into `/opt/homebrew/bin` (Apple Silicon)
   or `/usr/local/bin` (Intel). You can symlink the executable into your local
   PATH:

   $ sudo ln -s $(pwd)/.venv/bin/usbsdmux /usr/local/bin/usbsdmux
   # OR for global Apple Silicon custom scripts:
   $ sudo ln -s $(pwd)/.venv/bin/usbsdmux /opt/local/bin/usbsdmux

-------------------------------------------------------------------------------
3. LINUX FILE SYSTEMS ON MACOS (ext4)
-------------------------------------------------------------------------------

By default, macOS cannot natively read or write to Linux file systems like `ext4`.
If your µSD card contains a Linux OS or data partition, it will be recognized on
hardware level, but won't mount in the Finder automatically.

To access `ext4` partitions on macOS:
1. Install macFUSE
2. Install an ext4 compatibility layer such as `ext4fuse` or commercial tools
   like Paragon extFS for Mac.
3. Using a Linux VM (like UTM) and install

If you need full, high-speed WRITE access to ext4 partitions without using
commercial software, the most reliable and secure architectural solution is
leveraging a lightweight Linux Virtual Machine like UTM (https://mac.getutm.app).

Setup Instructions:
1. Download and install UTM (free open-source virtualization engine for macOS).
2. Create a minimal Linux VM (e.g., Ubuntu Server or Debian).
   * Download e.g. Debian (https://www.debian.org/CD/netinst/)
   * On Apple Silicon (M1/M2/M3), choose "Virtualize" -> ARM64 Linux.
   * On Intel Macs, choose "Virtualize" -> x86_64 Linux.
   This runs at near-native CPU speeds with virtually zero overhead.
3. Plug in the USB-SD-Mux FAST and run your command to switch to the host:
   $ sudo usbsdmux /dev/null host
4. In the UTM top toolbar, click the USB icon and select the Microchip bridge
   device (USB2642 USB-to-I2C/SD Reader) to forward it via USB-Passthrough.
5. Inside the Linux VM, the card will instantly appear as a raw storage node
   (e.g., `/dev/vdb` or `/dev/sdb`).
6. The native Linux kernel inside the VM will automatically safely mount the
   ext4 filesystem with full, unrestricted READ and WRITE capabilities.

This completely bypasses macOS OS-level filesystem locks and eliminates any risk
of partition corruption, as data is written by the official Linux ext4 driver.

Final consideration: if you install a Linux VM, you can directly install the
Linux usbsdmux tool there.

-------------------------------------------------------------------------------
4. TROUBLESHOOTING
-------------------------------------------------------------------------------

If you experience persistent `[Errno 32] Pipe error` or timeouts, a prior process
might have left the USB controller engine in an invalid intermediate state.
Simply physically unplug the USB-SD-Mux, wait 2 seconds, and plug it back in
to clear the hardware controller's internal registers.

-------------------------------------------------------------------------------
5. ARCHITECTURE & MACOS SYSTEM LIMITATIONS
-------------------------------------------------------------------------------

* Why we cannot use the native macOS SCSI/Storage Stack:
  Under Linux, the kernel automatically instantiates a generic SCSI device
  (`/dev/sgX`) for the card reader chip, providing a standardized IOCTL
  interface (`SG_IO`) to send raw vendor commands.

  On macOS, this is architecturally impossible for two main reasons:
  1. Strict Kernel Sandboxing: Apple's IOKit and Storage frameworks completely
     lock down Mass Storage devices (`IOStorageFamily`). The OS does not expose
     raw SCSI generic character nodes to user-space applications.
  2. Initial Hardware State: When the usb-sd-mux is plugged in or boots up in
     the initial DUT (Device Under Test) mode, the Microchip bridge controller
     has no physical contact with the µSD card lines. Because the SD card is
     disconnected on hardware level, the macOS kernel fails to enumerate any
     logical LUN or disk geometry. It considers the storage device dead or
     uninitialized, preventing the OS storage stack from creating any access hooks.

* What the implementation does (Linux IOCTL to PyUSB Translation):
  To bypass these operating system limitations, our custom backend acts as a
  lightweight user-space kernel driver emulator:

  1. Low-Level Claiming: It uses PyUSB/libusb to forcefully detach the native
     macOS kernel storage kext (`IOUSBMassStorageDriver`) from the raw USB
     interface and claims the hardware endpoints directly.
  2. BOT Pipeline Emulation: Instead of relying on a file system or SCSI driver,
     the `_call_macos_usb()` function manually reconstructs the official USB
     Mass Storage Class Bulk-Only Transport (BOT) specification. It executes
     the atomic three-phase transaction (CBW -> Data Phase -> CSW) by pushing raw
     bytes directly onto the Bulk endpoints.
  3. Dynamic Linux Replication: It strips the arbitrary 512-byte block padding
     forced by upper Python wrappers for standard disk sectors, dynamically reads
     the exact buffer payloads, handles inline endpoint stalls, and intercepts
     fused status wrappers—effectively mirroring exactly what the Linux `sg`
     kernel driver does when executing a native `ioctl()` system call.

===============================================================================
(created/formulated/translated with AI help)
