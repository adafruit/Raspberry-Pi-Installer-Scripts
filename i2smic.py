try:
    from adafruit_shell import Shell
except ImportError:
    raise RuntimeError("The library 'adafruit_shell' was not found. To install, try typing: sudo pip3 install adafruit-python-shell")

shell = Shell()

def main():
    shell.clear()
    print("""This script downloads and installs
I2S microphone support.
""")
    pimodel_select = shell.select_n("Select Pi Model:", ["Pi 0 or 0W", "Pi 2 or 3", "Pi 4"]) - 1

    auto_load = shell.prompt("Auto load module at boot?")

    print("""
Installing...""")

    # Get needed packages
    shell.run_command("apt-get -y install git raspberrypi-kernel-headers")

    # Clone the repo
    shell.run_command("git clone https://github.com/adafruit/Raspberry-Pi-Installer-Scripts.git")

    # Build and install the module
    shell.chdir("Raspberry-Pi-Installer-Scripts/i2s_mic_module")
    shell.run_command("make clean")
    shell.run_command("make")
    shell.run_command("make install")

    # Setup auto load at boot if selected
    if auto_load:
        shell.write_text_file(
            "/etc/modules-load.d/snd-i2smic-rpi.conf",
            "snd-i2smic-rpi"
        )
        shell.write_text_file(
            "/etc/modules-load.d/snd-i2smic-rpi.conf",
            "options snd-i2smic-rpi rpi_platform_generation={}".format(pimodel_select)
        )

    # Enable I2S overlay
    shell.run_command("sed -i -e 's/#dtparam=i2s/dtparam=i2s/g' /boot/config.txt")

    # Done
    print("""DONE.

Settings take effect on next boot.
""")
    if not shell.prompt("REBOOT NOW?", "n"):
        print("Exiting without reboot.")
        shell.exit()
    print("Reboot started...")
    shell.reboot()
    shell.exit()

# Main function
if __name__ == "__main__":
    shell.require_root()
    main()
