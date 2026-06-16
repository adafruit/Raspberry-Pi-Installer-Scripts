# SPDX-FileCopyrightText: 2019 Phillip Burgess for Adafruit Industries
#
# SPDX-License-Identifier: MIT

# INSTALLER SCRIPT FOR ADAFRUIT SPECTRO PROJECT

try:
    from adafruit_shell import Shell
except ImportError:
    raise RuntimeError("The library 'adafruit_shell' was not found. To install, try typing: sudo pip3 install adafruit-python-shell")

shell = Shell()
shell.group = "SPECTRO"

MATRIX_WIDTHS = (64, 32)
MATRIX_HEIGHTS = (32, 16)
SIZE_OPTS = (
    f"{MATRIX_WIDTHS[0]} x {MATRIX_HEIGHTS[0]}",
    f"{MATRIX_WIDTHS[1]} x {MATRIX_HEIGHTS[1]}",
)
SLOWDOWN_OPTS = ("0", "1", "2", "3", "4")

SPECTRO_DIR = "/home/pi/Adafruit_Spectro_Pi"


def write_spectro_service():
    """Install (or overwrite) the spectro.service systemd unit.

    /etc/rc.local is deprecated on Bookworm/Trixie, so selector.py is
    auto-started from a systemd unit instead.
    """
    shell.write_text_file(
        "/etc/systemd/system/spectro.service",
        f"""[Unit]
Description=Adafruit Spectro display daemon
After=multi-user.target

[Service]
Type=simple
User=pi
WorkingDirectory={SPECTRO_DIR}
ExecStart=/usr/bin/python3 {SPECTRO_DIR}/selector.py
Restart=on-failure
RestartSec=2
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
""",
        append=False,
    )
    shell.run_command("systemctl daemon-reload")
    shell.run_command("systemctl enable spectro.service")


