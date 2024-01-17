"""
Adafruit PiTFT MIPI Display Installer Script
(C) Adafruit Industries, Creative Commons 3.0 - Attribution Share Alike

Written by Melissa LeBlanc-Williams for Adafruit Industries
"""

import time
import os
try:
    import click
except ImportError:
    raise RuntimeError("The library 'Click' was not found. To install, try typing: pip3 install Click")
try:
    from adafruit_shell import Shell
except ImportError:
    raise RuntimeError("The library 'adafruit_shell' was not found. To install, try typing: pip3 install adafruit-python-shell")

shell = Shell()
shell.group = 'PITFT-MIPI'

__version__ = "1.0.1"

"""
This is the main configuration. Displays should be placed in the order
they are to appear in the menu.
"""
config = [
    {
        "type": "28r",
        "menulabel": "PiTFT 2.4\", 2.8\" or 3.2\" resistive (240x320)",
        "product": "2.8\" resistive, PID 1601",
        "touchscreen": {
            "identifier": "STMPE Touchscreen Calibration",
            "product": "stmpe",
            "transforms": {
                "0": "0.988809 -0.023645 0.060523 -0.028817 1.003935 0.034176 0 0 1",
                "90": "0.014773 -1.132874 1.033662 1.118701 0.009656 -0.065273 0 0 1",
                "180": "-1.115235 -0.010589 1.057967 -0.005964 -1.107968 1.025780 0 0 1",
                "270": "-0.033192 1.126869 -0.014114 -1.115846 0.006580 1.050030 0 0 1",
            },
            "calibrations": {
                "0": "4232 11 -879396 1 5786 -752768 65536",
                "90": "33 -5782 21364572 4221 35 -1006432 65536",
                "180": "-4273 61 16441290 4 -5772 21627524 65536",
                "270": "-9 5786 -784608 -4302 19 16620508 65536",
            },
            "overlay": "touch-stmpe",
        },
        "mipi_data": {
            "command_bin": "adafruit_ili9341_drm",
            "gpio": "dc-gpio=25",
            "viewport": {
                "90": "width=320,height=240",
                "180": "width=240,height=320",
                "270": "width=320,height=240",
                "0": "width=240,height=320",
            },
        },
        "width": 320,
        "height": 240,
    },
    {
        "type": "22",
        "menulabel": "PiTFT 2.2\" no touch",
        "product": "2.2\" no touch",
        "mipi_data": {
            "command_bin": "adafruit_ili9341_drm",
            "gpio": "dc-gpio=25",
            "viewport": {
                "90": "width=320,height=240",
                "180": "width=240,height=320",
                "270": "width=320,height=240",
                "0": "width=240,height=320",
            },
        },
        "width": 320,
        "height": 240,
    },
    {
        "type": "28c",
        "menulabel": "PiTFT 2.8\" capacitive touch",
        "product": "2.8\" capacitive, PID 1983",
        "touchscreen": {
            "identifier": "FocalTech Touchscreen Calibration",
            "product": "EP0110M09",
            "transforms": {
                "0": "-1 0 1 0 -1 1 0 0 1",
                "90": "0 1 0 -1 0 1 0 0 1",
                "180": "1 0 0 0 1 0 0 0 1",
                "270": "0 -1 1 1 0 0 0 0 1",
            },
            "calibrations": "320 65536 0 -65536 0 15728640 65536",
            "overlay": "touch-ft6236",
        },
        "mipi_data": {
            "command_bin": "adafruit_ili9341_drm",
            "gpio": "dc-gpio=25",
            "viewport": {
                "90": "width=320,height=240",
                "180": "width=240,height=320",
                "270": "width=320,height=240",
                "0": "width=240,height=320",
            },
        },
        "width": 320,
        "height": 240,
    },
    {
        "type": "35r",
        "menulabel": "PiTFT 3.5\" resistive touch",
        "product": "3.5\" Resistive",
        "touchscreen": {
            "identifier": "STMPE Touchscreen Calibration",
            "product": "stmpe",
            "transforms": {
                "0": "-1.098388 0.003455 1.052099 0.005512 -1.093095 1.026309 0 0 1",
                "90": "-0.000087 1.094214 -0.028826 -1.091711 -0.004364 1.057821 0 0 1",
                "180": "1.102807 0.000030 -0.066352 0.001374 1.085417 -0.027208 0 0 1",
                "270": "0.003893 -1.087542 1.025913 1.084281 0.008762 -0.060700 0 0 1",
            },
            "calibrations": {
                "0": "5724 -6 -1330074 26 8427 -1034528 65536",
                "90": "5 8425 -978304 -5747 61 22119468 65536",
                "180": "-5682 -1 22069150 13 -8452 32437698 65536",
                "270": "3 -8466 32440206 5703 -1 -1308696 65536",
            },
            "overlay": "touch-stmpe",
        },
        "mipi_data": {
            "command_bin": "adafruit_hx8357_drm",
            "gpio": "dc-gpio=25",
            "viewport": {
                "90": "width=480,height=320",
                "180": "width=320,height=480",
                "270": "width=480,height=320",
                "0": "width=320,height=480",
            },
        },
        "width": 480,
        "height": 320,
        "x11_scale": 1.5,
    },
    {
        "type": "st7789_240x240",
        "menulabel": "PiTFT Mini 1.3\" or 1.54\" display",
        "product": "1.54\" or 1.3\" no touch",
        "mipi_data": {
            "command_bin": "adafruit_st7789_drm",
            "gpio": "dc-gpio=25,backlight-gpio=22",
            "viewport": {
                "0": "width=240,height=240",
                "90": "width=240,height=240,x-offset=80",
                "180": "width=240,height=240,y-offset=80",
                "270": "width=240,height=240",
            },
        },
        "width": 240,
        "height": 240,
    },
    {
        "type": "st7789_240x320",
        "menulabel": "ST7789V 2.0\" no touch",
        "product": "2.0\" no touch",
        "mipi_data": {
            "command_bin": "adafruit_st7789_drm",
            "gpio": "dc-gpio=25,backlight-gpio=22",
            "viewport": {
                "0": "width=320,height=240",
                "90": "width=240,height=320",
                "180": "width=320,height=240",
                "270": "width=240,height=320",
            },
        },
        "width": 320,
        "height": 240,
    },
    {
        "type": "st7789_240x135",
        "menulabel": "MiniPiTFT 1.14\" display",
        "product": "1.14\" no touch",
        "mipi_data": {
            "command_bin": "adafruit_st7789_drm",
            "gpio": "dc-gpio=25,backlight-gpio=22",
            "viewport": {
                "0": "width=136,height=240,x-offset=52,y-offset=40",
                "90": "width=240,height=136,y-offset=52,x-offset=40",
                "180": "width=136,height=240,x-offset=52,y-offset=40",
                "270": "width=240,height=136,y-offset=52,x-offset=40",
            },
        },
        "width": 240,
        "height": 135,
    },
    {
        "type": "st7789v_bonnet_240x240",
        "menulabel": "TFT 1.3\" Bonnet + Joystick",
        "product": "1.3\" Joystick",
        "mipi_data": {
            "command_bin": "adafruit_st7789_drm",
            "gpio": "dc-gpio=25,backlight-gpio=22",
            "viewport": {
                "0": "width=240,height=240",
                "90": "width=240,height=240,x-offset=80",
                "180": "width=240,height=240,y-offset=80",
                "270": "width=240,height=240",
            },
        },
        "width": 240,
        "height": 240,
    },
]

