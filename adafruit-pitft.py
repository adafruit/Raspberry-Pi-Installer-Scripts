"""
Adafruit PiTFT Installer Script
(C) Adafruit Industries, Creative Commons 3.0 - Attribution Share Alike

Written in Python by Melissa LeBlanc-Williams for Adafruit Industries
"""

import time
import os
import glob
import re

try:
    import click
except ImportError:
    raise RuntimeError("The library 'Click' was not found. To install, try typing: pip3 install Click")
try:
    from adafruit_shell import Shell
except ImportError:
    raise RuntimeError("The library 'adafruit_shell' was not found. To install, try typing: pip3 install adafruit-python-shell")

shell = Shell()
shell.group = 'PITFT'

__version__ = "4.0.0"

"""
This is the main configuration. Displays should be placed in the order
they are to appear in the menu.

Config Parameters:
REQUIRED fields:
type: Unique identifier for the display type.
menulabel: The label to display in the menu.
product: The product name for the display.
kernel_upgrade: Whether the kernel needs to be upgraded for this display.
overlay: The overlay string to apply for the display.
width: Width of the display in pixels.
height: Height of the display in pixels.

OPTIONAL fields:
touchscreen: Dictionary containing touchscreen settings for displays with touchscreens.
    identifier: Name of the touchscreen calibration.
    product: Product name for the touchscreen.
    transforms: X11 transforms for different rotations.
    overlay_params: Overlay parameters for different rotations.
    calibrations: Calibration data for the touchscreen. Can be overall or per rotation.
overlay_drm_option: Optional parameter to add for DRM support.
overlay_src: Source path for the overlay file (if applicable).
overlay_dest: Destination path for the compiled overlay file (if applicable).
mipi_data (Optional): Dictionary containing MIPI display data.
    command_bin: Name of the command binary for MIPI.
    gpio: GPIO settings for the display.
    viewport: Viewport settings for different rotations.
mirror_rotations: Dictionary mapping pitftrot values to DRM rotation values.
"""

# Touchscreen Products
TS_STMPE = "stmpe"
TS_TSC2007 = "tsc2007"
TS_FOCALTOUCH = "EP0110M09"