def main():
    shell.require_root()
    shell.clear()

    print("This script installs software for the Adafruit")
    print("Spectro project for Raspberry Pi.")
    print("Steps include:")
    print("- Update package index files (apt-get update)")
    print("- Install prerequisite software")
    print("- Install Spectro software")
    print("- Configure hardware and boot options")
    print("Run time ~10 minutes.\n")
    print("EXISTING INSTALLATION, IF ANY, WILL BE OVERWRITTEN.")
    print("If you've edited any Spectro-related files, cancel")
    print("the installation and back up those files first.\n")
    if not shell.prompt("CONTINUE?", default="n"):
        print("Canceled.")
        shell.exit()

    # FEATURE PROMPTS ------------------------------------------------------
    # Installation doesn't begin until after all user input is taken.

    print("\nWhat size LED matrix are you using with Spectro?")
    matrix_size = shell.select_n("LED matrix size:", SIZE_OPTS) - 1

    print(
        "\nFaster Pi boards require dialing back GPIO speed\n"
        "to work with the LED matrix. For Raspberry Pi 4,\n"
        "this usually means the max '4' slowdown setting.\n"
        "For Pi 2 or 3, try the '1' or '2' settings. There\n"
        "is no hard-set rule to this, it can vary with\n"
        "matrix and cabling as well. If the Spectro display\n"
        "is glitchy, just re-run this installer, selecting\n"
        "a higher setting until you find a stable value."
    )
    slowdown_gpio = shell.select_n("GPIO slowdown setting:", SLOWDOWN_OPTS) - 1

    enable_mic = shell.prompt(
        "\nOPTIONAL: Enable USB microphone support?", default="n"
    )
    enable_accel = shell.prompt(
        "OPTIONAL: Enable LIS3DH accelerometer support?", default="n"
    )

    # VERIFY SELECTIONS BEFORE CONTINUING ----------------------------------

    print(f"\nLED matrix size: {SIZE_OPTS[matrix_size]}")
    print(f"GPIO slowdown: {SLOWDOWN_OPTS[slowdown_gpio]}")
    print(f"Enable USB microphone support: {'YES' if enable_mic else 'NO'}")
    print(f"Enable LIS3DH support: {'YES' if enable_accel else 'NO'}")
    if not shell.prompt("\nCONTINUE?", default="n"):
        print("Canceled.")
        shell.exit()

    # Check whether RGB matrix library is present. If not, offer to
    # download and run that installer first (then return here).
    print("\nUpdating package index files...")
    shell.run_command("apt-get update")
    shell.run_command("apt-get -qq install python3-pip")
    print("Checking for RGB matrix library...", end="")
    if shell.run_command("pip3 freeze | grep rgbmatrix", suppress_message=True):
        print("OK.")
    else:
        print("not present.")
        print(
            "Would you like to download and install the RGB matrix\n"
            "library (required by Spectro) first? If so, DO NOT REBOOT\n"
            "when prompted. You'll return to this script for more\n"
            "Spectro configuration."
        )
        if shell.prompt("Run RGB matrix installer?", default="n"):
            shell.run_command(
                "wget https://raw.githubusercontent.com/adafruit/"
                "Raspberry-Pi-Installer-Scripts/master/rgb-matrix.sh -O rgb-matrix.sh"
            )
            shell.run_command("bash rgb-matrix.sh")
            print(
                "\nYou are now back in the main Spectro installer script.\n"
                "When prompted about reboot again, now it's OK!"
            )

    # START INSTALL --------------------------------------------------------

    print("\nStarting installation...")

    # Python modules install into the active virtual environment (the guide
    # has the user create and activate an `env` venv first, then run this
    # script with `sudo -E env PATH=$PATH python3 spectro.py`).
    print("Downloading prerequisites...")
    shell.run_command("pip3 install psutil RPi.GPIO")
    shell.run_command("apt-get install -y python3-dev python3-pillow")
    if enable_mic:
        shell.run_command("apt-get install -y python3-pyaudio python3-numpy")
    if enable_accel:
        shell.run_command(
            "pip3 install adafruit-circuitpython-busdevice adafruit-circuitpython-lis3dh"
        )

    print("Downloading Spectro software...")
    shell.run_command(
        "curl -L https://github.com/adafruit/Adafruit_Spectro_Pi/archive/master.zip "
        "-o Adafruit_Spectro_Pi.zip"
    )
    shell.run_command("unzip -q -o Adafruit_Spectro_Pi.zip")
    shell.remove("Adafruit_Spectro_Pi.zip")
    shell.run_command("mv Adafruit_Spectro_Pi-master Adafruit_Spectro_Pi")
    shell.run_command("chown -R pi:pi Adafruit_Spectro_Pi")

    # CONFIG ---------------------------------------------------------------

    print("Configuring system...")

    if enable_mic:
        # Change ALSA settings to allow USB mic use
        shell.pattern_replace(
            "/usr/share/alsa/alsa.conf",
            "^defaults.ctl.card.*0",
            "defaults.ctl.card 1",
        )
        shell.pattern_replace(
            "/usr/share/alsa/alsa.conf",
            "^defaults.pcm.card.*0",
            "defaults.pcm.card 1",
        )

    if enable_accel:
        # Enable I2C for accelerometer
        shell.run_raspi_config("do_i2c 0")

    # Make default GIFs directory
    shell.run_command("mkdir /boot/gifs")

    # Set up LED columns, rows and slowdown in selector.py script
    flags = (
        f'FLAGS = ["--led-cols={MATRIX_WIDTHS[matrix_size]}", '
        f'"--led-rows={MATRIX_HEIGHTS[matrix_size]}", '
        f'"--led-slowdown-gpio={SLOWDOWN_OPTS[slowdown_gpio]}"]'
    )
    shell.pattern_replace("./Adafruit_Spectro_Pi/selector.py", "^FLAGS.*$", flags)

    # Force HDMI out so /dev/fb0 exists
    config = shell.get_boot_config()
    shell.reconfig(config, "^.*hdmi_force_hotplug.*$", "hdmi_force_hotplug=1")

    # Auto-start selector.py on boot via a systemd service
    print("Installing spectro.service systemd unit...")
    write_spectro_service()

    # PROMPT FOR REBOOT ----------------------------------------------------

    print("\nDone.\n")
    print("Settings take effect on next boot.")
    print("For proper clock time, set the time zone with raspi-config.\n")
    shell.prompt_reboot()


# Main function
if __name__ == "__main__":
    main()