# default mipi data
mipi_data = {
    "speed": 40000000,
    "spi": "spi0-0",
}

PITFT_ROTATIONS = ("90", "180", "270", "0")
UPDATE_DB = False
SYSTEMD = None
MIPI_MINIMUM_KERNEL = 5.15
pitft_config = None
pitftrot = None
auto_reboot = None

def warn_exit(message):
    shell.warn(message)
    shell.exit(1)

def print_version(ctx, param, value):
    if not value or ctx.resilient_parsing:
       return
    print("Adafruit PiTFT Helper v{}".format(__version__))
    shell.exit(1)

def progress(ellipsis_count):
    for i in range(ellipsis_count):
        print("...", end='')
        time.sleep(1)
    print("")

def sysupdate():
    global UPDATE_DB
    if not UPDATE_DB:
        print("Updating apt indexes...", end='')
        progress(3)
        if not shell.run_command('sudo apt update', suppress_message=True):
            warn_exit("Apt failed to update indexes!")
        if not shell.run_command('sudo apt-get update', suppress_message=True):
            warn_exit("Apt failed to update indexes!")
        print("Reading package lists...")
        progress(3)
        UPDATE_DB = True
    return True

############################ Sub-Scripts ############################

def softwareinstall():
    print("Installing Pre-requisite Software...This may take a few minutes!")
    if not shell.run_command("apt-get install -y libts0", suppress_message=True):
        if not shell.run_command("apt-get install -y tslib"):
            if not shell.run_command("apt-get install -y libts-dev"):
                warn_exit("Apt failed to install TSLIB!")
    if not shell.run_command("apt-get install -y bc fbi git python3-dev python3-pip python3-smbus python3-spidev evtest libts-bin device-tree-compiler libraspberrypi-dev build-essential python3-evdev"):
        warn_exit("Apt failed to install software!")
    return True

