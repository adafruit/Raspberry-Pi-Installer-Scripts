"""
Adafruit Retrogame Setup Script
(C) Adafruit Industries, Creative Commons 3.0 - Attribution Share Alike

Converted to Python by Melissa LeBlanc-Williams for Adafruit Industries

Note: Currently Untested
"""

try:
    from adafruit_shell import Shell
except ImportError:
    raise RuntimeError("The library 'adafruit_shell' was not found. To install, try typing: sudo pip3 install adafruit-python-shell")
import os

shell = Shell()
shell.group="Retrogame"

def main():
    shell.clear()
    print("""This script downloads and installs
retrogame, a GPIO-to-keypress utility
for adding buttons and joysticks, plus
one of several configuration files.
Run time <1 minute. Reboot recommended.
""")

    # Grouped by config name and menu label
    config = {
        "pigrrl2": "PiGRRL 2 controls",
        "pocket": "Pocket PiGRRL",
        "zero": "PiGRRL Zero",
        "super": "Super Game Pi",
        "2button": "Two buttons + joystick",
        "6button": "Six buttons + joystick",
        "bonnet": "Adafruit Arcade Bonnet",
        "cupcade-orig": "Cupcade (gen 1 & 2 only)"
    }

    RETROGAME_SELECT = shell.select_n(
        "Select configuration:", list(config.values()) + ["Quit without installing"]
    )

    if RETROGAME_SELECT <= len(config):
        CONFIG_NAME = list(config.keys())[RETROGAME_SELECT-1]

        if shell.exists("/boot/retrogame.cfg"):
            print("/boot/retrogame.cfg already exists.\n"
                  "Continuing will overwrite file.\n")
            if not shell.prompt("CONTINUE?", default='n'):
                print("Canceled.")
                shell.exit()

        print("Downloading, installing retrogame...", end="")
        # Download to tmpfile because might already be running
        if shell.run_command("curl -f -s -o /tmp/retrogame https://raw.githubusercontent.com/adafruit/Adafruit-Retrogame/master/retrogame"):
            shell.move("/tmp/retrogame", "/usr/local/bin/")
            os.chmod("/usr/local/bin/retrogame", 0o755)
            print("OK")
        else:
            print("ERROR")

        print("Downloading, installing retrogame.cfg...", end="")
        if shell.run_command(f"curl -f -s -o /boot/retrogame.cfg https://raw.githubusercontent.com/adafruit/Adafruit-Retrogame/master/configs/retrogame.cfg.{CONFIG_NAME}"):
            print("OK")
        else:
            print("ERROR")

        print("Performing other system configuration...", end="")

        # Add udev rule (will overwrite if present)
        shell.write_text_file("/etc/udev/rules.d/10-retrogame.rules", (
            r"SUBSYSTEM==\"input\", ATTRS{name}==\"retrogame\", "
            r"ENV{ID_INPUT_KEYBOARD}=\"1\""
        ))

        if CONFIG_NAME == "bonnet":
            # If Bonnet, make sure I2C is enabled.  Call the I2C
            # setup function in raspi-config (noninteractive):
            shell.run_command("raspi-config nonint do_i2c 0")

        # Start on boot
        if shell.run_command("grep retrogame /etc/rc.local", suppress_message=True):
            # retrogame already in rc.local, but make sure correct:
            shell.pattern_replace("/etc/rc.local", "^.*retrogame.*$", "/usr/local/bin/retrogame &")
        else:
            # Insert retrogame into rc.local before final 'exit 0'
            shell.pattern_replace("/etc/rc.local", "^exit 0", "/usr/local/bin/retrogame &\nexit 0")

        print("OK")

        shell.prompt_reboot()
        print("Done")

# Main function
if __name__ == "__main__":
    shell.require_root()
    main()
