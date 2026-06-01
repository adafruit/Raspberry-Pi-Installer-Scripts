"""
Adafruit Raspberry Pi Joy Bonnet Setup Script
(C) Adafruit Industries, Creative Commons 3.0 - Attribution Share Alike

Converted to Python by Melissa LeBlanc-Williams for Adafruit Industries

Target hardware: All Raspberry Pi models (Pi Zero / Zero W /
                Zero 2 W / 3 / 4 / 5 etc.). The Joy Bonnet itself
                is most commonly paired with the Pi Zero series
                (AdaBox 005), but the install script works on any
                Raspberry Pi that can host the bonnet.
Target OS:      Raspberry Pi OS (Bookworm or newer).

Notes on modernization (2026):
  - PEP 668 / Bookworm: Python libraries are installed via apt
    (python3-evdev, python3-smbus) instead of pip, since system pip
    is now externally managed.
  - rc.local is deprecated on Bookworm/Trixie. Autostart is provided
    via a systemd unit (joy-bonnet.service) instead of editing
    /etc/rc.local.
  - The boot partition moved from /boot to /boot/firmware on
    Bookworm. shell.get_boot_config() detects the active path.
  - On Pi 5 the legacy RPi.GPIO library does not support the RP1
    GPIO controller, so we install python3-rpi-lgpio (a drop-in
    replacement) instead of python3-rpi.gpio.
"""

import os

try:
    from adafruit_shell import Shell
except ImportError:
    raise RuntimeError(
        "The library 'adafruit_shell' was not found. To install, try typing: "
        "sudo pip3 install adafruit-python-shell"
    )

shell = Shell()
shell.group = "JOY"

JOY_BONNET_URL = (
    "https://raw.githubusercontent.com/adafruit/Adafruit-Retrogame/master/joyBonnet.py"
)
GPIO_HALT_URL = "https://github.com/adafruit/Adafruit-GPIO-Halt/archive/master.zip"