def uninstall_bootconfigtxt():
    """Remove any old flexfb/fbtft stuff"""
    if shell.pattern_search(f"{boot_dir}/config.txt", "adafruit-pitft-helper"):
        print(f"Already have an adafruit-pitft-helper section in {boot_dir}/config.txt.")
        print("Removing old section...")
        shell.run_command(f"cp {boot_dir}/config.txt {boot_dir}/configtxt.bak")
        shell.pattern_replace(f"{boot_dir}/config.txt", '\n# --- added by adafruit-pitft-helper.*?\n# --- end adafruit-pitft-helper.*?\n', multi_line=True)
    return True
def update_configtxt():
    f"""update {boot_dir}/config.txt with appropriate values"""
    uninstall_bootconfigtxt()
    # Driver does not work if hdmi_force_hotplug=1 is present
    shell.pattern_replace(f"{boot_dir}/config.txt", "hdmi_force_hotplug=1", "hdmi_force_hotplug=0")
    display_overlay = f"dtoverlay=mipi-dbi-spi,{mipi_data['spi']},speed=40000000"
    display_overlay += f"\ndtparam=compatible={mipi_data['command_bin']}\\0panel-mipi-dbi-spi"
    viewport = ""
    if mipi_data['viewport'][pitftrot] is not None:
        viewport = mipi_data['viewport'][pitftrot]
    display_overlay += f"\ndtparam={viewport}"
    if "gpio" in mipi_data:
        display_overlay += f"\ndtparam={mipi_data['gpio']}"

    # Touch Overlay
    touch_overlay = ""
    if "touchscreen" in pitft_config and "overlay" in pitft_config["touchscreen"]:
        # use dtc to compile and copy overlay
        touch_overlay = pitft_config["touchscreen"]["overlay"]
        shell.run_command(f"dtc -I dts -O dtb -o {boot_dir}/overlays/{touch_overlay}.dtbo overlays/{touch_overlay}.dts")
        touch_overlay = f"\ndtoverlay={touch_overlay}"
    date = shell.date()
    shell.write_text_file(f"{boot_dir}/config.txt", f"""
# --- added by adafruit-pitft-helper {date} ---
[all]
dtparam=spi=on
dtparam=i2c1=on
dtparam=i2c_arm=on

{display_overlay}
{touch_overlay}
# --- end adafruit-pitft-helper {date} ---
""")
    return True

def update_udev():
    shell.write_text_file("/etc/udev/rules.d/95-touchmouse.rules", """
SUBSYSTEM=="input", ATTRS{name}=="touchmouse", ENV{DEVNAME}=="*event*", SYMLINK+="input/touchscreen"
""", append=False)
    shell.write_text_file("/etc/udev/rules.d/95-ftcaptouch.rules", """
SUBSYSTEM=="input", ATTRS{name}=="EP0110M09", ENV{DEVNAME}=="*event*", SYMLINK+="input/touchscreen"
SUBSYSTEM=="input", ATTRS{name}=="generic ft5x06*", ENV{DEVNAME}=="*event*", SYMLINK+="input/touchscreen"
""", append=False)
    shell.write_text_file("/etc/udev/rules.d/95-stmpe.rules", """
SUBSYSTEM=="input", ATTRS{name}=="*stmpe*", ENV{DEVNAME}=="*event*", SYMLINK+="input/touchscreen"
""", append=False)
    return True

def compile_display_fw():
    command_src = "mipi/panel.txt"

    # We could just copy the file to panel.txt, edit that, then remove it after
    shell.copy(f"mipi/{mipi_data['command_bin']}.txt", command_src)

    # Make sure each of the lines with "# rotation" starts with exactly 1 # and no more
    shell.pattern_replace(command_src, "^#*(.*?# rotation.*?$)", "#\\1")
    # Uncomment the one for the rotation we are going for
    shell.pattern_replace(command_src, "^#(.*?# rotation " + pitftrot + ".*?$)", "\\1")
    # Download the mipi-dbi-cmd script if it doesn't exist
    if not shell.exists("mipi-dbi-cmd"):
        shell.run_command("wget https://raw.githubusercontent.com/notro/panel-mipi-dbi/main/mipi-dbi-cmd")
        shell.run_command("chmod +x mipi-dbi-cmd")
    # Run the mipi-dbi-script and output directly to the /lib/firmware folder
    shell.run_command(f"./mipi-dbi-cmd /lib/firmware/{mipi_data['command_bin']}.bin mipi/panel.txt")
    shell.remove(command_src)
    return True