config = [
    {
        "type": "24rv2",
        "menulabel": "PiTFT 2.4\" V2 resistive (240x320)",
        "product": "2.4\" V2 resistive",
        "kernel_upgrade": False,
        "overlay_src": "overlays/pitft24v2-tsc2007-overlay.dts",
        "overlay_dest": "{boot_dir}/overlays/pitft24rv2.dtbo",
        "touchscreen": {
            "identifier": "TSC2007 Touchscreen Calibration",
            "product": TS_TSC2007,
            "transforms": {
                "0": "-1 0 1 0 -1 1",
                "90": "0 1 0 -1 0 1",
                "180": "1 0 0 0 1 0",
                "270": "0 -1 1 1 0 0",
            },
        },
        "overlay": "dtoverlay=pitft24rv2,rotate={pitftrot},fps=60",
        "width": 320,
        "height": 240,
    },
    {
        "type": "28r",
        "menulabel": "PiTFT 2.4\", 2.8\" or 3.2\" resistive (240x320)",
        "product": "2.8\" resistive, PID 1601",
        "kernel_upgrade": False,
        "touchscreen": {
            "identifier": "STMPE Touchscreen Calibration",
            "product": TS_STMPE,
            # X11 Transforms
            "transforms": {
                "0": "0.988809 -0.023645 0.060523 -0.028817 1.003935 0.034176 0 0 1",
                "90": "0.014773 -1.132874 1.033662 1.118701 0.009656 -0.065273 0 0 1",
                "180": "-1.115235 -0.010589 1.057967 -0.005964 -1.107968 1.025780 0 0 1",
                "270": "-0.033192 1.126869 -0.014114 -1.115846 0.006580 1.050030 0 0 1",
            },
            "calibrations": {
                "0": "5724 -6 -1330074 26 8427 -1034528 65536",
                "90": "5 8425 -978304 -5747 61 22119468 65536",
                "180": "-5682 -1 22069150 13 -8452 32437698 65536",
                "270": "3 -8466 32440206 5703 -1 -1308696 65536",
            },
            "overlay_params": {
                "0": None,
                "90": "touch-swapxy,touch-invx",
                "180": "touch-invx,touch-invy",
                "270": "touch-swapxy,touch-invy",
            },
        },
        "overlay": "dtoverlay=pitft28-resistive,rotate={pitftrot},speed=64000000,fps=30",
	    "overlay_drm_option": "drm",
        "width": 320,
        "height": 240,
    },
    {
        "type": "22",
        "menulabel": "PiTFT 2.2\" no touch",
        "product": "2.2\" no touch",
        "kernel_upgrade": False,
        "overlay": "dtoverlay=pitft22,rotate={pitftrot},speed=64000000,fps=30",
	    "overlay_drm_option": "drm",
        "width": 320,
        "height": 240,
    },
    {
        "type": "28c",
        "menulabel": "PiTFT 2.8\" capacitive touch",
        "product": "2.8\" capacitive, PID 1983",
        "kernel_upgrade": False,
        "touchscreen": {
            "identifier": "FocalTech Touchscreen Calibration",
            "product": TS_FOCALTOUCH,
            # X11 Transforms
            "transforms": {
                "0": "-1 0 1 0 -1 1 0 0 1",
                "90": "0 1 0 -1 0 1 0 0 1",
                "180": "1 0 0 0 1 0 0 0 1",
                "270": "0 -1 1 1 0 0 0 0 1",
            },
            "overlay_params": {
                "0": "touch-invx,touch-invy",
                "90": "touch-swapxy,touch-invy",
                "180": None,
                "270": "touch-swapxy,touch-invx",
            },
            "calibrations": "320 65536 0 -65536 0 15728640 65536",
        },
        "overlay": "dtoverlay=pitft28-capacitive,rotate={pitftrot},speed=64000000,fps=30",
	    "overlay_drm_option": "drm",
        "width": 320,
        "height": 240,
    },
    {
        "type": "35r",
        "menulabel": "PiTFT 3.5\" resistive touch",
        "product": "3.5\" Resistive",
        "kernel_upgrade": False,
        "touchscreen": {
            "identifier": "STMPE Touchscreen Calibration",
            "product": TS_STMPE,
            # X11 Transforms
            "transforms": {
                "0": "-1.098388 0.003455 1.052099 0.005512 -1.093095 1.026309 0 0 1",
                "90": "-0.000087 1.094214 -0.028826 -1.091711 -0.004364 1.057821 0 0 1",
                "180": "1.102807 0.000030 -0.066352 0.001374 1.085417 -0.027208 0 0 1",
                "270": "0.003893 -1.087542 1.025913 1.084281 0.008762 -0.060700 0 0 1",
            },
            "overlay_params": {
                "0": None,
                "90": "touch-swapxy,touch-invx",
                "180": "touch-invx,touch-invy",
                "270": "touch-swapxy,touch-invy",
            },
        },
        "overlay": "dtoverlay=pitft35-resistive,rotate={pitftrot},speed=20000000,fps=20",
	    "overlay_drm_option": "drm",
        "width": 480,
        "height": 320,
        "display_scale": 1.5,
    },
    {
        "type": "st7789_240x240",
        "menulabel": "PiTFT Mini 1.3\" or 1.54\" display",
        "product": "1.54\" or 1.3\" no touch",
        "kernel_upgrade": True,
        "kernel_module": "fb_st7789v",
        "overlay_src": "overlays/minipitft13-overlay.dts",
        "overlay_dest": "{boot_dir}/overlays/drm-minipitft13.dtbo",
        "overlay": "dtoverlay=drm-minipitft13,rotate={pitftrot},fps=60",
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
        "mirror_rotations": {
            "0": "0",
            "90": "1",
            "180": "2",
            "270": "3",
        },
    },
    {
        "type": "st7789_240x320",
        "menulabel": "ST7789V 2.0\" no touch",
        "product": "2.0\" no touch",
        "kernel_upgrade": True,
        "kernel_module": "fb_st7789v",
        "overlay_src": "overlays/st7789v_240x320-overlay.dts",
        "overlay_dest": "{boot_dir}/overlays/drm-st7789v_240x320.dtbo",
        "overlay": "dtoverlay=drm-st7789v_240x320,rotate={pitftrot},fps=30",
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
        "kernel_upgrade": True,
        "kernel_module": "fb_st7789v",
        "overlay_src": "overlays/minipitft114-overlay.dts",
        "overlay_dest": "{boot_dir}/overlays/drm-minipitft114.dtbo",
        "overlay": "dtoverlay=drm-minipitft114,rotate={pitftrot},fps=60",
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
        "rotations": {
            "0": None,
            "90": "90",
            "180": None,
            "270": "270",
        },
        "width": 240,
        "height": 135,
        "mirror_rotations": {
            "0": "3",
            "90": "2",
            "180": "1",
            "270": "0",
        },
    },
    {
        "type": "st7789v_bonnet_240x240",
        "menulabel": "BrainCraft HAT or 1.3\" TFT Bonnet + Joystick",
        "product": "1.3\" Joystick",
        "kernel_upgrade": True,
        "kernel_module": "fb_st7789v",
        "overlay_src": "overlays/tftbonnet13-overlay.dts",
        "overlay_dest": "{boot_dir}/overlays/drm-tftbonnet13.dtbo",
        "overlay": "dtoverlay=drm-tftbonnet13,rotate={pitftrot},fps=60",
        "mipi_data": {
            "command_bin": "adafruit_st7789_drm",
            "gpio": "dc-gpio=25,backlight-gpio=26",
            "viewport": {
                "0": "width=240,height=240",
                "90": "width=240,height=240,x-offset=80",
                "180": "width=240,height=240,y-offset=80",
                "270": "width=240,height=240",
            },
        },
        "width": 240,
        "height": 240,
        "mirror_rotations": {
            "0": "0",
            "90": "1",
            "180": "2",
            "270": "3",
        },
    },
]

