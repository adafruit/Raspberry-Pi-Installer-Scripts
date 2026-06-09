# SPDX-FileCopyrightText: 2024 Melissa LeBlanc-Williams for Adafruit Industries
#
# SPDX-License-Identifier: MIT

"""
Adafruit Retrogame Setup Script

Downloads and installs the retrogame GPIO-to-keypress utility plus one
of several pre-baked configuration files, and sets up a systemd unit
to auto-start retrogame at boot.

Notes on modernization (2026):
  - rc.local is deprecated on Bookworm/Trixie. Autostart uses a
    retrogame.service systemd unit instead of editing /etc/rc.local.
  - The udev rule string is now a plain (non-raw) string so the
    double-quotes inside the rule aren't backslash-escaped, which is
    invalid udev syntax and broke the rule on the previous version.
"""

import os

from adafruit_shell import Shell

shell = Shell()
shell.group = "Retrogame"

RETROGAME_URL = (
    "https://raw.githubusercontent.com/adafruit/Adafruit-Retrogame/master/retrogame"
)
RETROGAME_CFG_BASE = (
    "https://raw.githubusercontent.com/adafruit/Adafruit-Retrogame/master/configs"
)


def write_retrogame_service():
    """Install (or overwrite) the retrogame.service systemd unit."""
    shell.write_text_file(
        "/etc/systemd/system/retrogame.service",
        """[Unit]
Description=Adafruit Retrogame GPIO-to-keypress daemon
After=multi-user.target

[Service]
Type=simple
ExecStart=/usr/local/bin/retrogame
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
    shell.run_command("systemctl enable retrogame.service")


def main():
    shell.clear()
    print("""This script downloads and installs
retrogame, a GPIO-to-keypress utility
for adding buttons and joysticks, plus
one of several configuration files.
Run time <1 minute. Reboot recommended.
""")

    # Grouped by config name and menu label.
    config = {
        "pigrrl2": "PiGRRL 2 controls",
        "pocket": "Pocket PiGRRL",
        "zero": "PiGRRL Zero",
        "super": "Super Game Pi",
        "2button": "Two buttons + joystick",
        "6button": "Six buttons + joystick",
        "bonnet": "Adafruit Arcade Bonnet",
        "cupcade-orig": "Cupcade (gen 1 & 2 only)",
    }

    retrogame_select = shell.select_n(
        "Select configuration:",
        list(config.values()) + ["Quit without installing"],
    )

    if retrogame_select > len(config):
        return
    config_name = list(config.keys())[retrogame_select - 1]

    if shell.exists("/boot/retrogame.cfg"):
        print("/boot/retrogame.cfg already exists.\n"
              "Continuing will overwrite file.\n")
        if not shell.prompt("CONTINUE?", default="n"):
            print("Canceled.")
            shell.exit()

    print("Downloading, installing retrogame...", end="")
    # Download to tmpfile because the daemon might already be running.
    if shell.run_command(f"curl -f -s -o /tmp/retrogame {RETROGAME_URL}"):
        shell.move("/tmp/retrogame", "/usr/local/bin/retrogame")
        os.chmod("/usr/local/bin/retrogame", 0o755)
        print("OK")
    else:
        print("ERROR")

    print("Downloading, installing retrogame.cfg...", end="")
    if shell.run_command(
        f"curl -f -s -o /boot/retrogame.cfg {RETROGAME_CFG_BASE}/retrogame.cfg.{config_name}"
    ):
        print("OK")
    else:
        print("ERROR")

    print("Performing other system configuration...", end="")

    # Add udev rule (will overwrite if present). Plain string, no raw prefix:
    # raw strings keep the backslashes in front of the inner quotes, which is
    # invalid udev syntax and silently breaks the rule.
    shell.write_text_file(
        "/etc/udev/rules.d/10-retrogame.rules",
        'SUBSYSTEM=="input", ATTRS{name}=="retrogame", ENV{ID_INPUT_KEYBOARD}="1"',
        append=False,
    )

    if config_name == "bonnet":
        # Arcade Bonnet uses an MCP23017 over I2C; make sure I2C is on.
        shell.run_raspi_config("do_i2c 0")

    # Auto-start retrogame at boot via systemd unit.
    write_retrogame_service()

    # Clean up any legacy rc.local autostart line from older installs so we
    # don't double-launch retrogame alongside the systemd unit.
    if shell.exists("/etc/rc.local"):
        shell.pattern_replace(
            "/etc/rc.local", r"[^\n]*retrogame[^\n]*\n", multi_line=True
        )

    print("OK")

    shell.prompt_reboot()
    print("Done")


if __name__ == "__main__":
    shell.require_root()
    main()