def write_joy_bonnet_service(boot_dir):
    """Install (or overwrite) the joy-bonnet.service systemd unit."""
    shell.write_text_file(
        "/etc/systemd/system/joy-bonnet.service",
        f"""[Unit]
Description=Adafruit Joy Bonnet keypress daemon
After=multi-user.target

[Service]
Type=simple
WorkingDirectory={boot_dir}
ExecStartPre=/sbin/modprobe uinput
ExecStart=/usr/bin/python3 {boot_dir}/joyBonnet.py
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
    shell.run_command("systemctl enable joy-bonnet.service")


def write_gpio_halt_service(halt_pin):
    """Install (or overwrite) the gpio-halt.service systemd unit."""
    shell.write_text_file(
        "/etc/systemd/system/gpio-halt.service",
        f"""[Unit]
Description=Adafruit GPIO Halt button daemon (BCM GPIO {halt_pin})
After=multi-user.target

[Service]
Type=simple
ExecStart=/usr/local/bin/gpio-halt {halt_pin}
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
    shell.run_command("systemctl enable gpio-halt.service")


def main():
    shell.clear()
    print("""This script installs software for the Adafruit
Joy Bonnet for Raspberry Pi.
Steps include:
- Update package index files (apt-get update).
- Install Python libraries via apt (python3-evdev,
  python3-smbus, and a Pi-model-appropriate GPIO library:
  python3-rpi.gpio on Pi 4 and earlier, python3-rpi-lgpio
  on Pi 5 and newer).
- Install joyBonnet.py in the boot partition and
  configure a systemd unit to auto-start it at boot.
- Enable I2C bus.
- OPTIONAL: disable overscan.
- OPTIONAL: install GPIO-halt utility as a systemd unit.
Run time ~10 minutes. Reboot required.
EXISTING INSTALLATION, IF ANY, WILL BE OVERWRITTEN.
""")
    if not shell.prompt("CONTINUE?", default='n'):
        print("Canceled.")
        shell.exit()
    print("Continuing...")
    disable_overscan = shell.prompt("Disable overscan?", default='n')
    install_halt = shell.prompt("Install GPIO-halt utility?", default='n')
    halt_pin = None
    if install_halt:
        while True:
            halt_pin_input = input("GPIO pin for halt (BCM number): ").strip()
            if halt_pin_input.isdigit() and 0 <= int(halt_pin_input) <= 27:
                halt_pin = int(halt_pin_input)
                break
            print("Please enter a valid BCM GPIO number (0-27).")
    print("\n")
    print(f"Overscan: {'disable' if disable_overscan else 'keep current setting'}.")
    print(f"Install GPIO-halt: {'YES (GPIO%d)' % halt_pin if install_halt else 'NO'}")

    if not shell.prompt("CONTINUE?", default='n'):
        print("Canceled.")
        shell.exit()

    # START INSTALL ------------------------------------------------------------
    boot_config = shell.get_boot_config()
    if boot_config is None:
        shell.bail("Could not find Raspberry Pi boot config (config.txt)")
    boot_dir = os.path.dirname(boot_config)

    print("\nStarting installation...")
    shell.info("Updating package index files...")
    shell.run_command("apt-get update", suppress_message=True)

    shell.info("Installing Python libraries via apt...")
    # On Bookworm+, the system Python is externally managed (PEP 668),
    # so we install via apt. python3-evdev and python3-smbus are both
    # packaged in Bookworm and Trixie.
    #
    # GPIO library choice:
    #   - Pi 5 (and newer) use the RP1 GPIO controller, which the legacy
    #     RPi.GPIO package does not support. python3-rpi-lgpio is a
    #     drop-in replacement that routes the same RPi.GPIO API through
    #     lgpio. It declares Conflicts/Provides against python3-rpi.gpio,
    #     so apt enforces that only one is installed.
    #   - Pi 4 and earlier use python3-rpi.gpio.
    gpio_pkg = "python3-rpi-lgpio" if shell.is_pi5_or_newer() else "python3-rpi.gpio"
    shell.run_command(f"apt-get install -y python3-evdev python3-smbus {gpio_pkg}")

    shell.info(f"Installing joyBonnet.py in {boot_dir}...")
    shell.chdir("/tmp")
    shell.run_command(f"curl -fLO {JOY_BONNET_URL}")
    # Moving between filesystems requires copy-and-delete:
    shell.copy("joyBonnet.py", boot_dir)
    shell.remove("joyBonnet.py")

    if install_halt:
        shell.info("Installing gpio-halt in /usr/local/bin...")
        # Pi OS Lite ships without unzip or a compiler toolchain; pull
        # them in before downloading/building.
        shell.run_command("apt-get install -y unzip build-essential")
        shell.chdir("/tmp")
        shell.run_command(f"curl -fLO {GPIO_HALT_URL}")
        shell.run_command("unzip -u master.zip")
        shell.chdir("Adafruit-GPIO-Halt-master")
        shell.run_command("make")
        shell.move("gpio-halt", "/usr/local/bin")
        shell.chdir("..")
        shell.remove("Adafruit-GPIO-Halt-master")
        shell.remove("master.zip")

    # CONFIG -------------------------------------------------------------------

    shell.info("Configuring system...")

    # Enable I2C using raspi-config
    shell.run_raspi_config("do_i2c 0")

    # Disable overscan compensation (use full screen):
    if disable_overscan:
        shell.run_raspi_config("do_overscan 1")

    # Auto-start joyBonnet.py on boot via systemd
    shell.info("Installing joy-bonnet.service systemd unit...")
    write_joy_bonnet_service(boot_dir)

    if install_halt:
        shell.info("Installing gpio-halt.service systemd unit...")
        write_gpio_halt_service(halt_pin)

    # Add udev rule (will overwrite if present)
    shell.write_text_file(
        "/etc/udev/rules.d/10-retrogame.rules",
        'SUBSYSTEM=="input", ATTRS{name}=="retrogame", ENV{ID_INPUT_KEYBOARD}="1"',
        append=False,
    )

    # Clean up any legacy rc.local autostart lines from older installs.
    # /etc/rc.local is gone on Bookworm/Trixie but may still exist on
    # systems upgraded from Bullseye. Without this, the systemd unit
    # and the rc.local entry would both launch joyBonnet.py and gpio-halt
    # at boot, causing duplicate uinput devices or pin contention.
    # multi_line=True runs the regex against the whole file (DOTALL),
    # so we use [^\n] instead of . to keep matches line-scoped, and
    # consume the trailing newline so no blank line is left behind.
    if shell.exists("/etc/rc.local"):
        shell.pattern_replace(
            "/etc/rc.local", r"[^\n]*joyBonnet\.py[^\n]*\n", multi_line=True
        )
        shell.pattern_replace(
            "/etc/rc.local", r"[^\n]*gpio-halt[^\n]*\n", multi_line=True
        )

    print("\nDONE.\nSettings take effect on next boot.\n")
    shell.prompt_reboot()


if __name__ == "__main__":
    shell.require_root()
    main()