# default rotations
mirror_rotations = {
    "0": "1",
    "90": "0",
    "180": "3",
    "270": "2",
}

# default mipi data
mipi_data = {
    "speed": 40000000,
    "spi": "spi0-0",
}

install_types = {
    "mirror": "Setup PiTFT as desktop display (mirror)",
    "console": "Display console on PiTFT (console)",
    "drivers": "Install Drivers only"
}

PITFT_ROTATIONS = ("90", "180", "270", "0")
UPDATE_DB = False
SYSTEMD = None
REMOVE_KERNEL_PINNING = False
pitft_config = None
pitftrot = None
auto_reboot = None
is_desktop = False
manager = None

def warn_exit(message):
    shell.warn(message)
    shell.exit(1)

def uninstall_cb(ctx, _param, value):
    if not value or ctx.resilient_parsing:
       return
    uninstall()

def print_version_cb(ctx, _param, value):
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
        if not shell.run_command('sudo apt-get update', suppress_message=True):
            warn_exit("Apt failed to update indexes! Try running 'sudo apt-get update' manually.")
        if not shell.run_command('sudo apt-get update', suppress_message=True):
            warn_exit("Apt failed to update indexes! Try running 'sudo apt-get update' manually.")
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
    if not shell.run_command("apt-get install -y raspi-config"):
        warn_exit("Apt failed to install raspi-config!")
    return True

def uninstall_bootconfigtxt():
    """Remove any old flexfb/fbtft stuff"""
    if shell.pattern_search(f"{boot_dir}/config.txt", "adafruit-pitft-helper"):
        print(f"Already have an adafruit-pitft-helper section in {boot_dir}/config.txt.")
        print("Removing old section...")
        shell.run_command(f"cp {boot_dir}/config.txt {boot_dir}/configtxt.bak")
        shell.pattern_replace(f"{boot_dir}/config.txt", '\n# --- added by adafruit-pitft-helper.*?\n# --- end adafruit-pitft-helper.*?\n', multi_line=True)
    return True

def uninstall_etc_modules():
    """Remove any old flexfb/fbtft stuff"""
    shell.run_command('rm -f /etc/modprobe.d/fbtft.conf')
    shell.pattern_replace("/etc/modules", 'spi-bcm2835')
    shell.pattern_replace("/etc/modules", 'flexfb')
    shell.pattern_replace("/etc/modules", 'fbtft_device')
    return True

def use_mipi_driver(config = None):
    """Check if MIPI Overlay is Present"""
    if not config:
        config = pitft_config
    if not "mipi_data" in config:
        return False
    if not shell.exists(f"{boot_dir}/overlays/mipi-dbi-spi.dtbo"):
        return False
    return True

def is_kernel_upgrade_required(config = None):
    """Check if kernel upgrade is required"""
    if not config:
        config = pitft_config
    if not config['kernel_upgrade']:
        return False
    # Only upgrade Kernel if MIPI Driver is not an option
    if use_mipi_driver(config):
        return False

    return True

def install_drivers():
    """Compile display driver and overlay if required"""
    if "overlay_src" in pitft_config and "overlay_dest" in pitft_config:
        print("Compiling Device Tree Overlay")
        destination = pitft_config['overlay_dest'].format(boot_dir=boot_dir)
        shell.run_command("dtc --warning no-unit_address_vs_reg -I dts -O dtb -o {dest} {src}".format(dest=destination, src=pitft_config['overlay_src']))

    if use_mipi_driver():
        mipi_data.update(pitft_config['mipi_data'])
        if not compile_mipi_fw():
            shell.bail("Unable to compile MIPI firmware")

    if is_kernel_upgrade_required():
        print("############# UPGRADING KERNEL ###############")
        print("Updating packages...")
        if not shell.run_command("sudo apt-get update", suppress_message=True):
            warn_exit("Apt failed to update itself!")
        print("Upgrading packages...")
        if not shell.run_command("sudo apt-get -y upgrade"):
            warn_exit("Apt failed to install software!")
        print("Installing Kernel Headers. This may take a few minutes...")
        if not shell.run_command("apt-get install -y raspberrypi-kernel-headers", suppress_message=True):
            warn_exit("Apt failed to install software!")
        # If the kernel was upgraded, a build folder should exist once it has been loaded
        module = pitft_config['kernel_module']
        if not shell.isdir(f"/lib/modules/{shell.release()}/build"):
            warn_exit(f"Kernel headers build folder for {shell.release()}, not found. Please reboot now and re-run script!")
        print("Compiling and installing display driver...")
        shell.pushd("st7789_module")
        if not shell.run_command("make"):
            warn_exit("Apt failed to compile ST7789V drivers!")
        shell.run_command(f"mv /lib/modules/{shell.release()}/kernel/drivers/staging/fbtft/{module}.ko.xz /lib/modules/{shell.release()}/kernel/drivers/staging/fbtft/{module}.BACK.xz")
        shell.run_command(f"xz -v2 {module}.ko")
        shell.run_command(f"mv {module}.ko.xz /lib/modules/{shell.release()}/kernel/drivers/staging/fbtft/{module}.ko.xz")
        shell.popd()
    return True