def update_pointercal():
    if "calibrations" in pitft_config["touchscreen"]:
        if isinstance(pitft_config["touchscreen"]["calibrations"], dict):
            shell.write_text_file("/etc/pointercal", pitft_config["touchscreen"]["calibrations"][pitftrot])
        else:
            shell.write_text_file("/etc/pointercal", pitft_config["touchscreen"]["calibrations"])
    return True

def install_mipi():
    global mipi_data

    if "mipi_data" in pitft_config:
        mipi_data.update(pitft_config['mipi_data'])
    if not compile_display_fw():
        shell.bail("Unable to compile MIPI firmware")
    # if there's X11 installed...
    if shell.exists("/etc/lightdm"):
        print("Setting raspi-config to boot to desktop w/o login...")
        shell.run_command("raspi-config nonint do_boot_behaviour B4")

    # Disable overscan compensation (use full screen):
    shell.run_command("raspi-config nonint do_overscan 1")

    if not update_configtxt():
        shell.bail(f"Unable to update {boot_dir}/config.txt")
    return True

def update_xorg():
    if "touchscreen" in pitft_config:
        transform = "Option \"TransformationMatrix\" \"{}\"".format(pitft_config["touchscreen"]["transforms"][pitftrot])
        shell.write_text_file("/usr/share/X11/xorg.conf.d/20-calibration.conf", f"""
Section "InputClass"
        Identifier "{pitft_config["touchscreen"]["identifier"]}"
        MatchProduct "{pitft_config["touchscreen"]["product"]}"
        MatchDevicePath "/dev/input/event*"
        Driver "libinput"
        {transform}
EndSection
""",
        append=False,
    )
    return True

def get_config_types():
    types = []
    for item in config:
        types.append(item["type"])
    return types

def get_config(type):
    for item in config:
        if item["type"] == type:
            return item
    return None

def success():
    global auto_reboot
    shell.info("Success!")
    print("""
Settings take effect on next boot.
""")
    if auto_reboot is None:
        auto_reboot = shell.prompt("REBOOT NOW?", default="y")
    if not auto_reboot:
        print("Exiting without reboot.")
        shell.exit()
    print("Reboot started...")
    shell.reboot()
    shell.exit()

####################################################### MAIN
target_homedir = "/home/pi"
username = os.environ["SUDO_USER"]
user_homedir = os.path.expanduser(f"~{username}")
if shell.isdir(user_homedir):
    target_homedir = user_homedir

boot_dir = "/boot/firmware"
if not shell.exists(boot_dir) or not shell.isdir(boot_dir):
    boot_dir = "/boot"

@click.command()
@click.option('-v', '--version', is_flag=True, callback=print_version, expose_value=False, is_eager=True, help="Print version information")
@click.option('-u', '--user', nargs=1, default=target_homedir, type=str, help="Specify path of primary user's home directory", show_default=True)
@click.option('--display', nargs=1, default=None, help="Specify a display option (1-{}) or type {}".format(len(config), get_config_types()))
@click.option('--rotation', nargs=1, default=None, type=int, help="Specify a rotation option (1-4) or degrees {}".format(tuple(sorted([int(x) for x in PITFT_ROTATIONS]))))
@click.option('--reboot', nargs=1, default=None, type=click.Choice(['yes', 'no']), help="Specify whether to reboot after the script is finished")
@click.option('--boot', nargs=1, default=boot_dir, type=str, help="Specify the boot directory", show_default=True)

