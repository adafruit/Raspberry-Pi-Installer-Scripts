"""
Adafruit Raspberry Pi SPI Chip Enable Reassignment Script
(C) Adafruit Industries, Creative Commons 3.0 - Attribution Share Alike
"""

try:
    import click
except ImportError:
    raise RuntimeError("The library 'Click' was not found. To install, try typing: sudo pip3 install Click")
try:
    from adafruit_shell import Shell
except ImportError:
    raise RuntimeError("The library 'adafruit_shell' was not found. To install, try typing: sudo pip3 install adafruit-python-shell")
import os

shell = Shell()
shell.group="SPI Reassign"

allowed_gpios = (4, 5, 6, 7, 8, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27)
spi0_default_pins = (8, 7)

"""
For now this will only ask about SPI0, but we can later add SPI1
"""

def valid_pins(ce0_pin, ce1_pin):
    if ce0_pin is None or ce1_pin is None:
        return False
    if ce0_pin == ce1_pin:
        return False
    if int(ce0_pin) not in allowed_gpios:
        return False
    if int(ce1_pin) not in allowed_gpios:
        return False
    return True

def disable_spi():
    print("Disabling SPI")
    shell.run_command("sudo raspi-config nonint do_spi 1")

def enable_spi():
    print("Enabling SPI")
    shell.run_command("sudo raspi-config nonint do_spi 0")

def remove_custom():
    shell.pattern_replace("/boot/config.txt", 'dtoverlay=spi0-2cs,cs.*?\n', multi_line=True)

def write_new_custom(ce0_pin, ce1_pin):
    if (ce0_pin, ce1_pin) == spi0_default_pins:
        enable_spi()
    else:
        overlay_command = "dtoverlay=spi0-2cs"
        if ce0_pin != spi0_default_pins[0]:
            overlay_command += ",cs0_pin={}".format(ce0_pin)
        if ce1_pin != spi0_default_pins[1]:
            overlay_command += ",cs1_pin={}".format(ce1_pin)
        shell.write_text_file("/boot/config.txt", overlay_command + "\n")

@click.command()
@click.option('--ce0', nargs=1, default=None, help="Specify a GPIO for CE0")
@click.option('--ce1', nargs=1, default=None, help="Specify a GPIO for CE1")
@click.option('--reboot', nargs=1, default=None, type=click.Choice(['yes', 'no']), help="Specify whether to reboot after the script is finished")
def main(ce0, ce1, reboot):
    ask_reboot = True
    auto_reboot = False
    if reboot is not None:
        ask_reboot = False
        auto_reboot = reboot.lower() == 'yes'
    if valid_pins(ce0, ce1):
        remove_custom()
        disable_spi()
        write_new_custom(ce0, ce1)
        if auto_reboot:
            shell.reboot()
        if ask_reboot:
            shell.prompt_reboot()
        exit(0)
    else:
        print("Invalid ce0 or ce1", ce0, ce1)
    #shell.clear()
    # Check Raspberry Pi and Bail
    pi_model = shell.get_board_model()
    print("""This script allows you
to easily reassign the SPI Chip Enable
pins so the OS automatic handling of the
lines doesn't interfere with CircuitPython.
Run time of < 1 minute. Reboot required for
changes to take effect!
""")
    shell.info("{} detected.\n".format(pi_model))
    if not shell.is_raspberry_pi():
        shell.bail("Non-Raspberry Pi board detected. This must be run on a Raspberry Pi")
    os_identifier = shell.get_os()
    if os_identifier != "Raspbian":
        shell.bail("Sorry, the OS detected was {}. This script currently only runs on Raspberry Pi OS.".format(os_identifier))
    menu_selection = shell.select_n(
        "Select an option:", (
            "Reassign SPI Chip Enable Pins",
            "Reset to Defaults Pins",
            "Disable SPI",
            "Exit",
        )
    )
    if menu_selection == 1:
        while True:
            # Reassign
            gpio_pool = list(allowed_gpios)
            # Ask for pin for CE0
            ce0_selection = shell.select_n("Select a new GPIO for CE0", ["GPIO {}".format(x) for x in gpio_pool])
            ce0_pin = gpio_pool[ce0_selection - 1]
            gpio_pool.remove(ce0_pin)
            # Ask for pin for CE1
            ce1_selection = shell.select_n("Select a new GPIO for CE1", ["GPIO {}".format(x) for x in gpio_pool])
            ce1_pin = gpio_pool[ce1_selection - 1]
            if shell.prompt("The new GPIO {} for CE0 and GPIO {} for CE1. Is this correct?".format(ce0_pin, ce1_pin)):
                break
        remove_custom()
        disable_spi()
        write_new_custom(ce0_pin, ce1_pin)
    elif menu_selection == 2:
        # Reset to Defaults
        remove_custom()
        enable_spi()
    elif menu_selection == 3:
        # Disable
        remove_custom()
        disable_spi()
    elif menu_selection == 4:
        # Exit
        shell.exit(0)
    # Done
    print("""DONE.

Settings take effect on next boot.
""")
    if auto_reboot:
        shell.reboot()
    if ask_reboot:
        shell.prompt_reboot()

# Main function
if __name__ == "__main__":
    shell.require_root()
    main()