def update_configtxt(rotation_override=None, tinydrm_install=False):
    """update /boot/firmware/config.txt (or equivalent folder) with appropriate values"""
    uninstall_bootconfigtxt()
    uninstall_etc_modules()
    overlay_key = "overlay"
    overlay = pitft_config[overlay_key]
    if "{pitftrot}" in overlay:
        rotation = str(rotation_override) if rotation_override is not None else pitftrot
        overlay = overlay.format(pitftrot=rotation)
    if use_mipi_driver():
        # Mipi Driver does not work if hdmi_force_hotplug=1 is present
        shell.pattern_replace(f"{boot_dir}/config.txt", "hdmi_force_hotplug=1", "hdmi_force_hotplug=0")
        # Use the MIPI Overlay instead
        overlay = f"dtoverlay=mipi-dbi-spi,{mipi_data['spi']},speed=40000000"
        overlay += f"\ndtparam=compatible={mipi_data['command_bin']}\\0panel-mipi-dbi-spi"
        viewport = ""
        if mipi_data['viewport'][pitftrot] is not None:
            viewport = mipi_data['viewport'][pitftrot]
        overlay += f"\ndtparam={viewport}"
        if "gpio" in mipi_data:
            overlay += f"\ndtparam={mipi_data['gpio']}"

    if tinydrm_install: # Use overlay params for Wayland
        overlay += ",drm"
        if "overlay_params" in pitft_config and pitftrot in pitft_config["overlay_params"] and pitft_config["overlay_params"][pitftrot] is not None:
            overlay += "," + pitft_config["overlay_params"][pitftrot]
    config_text_base = shell.load_template("templates/config_text_base.txt", date=shell.date(), overlay=overlay)
    if config_text_base is None:
        shell.bail("Unable to load config_text_base template!")
    shell.write_text_file(f"{boot_dir}/config.txt", config_text_base)
    return True

def update_udev():
    product = None
    if "touchscreen" in pitft_config and "product" in pitft_config["touchscreen"]:
        product = pitft_config["touchscreen"]["product"]
    shell.write_templated_file("/etc/udev/rules.d/", "templates/95-touchmouse.rules")
    if product == TS_FOCALTOUCH:
        shell.write_templated_file("/etc/udev/rules.d/", "templates/95-ftcaptouch.rules")
    elif product == TS_STMPE:
        shell.write_templated_file("/etc/udev/rules.d/", "templates/95-stmpe.rules")
    elif product == TS_TSC2007:
        calibration_matrix = "0 1 0 -1 0 1"  # Default calibration matrix
        if "transforms" in pitft_config["touchscreen"] and pitftrot in pitft_config["touchscreen"]["transforms"]:
            calibration_matrix = pitft_config["touchscreen"]["transforms"][pitftrot]
        shell.write_templated_file("/etc/udev/rules.d/", "templates/99-tsc2007-touchscreen.rules", calibration_matrix=calibration_matrix)
    shell.write_templated_file("/etc/udev/rules.d/", "templates/99-spi-tft-drm.rules")
    return True

def compile_mipi_fw():
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
    if "touchscreen" in pitft_config and "calibrations" in pitft_config["touchscreen"]:
        if isinstance(pitft_config["touchscreen"]["calibrations"], dict):
            shell.write_text_file("/etc/pointercal", pitft_config["touchscreen"]["calibrations"][pitftrot], append=False)
        else:
            shell.write_text_file("/etc/pointercal", pitft_config["touchscreen"]["calibrations"], append=False)
    else:
        shell.remove("/etc/pointercal")
    return True

def install_console():
    print("Installing console fbcon map helper...")
    shell.write_templated_file("/usr/local/bin/", "templates/con2fbmap-helper.sh")
    shell.chmod("/usr/local/bin/con2fbmap-helper.sh", "+x")

    print("Installing console fbcon map service...")
    shell.write_templated_file("/etc/systemd/system/", "templates/con2fbmap.service")
    shell.run_command("systemctl daemon-reload")
    shell.run_command("systemctl restart con2fbmap.service")

    print("Turning off console blanking")
    # removing old versions
    shell.pattern_replace("/etc/rc.local", '# disable console blanking.*')
    shell.pattern_replace("/etc/rc.local", 'sudo sh -c "TERM=linux setterm -blank.*')

    # adding new version
    shell.pattern_replace("/etc/rc.local", '^exit 0', "# disable console blanking on PiTFT\\nsudo sh -c \"TERM=linux setterm -blank 0 >/dev/tty0\"\\nexit 0")

    # Set the console font to Terminus 6x12
    shell.reconfig("/etc/default/console-setup", "^.*FONTFACE.*$", "FONTFACE=\"Terminus\"")
    shell.reconfig("/etc/default/console-setup", "^.*FONTSIZE.*$", "FONTSIZE=\"6x12\"")

    print("Setting raspi-config to boot to console w/o login...")
    shell.chdir(target_homedir)
    shell.run_command("raspi-config nonint do_boot_behaviour B2")

    # remove fbcp
    shell.pattern_replace("/etc/rc.local", "^.*fbcp.*$")
    return True

