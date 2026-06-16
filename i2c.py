# SPDX-FileCopyrightText: 2016 ladyada for Adafruit Industries
#
# SPDX-License-Identifier: MIT

# INSTALLER SCRIPT TO ENABLE I2C ON A RASPBERRY PI

try:
    from adafruit_shell import Shell
except ImportError:
    raise RuntimeError(
        "The library 'adafruit_shell' was not found. To install, try typing: "
        "sudo pip3 install adafruit-python-shell"
    )

shell = Shell()
shell.group = "I2C"


def main():
    shell.clear()
    print("This script will enable I2C on your Raspberry Pi")
    print("")
    shell.warn("--- Warning ---")
    print("Always be careful when running scripts and commands copied")
    print("from the internet. Ensure they are from a trusted source.")
    print("")

    if not shell.prompt("Do you wish to continue?", default="n"):
        shell.bail("Aborting...")

    print("")
    print("Enabling I2C...")
    # raspi-config performs the device-tree (dtparam=i2c_arm=on) edit and
    # loads the i2c kernel module on the current Raspberry Pi OS.
    shell.run_raspi_config("do_i2c 0")

    # Ensure the i2c-dev character interface is loaded at boot so /dev/i2c-*
    # is available to user-space tools (i2cdetect, Blinka, etc.).
    shell.append_if_missing("/etc/modules", "i2c-dev")
    shell.run_command("modprobe i2c-dev")

    print("")
    shell.info("Enabled")
    print("")
    print("Settings take effect on next boot.")
    print("")
    shell.prompt_reboot()


if __name__ == "__main__":
    shell.require_root()
    main()