def main(user, display, rotation, reboot, boot):
    global target_homedir, pitft_config, pitftrot, auto_reboot, boot_dir
    shell.clear()
    if user != target_homedir:
        target_homedir = user
        print(f"Homedir = {target_homedir}")
    if boot != boot_dir:
        if shell.isdir(boot):
            boot_dir = boot
            print(f"Boot dir = {boot_dir}")
        else:
            print(f"{boot} not found or not a directory. Using {boot_dir} instead.")

    print("""This script downloads and installs
PiTFT Support using userspace touch
controls and a DTO for display drawing.
one of several configuration files.
Run time of up to 5 minutes. Reboot required!
""")
    if reboot is not None:
        auto_reboot = reboot.lower() == 'yes'

    # Check that the user is running the minimum kernel on this device
    if not shell.kernel_minimum(MIPI_MINIMUM_KERNEL):
        shell.warn(f"In order to continue, you will need to update your kernel to a minimum of {MIPI_MINIMUM_KERNEL}. ")
        if shell.get_os() == "Raspbian":
            shell.info("It looks like you are running this on a Raspberry Pi. You can update it to the latest version by running 'sudo rpi-update'.")
            shell.exit()

    if display in [str(x) for x in range(1, len(config) + 1)]:
        pitft_config = config[int(display) - 1]
        print("Display Type: {}".format(pitft_config["menulabel"]))
    elif display in get_config_types():
        pitft_config = get_config(display)
        print("Display Type: {}".format(pitft_config["menulabel"]))
    else:
        # Build menu from config
        selections = []
        for item in config:
            option = "{} ({}x{})".format(item['menulabel'], item['width'], item['height'])
            selections.append(option)
        selections.append("Quit without installing")

        PITFT_SELECT = shell.select_n("Select configuration:", selections)
        if PITFT_SELECT == len(config) + 1:
            shell.exit(1)
        pitft_config = config[PITFT_SELECT - 1]

    if rotation is not None and 1 <= rotation <= 4:
        pitftrot = PITFT_ROTATIONS[rotation - 1]
        print("Rotation: {}".format(pitftrot))
    elif str(rotation) in PITFT_ROTATIONS:
        pitftrot = str(rotation)
        print("Rotation: {}".format(pitftrot))
    else:
        PITFT_ROTATE = shell.select_n(
        "Select rotation:", (
            "90 degrees (landscape)",
            "180 degrees (portrait)",
            "270 degrees (landscape)",
            "0 degrees (portrait)"
        ))
        pitftrot = PITFT_ROTATIONS[PITFT_ROTATE - 1]

    if 'rotations' in pitft_config and isinstance(pitft_config['rotations'], dict) and pitftrot in pitft_config['rotations'] and pitft_config['rotations'][pitftrot] is None:
        shell.bail("""Unfortunately {rotation} degrees for the {display} is not working at this time. Please
restart the script and choose a different orientation.""".format(rotation=pitftrot, display=pitft_config["menulabel"]))

    # check init system (technique borrowed from raspi-config):
    shell.info('Checking init system...')
    if shell.run_command("which systemctl", suppress_message=True) and shell.run_command("systemctl | grep '\-\.mount'", suppress_message=True):
        SYSTEMD = True
        print("Found systemd")
    elif os.path.isfile("/etc/init.d/cron") and not os.path.islink("/etc/init.d/cron"):
        SYSTEMD = False
        print("Found sysvinit")
    else:
        shell.bail("Unrecognised init system")

    if shell.grep("boot", "/proc/mounts"):
        print("/boot is mounted")
    else:
        print("/boot must be mounted. if you think it's not, quit here and try: sudo mount /dev/mmcblk0p1 /boot")
        if shell.prompt("Continue?"):
            print("Proceeding.")
        else:
            shell.bail("Aborting.")

    if not shell.isdir(target_homedir):
        shell.bail("{} must be an existing directory (use -u /home/foo to specify)".format(target_homedir))

    shell.info("System update")
    if not sysupdate():
        shell.bail("Unable to apt-get update")

    shell.info("Installing Python libraries & Software...")
    if not softwareinstall():
        shell.bail("Unable to install software")

    shell.info("Adding MIPI support...")
    if not install_mipi():
        shell.bail("Unable to configure mipi")

    shell.info(f"Updating {boot_dir}/config.txt...")
    if not update_configtxt():
        shell.bail(f"Unable to update {boot_dir}/config.txt")

    if "touchscreen" in pitft_config:
        shell.info("Updating SysFS rules for Touchscreen...")
        if not update_udev():
            shell.bail("Unable to update /etc/udev/rules.d")

        shell.info("Updating TSLib default calibration...")
        if not update_pointercal():
            shell.bail("Unable to update /etc/pointercal")

    if shell.exists("/etc/lightdm"):
        shell.info("Updating X11 default calibration...")
        if not update_xorg():
            shell.bail("Unable to update calibration")
    success()

# Main function
if __name__ == "__main__":
    shell.require_root()
    main()