def uninstall_console():
    print(f"Removing console fbcon map from {boot_dir}/cmdline.txt")
    shell.pattern_replace(f"{boot_dir}/cmdline.txt", 'rootwait fbcon=map:10 fbcon=font:VGA8x8', 'rootwait')

    if is_desktop:
        print("Restoring Desktop Environment...")
        shell.run_command("apt-get -y install rpd-plym-splash")     # Install Splash Screen
        shell.run_command("raspi-config nonint do_boot_splash 0")   # Enable Splash Screen
        shell.run_command("apt-get -y install raspberrypi-ui-mods") # Reinstall Raspberry Pi OS UI mods
        shell.run_command("raspi-config nonint do_boot_target B2")  # Boot to Desktop

    if shell.exists("/etc/systemd/system/con2fbmap.service"):
        print("Removing console fbcon map service...")
        shell.run_command("systemctl stop con2fbmap.service")
        shell.run_command("systemctl disable con2fbmap.service")
        shell.remove("/etc/systemd/system/con2fbmap.service")

    if shell.exists("/usr/local/bin/con2fbmap-helper.sh"):
        print("Removing console fbcon map helper...")
        shell.remove("/usr/local/bin/con2fbmap-helper.sh")

    if shell.exists("/etc/rc.local"):
        shell.pattern_replace("/etc/rc.local", '^# disable console blanking.*')
        shell.pattern_replace("/etc/rc.local", '^sudo sh -c "TERM=linux.*')
    return True

def install_mirror():
    global mirror_rotations
    print("Installing cmake...")
    if not shell.run_command("apt-get --yes --allow-downgrades --allow-remove-essential --allow-change-held-packages install cmake", suppress_message=True):
        warn_exit("Apt failed to install software!")
    print("Downloading rpi-fbcp...")
    shell.pushd("/tmp")
    shell.run_command("curl -sLO https://github.com/adafruit/rpi-fbcp/archive/master.zip")
    print("Uncompressing rpi-fbcp...")
    shell.run_command("rm -rf /tmp/rpi-fbcp-master")
    if not shell.run_command("unzip master.zip", suppress_message=True):
        warn_exit("Failed to uncompress fbcp!")
    shell.chdir("rpi-fbcp-master")
    shell.run_command("mkdir build")
    shell.chdir("build")
    print("Building rpi-fbcp...")
    shell.write_text_file("../CMakeLists.txt", "\nset (CMAKE_C_FLAGS \"-std=gnu99 ${CMAKE_C_FLAGS}\")")
    if not shell.run_command("cmake ..", suppress_message=True):
        warn_exit("Failed to cmake fbcp!")
    if not shell.run_command("make", suppress_message=True):
        warn_exit("Failed to make fbcp!")
    print("Installing rpi-fbcp...")
    shell.run_command("install fbcp /usr/local/bin/fbcp")
    shell.popd()
    shell.run_command("rm -rf /tmp/rpi-fbcp-master")

    if "mirror_rotations" in pitft_config:
        mirror_rotations = pitft_config['mirror_rotations']

    # Start fbcp in the appropriate place, depending on init system:
    if SYSTEMD:
        # Add fbcp to /etc/rc.local:
        print("We have sysvinit, so add fbcp to /etc/rc.local...")
        if shell.pattern_search("/etc/rc.local", "fbcp"):
            # fbcp already in rc.local, but make sure correct:
            shell.pattern_replace("/etc/rc.local", "^.*fbcp.*$", "/usr/local/bin/fbcp \&")
        else:
            # Insert fbcp into rc.local before final 'exit 0':
            shell.pattern_replace("/etc/rc.local", "^exit 0", "/usr/local/bin/fbcp \&\\nexit 0")
    else:
        # Install fbcp systemd service, first making sure it's not in rc.local:
        uninstall_fbcp_rclocal()
        print("We have systemd, so install fbcp systemd service...")
        if not install_fbcp_service():
            shell.bail("Unable to install fbcp service file")
        shell.run_command("sudo systemctl enable fbcp.service")

    # if desktop environment is installed...
    if is_desktop:
        print("Setting raspi-config to boot to desktop w/o login...")
        shell.run_command("raspi-config nonint do_boot_behaviour B4")

    # Disable overscan compensation (use full screen):
    shell.run_command("raspi-config nonint do_overscan 1")
    # Set up HDMI parameters:
    print("Configuring boot/config.txt for forced HDMI")
    shell.reconfig(f"{boot_dir}/config.txt", "^.*hdmi_force_hotplug.*$", "hdmi_force_hotplug=1")
    shell.reconfig(f"{boot_dir}/config.txt", "^.*hdmi_group.*$", "hdmi_group=2")
    shell.reconfig(f"{boot_dir}/config.txt", "^.*hdmi_mode.*$", "hdmi_mode=87")

    # if using the desktop version, update driver scale...
    scale = 1
    if is_desktop:
        if "display_scale" in pitft_config:
            scale = pitft_config["display_scale"]
        else:
            scale = 2
    WIDTH = int(pitft_config['width'] * scale)
    HEIGHT = int(pitft_config['height'] * scale)

    shell.reconfig(f"{boot_dir}/config.txt", "^.*hdmi_cvt.*$", "hdmi_cvt={} {} 60 1 0 0 0".format(WIDTH, HEIGHT))

    try:
        default_orientation = int(list(mirror_rotations.keys())[list(mirror_rotations.values()).index("0")])
    except ValueError:
        default_orientation = 90

    if mirror_rotations[pitftrot] == "0":
        # dont rotate HDMI on default orientation
        shell.reconfig(f"{boot_dir}/config.txt", "^.*display_hdmi_rotate.*$", "")
    else:
        display_rotate = mirror_rotations[pitftrot]
        shell.reconfig(f"{boot_dir}/config.txt", "^.*display_hdmi_rotate.*$", "display_hdmi_rotate={}".format(display_rotate))
        # Because we rotate HDMI we have to 'unrotate' the TFT by overriding pitftrot!
        if not update_configtxt(rotation=default_orientation):
            shell.bail(f"Unable to update {boot_dir}/config.txt")
    return True

