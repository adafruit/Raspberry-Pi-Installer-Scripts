"""
Adafruit Raspberry Pi SPI Chip Enable Reassignment Script
(C) Adafruit Industries, Creative Commons 3.0 - Attribution Share Alike
"""

try:
    import click
except ImportError:
    raise RuntimeError("The library 'Click' was not found. To install, try typing: sudo pip3 install --upgrade click")
try:
    from adafruit_shell import Shell
except ImportError:
    raise RuntimeError("The library 'adafruit_shell' was not found. To install, try typing: sudo pip3 install adafruit-python-shell")

shell = Shell()
shell.group="SPI Reassign"

allowed_gpios = (4, 5, 6, 7, 8, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27)
spi0_default_pins = (8, 7)

DISABLE_GPIO_TEXT = "Disabled"

boot_dir = "/boot/firmware"
if not shell.exists(boot_dir) or not shell.isdir(boot_dir):
    boot_dir = "/boot"

"""
For now this will only ask about SPI0, but we can later add SPI1
"""

def valid_pins(ce0_pin, ce1_pin):
    if ce0_pin is None and ce1_pin is not None:
        return False
    if ce0_pin is not None and ce0_pin == ce1_pin:
        return False
    if ce0_pin is not None and int(ce0_pin) not in allowed_gpios:
        return False
    if ce1_pin is not None and int(ce1_pin) not in allowed_gpios:
        return False
    return True

def convert_option(pin):
    if pin == "disabled":
        return None
    return int(pin)

def valid_options(ce0_option, ce1_option):
    if ce0_option is None or ce1_option is None:
        return False
    return valid_pins(convert_option(ce0_option), convert_option(ce1_option))

def disable_spi():
    print("Disabling SPI")
    shell.run_command("sudo raspi-config nonint do_spi 1")

def enable_spi():
    print("Enabling SPI")
    shell.run_command("sudo raspi-config nonint do_spi 0")

def spi_disabled():
    return shell.run_command("sudo raspi-config nonint get_spi", suppress_message=True, return_output=True).strip() == "1"

def remove_custom():
    shell.pattern_replace(f"{boot_dir}/config.txt", 'dtoverlay=spi0-[0-2]cs,cs.*?\n', multi_line=True)

def format_gpio(gpio):
    if gpio is None:
        return DISABLE_GPIO_TEXT
    return f"GPIO {gpio}"

def gpio_options(pool):
    options = []
    for gpio in pool:
        options.append(format_gpio(gpio))
    return options

def write_new_custom(ce0_pin, ce1_pin):
    if (ce0_pin, ce1_pin) != spi0_default_pins:
        overlay_command = "dtoverlay=spi0-2cs"
        if ce0_pin is None and ce1_pin is None:
            overlay_command = "dtoverlay=spi0-0cs"
        elif ce1_pin is None:
            overlay_command = "dtoverlay=spi0-1cs"
        if ce0_pin != spi0_default_pins[0] and ce0_pin is not None:
            overlay_command += ",cs0_pin={}".format(ce0_pin)
        if ce1_pin != spi0_default_pins[1] and ce1_pin is not None:
            overlay_command += ",cs1_pin={}".format(ce1_pin)
        shell.write_text_file(f"{boot_dir}/config.txt", overlay_command + "\n")

@click.command()
@click.option('--ce0', nargs=1, default=None, help="Specify a GPIO for CE0 or 'disabled' to disable", type=str)
@click.option('--ce1', nargs=1, default=None, help="Specify a GPIO for CE1 or 'disabled' to disable", type=str)
@click.option('--reboot', nargs=1, default=None, type=click.Choice(['yes', 'no']), help="Specify whether to reboot after the script is finished")
def main(ce0, ce1, reboot):
    ask_reboot = True
    auto_reboot = False
    if reboot is not None:
        ask_reboot = False
        auto_reboot = reboot.lower() == 'yes'
    if valid_options(ce0, ce1):
        ce0 = convert_option(ce0)
        ce1 = convert_option(ce1)
        remove_custom()
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
    menu_options = [
        "Reassign SPI Chip Enable Pins",
        "Reset to Defaults Pins",
        "Disable SPI",
        "Exit",
    ]

    if spi_disabled():
        menu_options[2] = "Enable SPI"

    shell.info("{} detected.\n".format(pi_model))
    if not shell.is_raspberry_pi():
        shell.bail("Non-Raspberry Pi board detected. This must be run on a Raspberry Pi")
    os_identifier = shell.get_os()
    if os_identifier != "Raspbian":
        shell.bail("Sorry, the OS detected was {}. This script currently only runs on Raspberry Pi OS.".format(os_identifier))
    menu_selection = shell.select_n(
        "Select an option:", menu_options
    )
    if menu_selection == 1:
        while True:
            # Reassign
            gpio_pool = list(allowed_gpios)
            gpio_pool.append(None)
            # Ask for pin for CE0
            ce0_selection = shell.select_n("Select a new GPIO for CE0", gpio_options(gpio_pool))
            ce0_pin = gpio_pool[ce0_selection - 1]
            if ce0_pin is not None:
                gpio_pool.remove(ce0_pin)
                # Ask for pin for CE1
                ce1_selection = shell.select_n("Select a new GPIO for CE1", gpio_options(gpio_pool))
                ce1_pin = gpio_pool[ce1_selection - 1]
            else:
                ce1_pin = None
            if shell.prompt(f"The new settings will be {format_gpio(ce0_pin)} for CE0 and {format_gpio(ce1_pin)} for CE1. Is this correct?"):
                break
        remove_custom()
        write_new_custom(ce0_pin, ce1_pin)
        if spi_disabled():
            enable_spi()
    elif menu_selection == 2:
        # Reset to Defaults
        remove_custom()
    elif menu_selection == 3:
        # Enable/Disable SPI
        if spi_disabled():
            enable_spi()
        else:
            disable_spi()
            remove_custom()
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
