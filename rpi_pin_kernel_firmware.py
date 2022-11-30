"""
Adafruit Raspberry Pi Script to Pin a specific version of the rpi kernel and firmware
(C) Adafruit Industries, Creative Commons 3.0 - Attribution Share Alike

Converted to Python by Melissa LeBlanc-Williams for Adafruit Industries
"""

try:
    from adafruit_shell import Shell
except ImportError:
    raise RuntimeError("The library 'adafruit_shell' was not found. To install, try typing: sudo pip3 install adafruit-python-shell")

shell = Shell()
shell.group = 'PINNING'

def main():
    shell.clear()
    # Check Raspberry Pi and Bail
    pi_model = shell.get_board_model()
    print("{} detected.\n".format(pi_model))
    if not shell.is_raspberry_pi():
        shell.bail("Non-Raspberry Pi board detected. This must be run on a Raspberry Pi")
    if shell.get_os() != "Raspbian":
        print("OS Detected:" + shell.get_os())
        shell.bail("Sorry. This script currently only runs on Raspberry Pi OS.")
    if len(shell.args) == 1:
        print("Usage: sudo python3 {} kernel-version\n".format(shell.script()))
        print("e.g., {} 1.20201126-1".format(shell.script()))
        shell.exit(1)
    version = shell.args[1]
    base = "http://archive.raspberrypi.org/debian/pool/main/r/raspberrypi-firmware/"
    packagelist = [
        "libraspberrypi0",
        "libraspberrypi-bin",
        "libraspberrypi-dev",
        "libraspberrypi-doc",
        "raspberrypi-bootloader",
        "raspberrypi-kernel",
        "raspberrypi-kernel-headers"
    ]
    new_packages = []
    for package in packagelist:
        filename = f"{package}_{version}_armhf.deb"
        new_packages.append(filename)
        shell.run_command("wget --continue -O {} {}".format(filename, base + filename))

    shell.run_command("dpkg -i " + " ".join(new_packages))

    for package in packagelist:
        shell.write_text_file("/etc/apt/preferences.d/99-adafruit-pin-kernel", (
            f"Package: {package}\n"
            f"Pin: version {version}\n"
            f"Pin-Priority:999\n\n"
        ))
    shell.prompt_reboot()

# Main function
if __name__ == "__main__":
    shell.require_root()
    main()