def update_wayland_settings():
    # Set the scale factor for Wayland, which is the reciprocal of the X11 scale factor
    if "display_scale" in pitft_config:
        scale = 1/pitft_config["display_scale"]
    else:
        scale = 0.5 # Default Scale
    device_name = "SPI-1"
    date = shell.date()

    if manager == "wayfire":
        ### WAYFIRE ###
        wayfire_config = f"{target_homedir}/.config/wayfire.ini"
        # Remove any existing settings previously added by this script
        shell.pattern_replace(wayfire_config, '\n# --- added by adafruit-pitft-helper.*?\n# --- end adafruit-pitft-helper.*?\n', multi_line=True)
        shell.write_text_file(wayfire_config, f"""
# --- added by adafruit-pitft-helper {date} ---
[output:{device_name}]
scale = {scale}
# --- end adafruit-pitft-helper {date} ---
""")

    elif manager == "labwc":
        ### LABWC (Using Kanshi) ###
        # See https://man.archlinux.org/man/kanshi.5.en for more information on kanshi config files
        labwc_config = f"{target_homedir}/.config/kanshi/config"

        # If the config file doesn't exist or doesn't contain profile, enumerate the devices and create a new profile
        if not shell.exists(labwc_config) or not shell.pattern_search(labwc_config, "^profile"):
            drm_devices = get_drm_devices(connected_only=True)
            profile_content = "profile {"
            for device in drm_devices:
                device_name = device["name"]
                mode = device["modes"][0]
                device_refresh = "@60.000"
                device_scale = ""
                if device_name == "SPI-1":
                    device_refresh = ""  # For SPI displays, we don't specify refresh rate
                    device_scale = f" scale {scale}"

                profile_content += f"\n\t\toutput {device_name} enable mode {mode}{device_refresh} transform normal{device_scale}"
            profile_content += "\n}\n"
            shell.write_text_file(labwc_config, profile_content, append=True)
        else:
            profiles = shell.pattern_search(labwc_config, r"(profile(?: .*)?) {([\S\s]*?)}", multi_line=True, return_match=True, find_all=True)
            if profiles:
                for profile in profiles:
                    profile_name = profile[0].strip()
                    profile_content = profile[1].strip()
                    # Check if the profile already has an output section for the device
                    if not shell.pattern_search(profile_content, f"(output {device_name}.*)"):
                        # If not, add the output section for the device
                        width, height = pitft_config["width"], pitft_config["height"]
                        new_output_device = f"\t\toutput {device_name} enable mode {width}x{height} transform normal scale {scale}\n"
                        # insert the new output device line into the profile content
                        profile_content += new_output_device
                        # Replace the profile with the updated content
                        shell.pattern_replace(labwc_config, f"^{profile_name} {{([\S\s]*?)}}", f"{profile_name}: {{{profile_content}}}", multi_line=True)

            # Remove scaling from any existing scale settings for the device
            shell.pattern_replace(labwc_config, f"(output {device_name}.*) scale [0-9](?:\.[0-9]+)?(.*)", r"\1\2")
            # Add new scale to the end of the line
            shell.pattern_replace(labwc_config, f"(output {device_name}.*)", r"\1 scale " + f"{scale}")

def install_fbcp_service():
    shell.write_templated_file("/etc/systemd/system/", "templates/fbcp.service")
    return True

def uninstall_fbcp():
    uninstall_fbcp_rclocal()
    # Enable overscan compensation
    if shell.exists("/etc/systemd/system/fbcp.service"):
        shell.run_command("sudo systemctl disable fbcp.service")
    # Set up HDMI parameters:
    shell.run_command("raspi-config nonint do_overscan 0")
    print("Configuring boot/config.txt for default HDMI")
    shell.reconfig(f"{boot_dir}/config.txt", "^.*hdmi_force_hotplug.*$", "hdmi_force_hotplug=0")
    shell.pattern_replace(f"{boot_dir}/config.txt", "^.*#.*dtoverlay=vc4-kms-v3d.*$", "dtoverlay=vc4-kms-v3d")
    shell.pattern_replace(f"{boot_dir}/config.txt", "^.*#.*dtoverlay=vc4-fkms-v3d.*$", "dtoverlay=vc4-fkms-v3d")
    shell.pattern_replace(f"{boot_dir}/config.txt", '^hdmi_group=2.*$')
    shell.pattern_replace(f"{boot_dir}/config.txt", '^hdmi_mode=87.*$')
    shell.pattern_replace(f"{boot_dir}/config.txt", '^hdmi_cvt=.*$')

    return True

def uninstall_fbcp_rclocal():
    """Remove fbcp from /etc/rc.local:"""
    print("Remove fbcp from /etc/rc.local, if it's there...")
    shell.pattern_replace("/etc/rc.local", '^.*fbcp.*$')
    return True

def update_xorg():
    if "touchscreen" in pitft_config:
        transform_setting = pitft_config["touchscreen"]["transforms"][pitftrot]
        transform = f"Option \"TransformationMatrix\" \"{transform_setting}\""
        if shell.exists("/usr/share/X11/xorg.conf.d"):
            shell.write_text_file("/usr/share/X11/xorg.conf.d/20-calibration.conf", """
Section "InputClass"
        Identifier "{identifier}"
        MatchProduct "{product}"
        MatchDevicePath "/dev/input/event*"
        Driver "libinput"
        {transform}
EndSection
""".format(
            identifier=pitft_config["touchscreen"]["identifier"],
            product=pitft_config["touchscreen"]["product"],
            transform=transform
        ),
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

def uninstall():
    shell.info("Uninstalling PiTFT")
    uninstall_bootconfigtxt()
    uninstall_console()
    uninstall_fbcp()
    uninstall_etc_modules()
    success()

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

def get_drm_devices(connected_only=False):
    # get all drm devices from /sys/class/drm e.g. card1-HDMI-A-1, card2-SPI-1, etc.
    devices = []
    for item in glob.glob("/sys/class/drm/card?-*"):
        status = shell.read_text_file(f"{item}/status").strip()
        if connected_only and status != "connected":
            continue
        modes = shell.read_text_file(f"{item}/modes").strip().splitlines()
        # remove duplicate modes
        modes = list(dict.fromkeys(modes))
        info = {
            "name": item.split("-", 1)[1],
            "status": status,
            "modes": modes,
        }
        devices.append(info)
    return devices

####################################################### MAIN
target_homedir = "/home/pi"
username = os.environ["SUDO_USER"]
user_homedir = os.path.expanduser(f"~{username}")
if shell.isdir(user_homedir):
    target_homedir = user_homedir

boot_dir = "/boot/firmware" if shell.isdir("/boot/firmware") else "/boot"

# If neither directory is valid, use shell.get_boot_config()
if not shell.isdir(boot_dir):
    boot_dir = os.path.dirname(shell.get_boot_config())

# Final safeguard: Ensure boot_dir is actually a directory and not a file path
if boot_dir is None or not shell.isdir(boot_dir):
    shell.bail("Unable to find boot directory")

if shell.get_raspbian_version() == "bullseye":
    shell.bail("Bullseye is not supported by this script. Please update to Bookworm first.")

@click.command()
@click.option('-v', '--version', is_flag=True, callback=print_version_cb, expose_value=False, is_eager=True, help="Print version information")
@click.option('-u', '--user', nargs=1, default=target_homedir, type=str, help="Specify path of primary user's home directory", show_default=True)
@click.option('--display', nargs=1, default=None, help="Specify a display option (1-{}) or type {}".format(len(config), get_config_types()))
@click.option('--rotation', nargs=1, default=None, type=int, help="Specify a rotation option (1-4) or degrees {}".format(tuple(sorted([int(x) for x in PITFT_ROTATIONS]))))
@click.option('--install-type', nargs=1, default=None, type=click.Choice(['mirror', 'fbcp', 'console', 'uninstall']), help="Installation Type")
@click.option('--reboot', nargs=1, default=None, type=click.Choice(['yes', 'no']), help="Specify whether to reboot after the script is finished")
@click.option('--boot', nargs=1, default=boot_dir, type=str, help="Specify the boot directory", show_default=True)
def main(user, display, rotation, install_type, reboot, boot):
    global target_homedir, pitft_config, pitftrot, auto_reboot, boot_dir, is_desktop, manager, SYSTEMD
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
    # Check if we are running on a desktop environment or lite
    is_desktop = shell.exists("/etc/lightdm")
    print("Running on a {} environment".format("desktop" if is_desktop else "lite"))
    if is_desktop:
        manager = shell.get_window_manager()
        if manager is None:
            shell.bail("Unable to determine desktop manager. Please run this script in a terminal emulator, not from the desktop environment.")
        print("Desktop manager: {}".format(manager))
    print()

    print("""This script downloads and installs
PiTFT Support using userspace touch
controls and a DTO for display drawing.
one of several configuration files.
Run time of up to 5 minutes. Reboot required!
""")
    if reboot is not None:
        auto_reboot = reboot.lower() == 'yes'

    if install_type == "uninstall":
        uninstall()
    def select_display(config, interactive=False):
        global pitft_config
        pitft_config = config
        print("Display Type: {}".format(pitft_config["menulabel"]))
        if is_kernel_upgrade_required():
            print("WARNING! WILL UPGRADE YOUR KERNEL TO LATEST")

    if display in [str(x) for x in range(1, len(config) + 1)]:
        select_display(config[int(display) - 1])
    elif display in get_config_types():
        select_display(get_config(display))
    else:
        # Build menu from config
        selections = []
        for item in config:
            option = "{} ({}x{})".format(item['menulabel'], item['width'], item['height'])
            if is_kernel_upgrade_required(item):
                option += " - WARNING! WILL UPGRADE YOUR KERNEL TO LATEST"
            selections.append(option)
        selections.append("Uninstall PiTFT")
        selections.append("Quit without installing")

        PITFT_SELECT = shell.select_n("Select configuration:", selections)
        if PITFT_SELECT == len(config) + 2:
            shell.exit(1)
        if PITFT_SELECT == len(config) + 1:
            uninstall()
        select_display(config[PITFT_SELECT - 1], True)

    if rotation is not None and 1 <= rotation <= 4:
        pitftrot = PITFT_ROTATIONS[rotation - 1]
        shell.info("Rotation: {}".format(pitftrot))
    elif str(rotation) in PITFT_ROTATIONS:
        pitftrot = str(rotation)
        shell.info("Rotation: {}".format(pitftrot))
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

    if install_type is None:
        # Show a selection menu for install_types using shell.select_n and setting the selection to the key of install_types
        install_selection = shell.select_n("Select install type:", install_types.values())
        install_type = list(install_types.keys())[install_selection - 1]
    update_wayland_settings()
    if REMOVE_KERNEL_PINNING:
        # Checking if kernel is pinned
        if shell.exists('/etc/apt/preferences.d/99-adafruit-pin-kernel'):
            shell.warn("WARNING! Script detected your system is currently pinned to an older kernel. The pin will be removed and your system will be updated.")
            if not shell.prompt("Continue?"):
                shell.exit()
            shell.remove('/etc/apt/preferences.d/99-adafruit-pin-kernel')

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

    if "overlay_src" in pitft_config and "overlay_dest" in pitft_config:
        shell.info("Installing display drivers and device tree overlay...")
        if not install_drivers():
            shell.bail("Unable to install display drivers")

    shell.info(f"Updating {boot_dir}/config.txt...")
    if not update_configtxt(tinydrm_install=True):
        shell.bail(f"Unable to update {boot_dir}/config.txt")

    if "touchscreen" in pitft_config:
        shell.info("Updating SysFS rules for Touchscreen...")
        if not update_udev():
            shell.bail("Unable to update /etc/udev/rules.d")

        shell.info("Updating TSLib default calibration...")
        if not update_pointercal():
            shell.bail("Unable to update /etc/pointercal")

    # ask for console access
    if install_type == "console":
        shell.info("Updating console to PiTFT...")
        if not uninstall_fbcp():
            shell.bail("Unable to uninstall fbcp")
        if not install_console():
            shell.bail("Unable to configure console")
    else:
        shell.info("Making sure console doesn't use PiTFT")
        if not uninstall_console():
            shell.bail("Unable to uninstall console")

        # With wayland, PiTFT shows up as an additional display rather than a mirror
        if install_type == "mirror":
            if is_desktop:
                shell.info("Updating Wayland desktop settings...")
                update_wayland_settings()
                shell.info("Updating Desktop Touch calibration...")
                if not update_xorg():
                    shell.bail("Unable to update calibration")
        else:
            if not uninstall_fbcp():
                shell.bail("Unable to uninstall fbcp")
    success()

# Main function
if __name__ == "__main__":
    shell.require_root()
    if shell.is_raspberry_pi_os() and shell.is_kernel_userspace_mismatched() and shell.is_pi5_or_newer():
        shell.bail("Unable to proceed on Pi 5 or newer boards with a with a 32-bit OS. Please reinstall with a 64-bit OS.")
    shell.check_kernel_userspace_mismatch()
    main()
