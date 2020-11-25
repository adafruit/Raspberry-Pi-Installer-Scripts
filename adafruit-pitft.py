"""
Adafruit PiTFT Installer Script
(C) Adafruit Industries, Creative Commons 3.0 - Attribution Share Alike
"""

import time
try:
    import click
except ImportError:
    raise RuntimeError("The library 'Click' was not found. To install, try typing: sudo pip3 install Click==7.0")
try:
    from adafruit_shell import Shell
except ImportError:
    raise RuntimeError("The library 'adafruit_shell' was not found. To install, try typing: sudo pip3 install adafruit-python-shell")

shell = Shell()
shell.group = 'PITFT'

__version__ = "3.0.0"

"""
This is the main configuration. Displays should be placed in the order
they are to appear in the menu.
"""
config = [
    {
        "type": "28r",
        "menulabel": "PiTFT 2.4\", 2.8\" or 3.2\" resistive (240x320)",
        "product": "2.8\" resistive, PID 1601",
        "kernel_upgrade": False,
        "touchscreen": {
            "identifier": "STMPE Touchscreen Calibration",
            "product": "stmpe",
            "transforms": {
                "0": "0.988809 -0.023645 0.060523 -0.028817 1.003935 0.034176 0 0 1",
                "90": "0.014773 -1.132874 1.033662 1.118701 0.009656 -0.065273 0 0 1",
                "180": "-1.115235 -0.010589 1.057967 -0.005964 -1.107968 1.025780 0 0 1",
                "270": "-0.033192 1.126869 -0.014114 -1.115846 0.006580 1.050030 0 0 1",
            },
        },
        "overlay": "dtoverlay=pitft28-resistive,rotate={pitftrot},speed=64000000,fps=30",
        "calibrations": {
            "0": "4232 11 -879396 1 5786 -752768 65536",
            "90": "33 -5782 21364572 4221 35 -1006432 65536",
            "180": "-4273 61 16441290 4 -5772 21627524 65536",
            "270": "-9 5786 -784608 -4302 19 16620508 65536",
        },
        "width": 320,
        "height": 240,
    },
    {
        "type": "22",
        "menulabel": "PiTFT 2.2\" no touch",
        "product": "2.2\" no touch",
        "kernel_upgrade": False,
        "touchscreen": False,
        "overlay" : "dtoverlay=pitft22,rotate={pitftrot},speed=64000000,fps=30",
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
            "product": "EP0110M09",
            "transforms": {
                "0": "-1 0 1 0 -1 1 0 0 1",
                "90": "0 1 0 -1 0 1 0 0 1",
                "180": "1 0 0 0 1 0 0 0 1",
                "270": "0 -1 1 1 0 0 0 0 1",
            },
        },
        "overlay": """dtoverlay=pitft28-capacitive,speed=64000000,fps=30
dtoverlay=pitft28-capacitive,{rotation}""",
        "calibrations": "320 65536 0 -65536 0 15728640 65536",
        "rotations": {
            "0": "rotate=90,touch-invx=true,touch-invy=true",
            "90": "rotate=90,touch-swapxy=true,touch-invx=true",
            "180": "rotate=90",
            "270": "rotate=270,touch-swapxy=true,touch-invy=true",
        },
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
            "product": "stmpe",
            "transforms": {
                "0": "-1.098388 0.003455 1.052099 0.005512 -1.093095 1.026309 0 0 1",
                "90": "-0.000087 1.094214 -0.028826 -1.091711 -0.004364 1.057821 0 0 1",
                "180": "1.102807 0.000030 -0.066352 0.001374 1.085417 -0.027208 0 0 1",
                "270": "0.003893 -1.087542 1.025913 1.084281 0.008762 -0.060700 0 0 1",
            },
        },
        "overlay": "dtoverlay=pitft35-resistive,rotate={pitftrot},speed=20000000,fps=20",
        "calibrations": {
            "0": "5724 -6 -1330074 26 8427 -1034528 65536",
            "90": "5 8425 -978304 -5747 61 22119468 65536",
            "180": "-5682 -1 22069150 13 -8452 32437698 65536",
            "270": "3 -8466 32440206 5703 -1 -1308696 65536",
        },
        "width": 480,
        "height": 320,
        "x11_scale": 1.5,
    },
    {
        "type": "st7789_240x240",
        "menulabel": "PiTFT Mini 1.3\" or 1.54\" display",
        "product": "1.54\" or 1.3\" no touch",
        "kernel_upgrade": True,
        "overlay_src": "overlays/minipitft13-overlay.dts",
        "overlay_dest": "/boot/overlays/drm-minipitft13.dtbo",
        "overlay": "dtoverlay=drm-minipitft13,rotation={pitftrot}",
        "width": 240,
        "height": 240,
    },
    {
        "type": "st7789_240x320",
        "menulabel": "ST7789V 2.0\" no touch",
        "product": "2.0\" no touch",
        "kernel_upgrade": True,
        "overlay_src": "overlays/st7789v_240x320-overlay.dts",
        "overlay_dest": "/boot/overlays/drm-st7789v_240x320.dtbo",
        "overlay": "dtoverlay=drm-st7789v_240x320,rotate={pitftrot}",
        "width": 320,
        "height": 240,
        "rotate": False,
    },
    {
        "type": "st7789_240x135",
        "menulabel": "MiniPiTFT 1.14\" display",
        "product": "1.14\" no touch",
        "kernel_upgrade": True,
        "overlay_src": "overlays/minipitft114-overlay.dts",
        "overlay_dest": "/boot/overlays/drm-minipitft114.dtbo",
        "overlay": "dtoverlay=drm-minipitft114,rotation={pitftrot}",
        "width": 240,
        "height": 135,
    },
]

PITFT_ROTATIONS = ("90", "180", "270", "0")
UPDATE_DB = False
SYSTEMD = None
pitft_config = None
pitftrot = None
auto_reboot = None

def warn_exit(message):
    shell.warn(message)
    shell.exit(1)

def uninstall_cb(ctx, param, value):
    if not value or ctx.resilient_parsing:
       return
    uninstall()

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
        if not shell.run_command('sudo apt update', True):
            warn_exit("Apt failed to update indexes!")
        if not shell.run_command('sudo apt-get update', True):
            warn_exit("Apt failed to update indexes!")
        print("Reading package lists...")
        progress(3)
        UPDATE_DB = True
    return True

############################ Sub-Scripts ############################

def softwareinstall():
    print("Installing Pre-requisite Software...This may take a few minutes!")
    if not shell.run_command("apt-get install -y libts0", True):
        if not shell.run_command("apt-get install -y tslib"):
            warn_exit("Apt failed to install TSLIB!")
    if not shell.run_command("apt-get install -y bc fbi git python-dev python-pip python-smbus python-spidev evtest libts-bin device-tree-compiler"):
        warn_exit("Apt failed to install software!")
    if not shell.run_command("pip3 install evdev"):
        warn_exit("Pip failed to install software!")
    return True

def uninstall_bootconfigtxt():
    """Remove any old flexfb/fbtft stuff"""
    if shell.pattern_search("/boot/config.txt", "adafruit-pitft-helper"):
        print("Already have an adafruit-pitft-helper section in /boot/config.txt.")
        print("Removing old section...")
        shell.run_command("cp /boot/config.txt /boot/configtxt.bak")
        shell.pattern_replace("/boot/config.txt", '\n# --- added by adafruit-pitft-helper.*?\n# --- end adafruit-pitft-helper.*?\n', multi_line=True)
    return True

def uninstall_etc_modules():
    """Remove any old flexfb/fbtft stuff"""
    shell.run_command('rm -f /etc/modprobe.d/fbtft.conf')
    shell.pattern_replace("/etc/modules", 'spi-bcm2835')
    shell.pattern_replace("/etc/modules", 'flexfb')
    shell.pattern_replace("/etc/modules", 'fbtft_device')
    return True

def update_configtxt(rotation_override=None):
    """update /boot/config.txt with appropriate values"""
    uninstall_bootconfigtxt()
    uninstall_etc_modules()
    overlay = pitft_config['overlay']
    if "{pitftrot}" in overlay:
        rotation = str(rotation_override) if rotation_override is not None else pitftrot
        overlay = overlay.format(pitftrot=rotation)
    if "{rotation}" in overlay and isinstance(pitft_config['rotations'], dict):
        overlay = overlay.format(rotation=pitft_config['rotations'][pitftrot])
    if "overlay_src" in pitft_config and "overlay_dest" in pitft_config:
        shell.run_command("dtc -@ -I dts -O dtb -o {dest} {src}".format(dest=pitft_config['overlay_dest'], src=pitft_config['overlay_src']))

        print("############# UPGRADING KERNEL ###############")
        print("Updating packages...")
        if not shell.run_command("sudo apt-get update", True):
            warn_exit("Apt failed to update itself!")
        print("Upgrading packages...")
        if not shell.run_command("sudo apt-get -y upgrade", False):
            warn_exit("Apt failed to install software!")
        print("Installing Kernel Headers...")
        if not shell.run_command("apt-get install -y raspberrypi-kernel-headers", True):
            warn_exit("Apt failed to install software!")
        if not shell.isdir("/lib/modules/{}/build".format(shell.release())):
            warn_exit("Kernel was updated, please reboot now and re-run script!")
        shell.pushd("st7789_module")
        if not shell.run_command("make -C /lib/modules/$(uname -r)/build M=$(pwd) modules"):
            warn_exit("Apt failed to compile ST7789V drivers!")
        shell.run_command("mv /lib/modules/{rel}/kernel/drivers/gpu/drm/tiny/mi0283qt.ko /lib/modules/{rel}/kernel/drivers/gpu/drm/tiny/mi0283qt.BACK".format(rel=shell.release()))
        shell.run_command("mv /lib/modules/{rel}/kernel/drivers/staging/fbtft/fb_st7789v.ko /lib/modules/{rel}/kernel/drivers/gpu/drm/tiny/mi0283qt.BACK".format(rel=shell.release()))
        shell.run_command("mv st7789v_ada.ko /lib/modules/{rel}/kernel/drivers/gpu/drm/tiny/mi0283qt.ko".format(rel=shell.release()))
        shell.run_command("mv fb_st7789v.ko /lib/modules/{rel}/kernel/drivers/staging/fbtft/fb_st7789v.ko".format(rel=shell.release()))
        shell.popd()

    shell.write_text_file("/boot/config.txt", """
# --- added by adafruit-pitft-helper {date} ---
hdmi_force_hotplug=1  # required for cases when HDMI is not plugged in!
dtparam=spi=on
dtparam=i2c1=on
dtparam=i2c_arm=on
{overlay}
# --- end adafruit-pitft-helper {date} ---
""".format(date=shell.date(), overlay=overlay))
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

def update_pointercal():
    if "calibrations" in pitft_config:
        if isinstance(pitft_config["calibrations"], dict):
            shell.write_text_file("/etc/pointercal", pitft_config["calibrations"][pitftrot])
        else:
            shell.write_text_file("/etc/pointercal", pitft_config["calibrations"])
    return True

def install_console():
    print("Set up main console turn on")
    if not shell.pattern_search("/boot/cmdline.txt", 'fbcon=map:10 fbcon=font:VGA8x8'):
        print("Updating /boot/cmdline.txt")
        shell.pattern_replace("/boot/cmdline.txt", "rootwait", "rootwait fbcon=map:10 fbcon=font:VGA8x8")
    else:
        print("/boot/cmdline.txt already updated")

    print("Turning off console blanking")

    # pre-stretch this is what you'd do:
    if shell.exists("/etc/kbd/config"):
        shell.pattern_replace("/etc/kbd/config", "BLANK_TIME=.*", "BLANK_TIME=0")

    # as of stretch....
    # removing any old version
    shell.pattern_replace("/etc/rc.local", '# disable console blanking.*')
    shell.pattern_replace("/etc/rc.local", 'sudo sh -c "TERM=linux setterm -blank.*')
    shell.pattern_replace("/etc/rc.local", '^exit 0', "# disable console blanking on PiTFT\\nsudo sh -c \"TERM=linux setterm -blank 0 >/dev/tty0\"\\nexit 0")

    shell.reconfig("/etc/default/console-setup", "^.*FONTFACE.*$", "FONTFACE=\"Terminus\"")
    shell.reconfig("/etc/default/console-setup", "^.*FONTSIZE.*$", "FONTSIZE=\"6x12\"")

    print("Setting raspi-config to boot to console w/o login...")
    shell.chdir(target_homedir)
    shell.run_command("raspi-config nonint do_boot_behaviour B2")

    # remove fbcp
    shell.pattern_replace("/etc/rc.local", "^.*fbcp.*$")
    return True

def uninstall_console():
    print("Removing console fbcon map from /boot/cmdline.txt")
    shell.pattern_replace("/boot/cmdline.txt", 'rootwait fbcon=map:10 fbcon=font:VGA8x8', 'rootwait')
    print("Screen blanking time reset to 10 minutes")
    if shell.exists("/etc/kbd/config"):
        shell.pattern_replace("/boot/cmdline.txt", 'BLANK_TIME=0', 'BLANK_TIME=10')
    shell.pattern_replace("/etc/rc.local", '^# disable console blanking.*')
    shell.pattern_replace("/etc/rc.local", '^sudo sh -c "TERM=linux.*')
    return True

def install_fbcp():
    print("Installing cmake...")
    if not shell.run_command("apt-get --yes --allow-downgrades --allow-remove-essential --allow-change-held-packages install cmake", True):
        warn_exit("Apt failed to install software!")
    print("Downloading rpi-fbcp...")
    shell.pushd("/tmp")
    shell.run_command("curl -sLO https://github.com/adafruit/rpi-fbcp/archive/master.zip")
    print("Uncompressing rpi-fbcp...")
    shell.run_command("rm -rf /tmp/rpi-fbcp-master")
    if not shell.run_command("unzip master.zip", True):
        warn_exit("Failed to uncompress fbcp!")
    shell.chdir("rpi-fbcp-master")
    shell.run_command("mkdir build")
    shell.chdir("build")
    print("Building rpi-fbcp...")
    shell.write_text_file("../CMakeLists.txt", "\nset (CMAKE_C_FLAGS \"-std=gnu99 ${CMAKE_C_FLAGS}\")")
    if not shell.run_command("cmake ..", True):
        warn_exit("Failed to cmake fbcp!")
    if not shell.run_command("make", True):
        warn_exit("Failed to make fbcp!")
    print("Installing rpi-fbcp...")
    shell.run_command("install fbcp /usr/local/bin/fbcp")
    shell.popd()
    shell.run_command("rm -rf /tmp/rpi-fbcp-master")

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
        # Install fbcp systemd unit, first making sure it's not in rc.local:
        uninstall_fbcp_rclocal()
        print("We have systemd, so install fbcp systemd unit...")
        if not install_fbcp_unit():
            shell.bail("Unable to install fbcp unit file")
        shell.run_command("sudo systemctl enable fbcp.service")

    # if there's X11 installed...
    if shell.exists("/etc/lightdm"):
        print("Setting raspi-config to boot to desktop w/o login...")
        shell.run_command("raspi-config nonint do_boot_behaviour B4")

    # Disable overscan compensation (use full screen):
    shell.run_command("raspi-config nonint do_overscan 1")
    # Set up HDMI parameters:
    print("Configuring boot/config.txt for forced HDMI")
    shell.reconfig("/boot/config.txt", "^.*hdmi_force_hotplug.*$", "hdmi_force_hotplug=1")
    shell.reconfig("/boot/config.txt", "^.*hdmi_group.*$", "hdmi_group=2")
    shell.reconfig("/boot/config.txt", "^.*hdmi_mode.*$", "hdmi_mode=87")
    shell.pattern_replace("/boot/config.txt", "^[^#]*dtoverlay=vc4-fkms-v3d.*$", "#dtoverlay=vc4-fkms-v3d")

    # if there's X11 installed...
    scale = 1
    if shell.exists("/etc/lightdm"):
        if "x11_scale" in pitft_config:
            scale = pitft_config["x11_scale"]
        else:
            scale = 2
    WIDTH = int(pitft_config['width'] * scale)
    HEIGHT = int(pitft_config['height'] * scale)

    shell.reconfig("/boot/config.txt", "^.*hdmi_cvt.*$", "hdmi_cvt={} {} 60 1 0 0 0".format(WIDTH, HEIGHT))

    if pitftrot == "90" or pitftrot == "270" or ("rotate" in pitft_config and not pitft_config['rotate']):
        # dont rotate HDMI on 90 or 270
        shell.reconfig("/boot/config.txt", "^.*display_hdmi_rotate.*$", "")

    if pitftrot in ("0", "180"):
        display_rotate = "3" if pitftrot == "180" else "1"
        shell.reconfig("/boot/config.txt", "^.*display_hdmi_rotate.*$", "display_hdmi_rotate={}".format(display_rotate))
        # Because we rotate HDMI we have to 'unrotate' the TFT by overriding pitftrot!
        if not update_configtxt(90):
            shell.bail("Unable to update /boot/config.txt")
    return True

def install_fbcp_unit():
    shell.write_text_file("/etc/systemd/system/fbcp.service",
    """[Unit]
Description=Framebuffer copy utility for PiTFT
After=network.target

[Service]
Type=simple
ExecStartPre=/bin/sleep 10
ExecStart=/usr/local/bin/fbcp

[Install]
WantedBy=multi-user.target
""", append=False)
    return True

def uninstall_fbcp():
    uninstall_fbcp_rclocal()
    # Enable overscan compensation
    shell.run_command("sudo systemctl disable fbcp.service")
    # Set up HDMI parameters:
    shell.run_command("raspi-config nonint do_overscan 0")
    print("Configuring boot/config.txt for default HDMI")
    shell.reconfig("/boot/config.txt", "^.*hdmi_force_hotplug.*$", "hdmi_force_hotplug=0")
    shell.pattern_replace("/boot/config.txt", "^.*#.*dtoverlay=vc4-fkms-v3d.*$", "dtoverlay=vc4-fkms-v3d")
    shell.pattern_replace("/boot/config.txt", '^hdmi_group=2.*$')
    shell.pattern_replace("/boot/config.txt", '^hdmi_mode=87.*$')
    shell.pattern_replace("/boot/config.txt", '^hdmi_cvt=.*$')
    return True

def uninstall_fbcp_rclocal():
    """Remove fbcp from /etc/rc.local:"""
    print("Remove fbcp from /etc/rc.local, if it's there...")
    shell.pattern_replace("/etc/rc.local", '^.*fbcp.*$')
    return True

def update_xorg():
    if "touchscreen" in pitft_config:
        transform = "Option \"TransformationMatrix\" \"{}\"".format(pitft_config["touchscreen"]["transforms"][pitftrot])
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
    uninstall_fbcp_rclocal()
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

####################################################### MAIN
target_homedir = "/home/pi"
@click.command()
@click.option('-v', '--version', is_flag=True, callback=print_version, expose_value=False, is_eager=True, help="Print version information")
@click.option('-u', '--user', nargs=1, default="/home/pi", type=str, help="Specify path of primary user's home directory", show_default=True)
@click.option('--display', nargs=1, default=None, help="Specify a display option (1-{}) or type {}".format(len(config), get_config_types()))
@click.option('--rotation', nargs=1, default=None, type=int, help="Specify a rotation option (1-4) or degrees {}".format(tuple(sorted([int(x) for x in PITFT_ROTATIONS]))))
@click.option('--install-type', nargs=1, default=None, type=click.Choice(['fbcp', 'console', 'uninstall']), help="Installation Type")
@click.option('--reboot', nargs=1, default=None, type=click.Choice(['yes', 'no']), help="Specify whether to reboot after the script is finished")
def main(user, display, rotation, install_type, reboot):
    global target_homedir, pitft_config, pitftrot, auto_reboot
    shell.clear()
    if user != target_homedir:
        target_homedir = user
        print("Homedir = {}".format(target_homedir))

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
        
    if display in [str(x) for x in range(1, len(config) + 1)]:
        pitft_config = config[int(display) - 1]
        print("Display Type: {}".format(pitft_config["menulabel"]))
        if pitft_config['kernel_upgrade']:
            print("WARNING! WILL UPGRADE YOUR KERNEL TO LATEST")
    elif display in get_config_types():
        pitft_config = get_config(display)
        print("Display Type: {}".format(pitft_config["menulabel"]))
        if pitft_config['kernel_upgrade']:
            print("WARNING! WILL UPGRADE YOUR KERNEL TO LATEST")
    else:
        # Build menu from config
        selections = []
        for item in config:
            option = "{} ({}x{})".format(item['menulabel'], item['width'], item['height'])
            if item['kernel_upgrade']:
                option += " - WARNING! WILL UPGRADE YOUR KERNEL TO LATEST"
            selections.append(option)
        selections.append("Uninstall PiTFT")
        selections.append("Quit without installing")

        PITFT_SELECT = shell.select_n("Select configuration:", selections)
        if PITFT_SELECT == len(config) + 2:
            shell.exit(1)
        if PITFT_SELECT == len(config) + 1:
            uninstall()
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

    # check init system (technique borrowed from raspi-config):
    shell.info('Checking init system...')
    if shell.run_command("which systemctl", True) and shell.run_command("systemctl | grep '\-\.mount'", True):
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

    shell.info("Updating /boot/config.txt...")
    if not update_configtxt():
        shell.bail("Unable to update /boot/config.txt")

    if "touchscreen" in pitft_config:
        shell.info("Updating SysFS rules for Touchscreen...")
        if not update_udev():
            shell.bail("Unable to update /etc/udev/rules.d")

        shell.info("Updating TSLib default calibration...")
        if not update_pointercal():
            shell.bail("Unable to update /etc/pointercal")

    # ask for console access
    if install_type == "console" or (install_type is None and shell.prompt("Would you like the console to appear on the PiTFT display?")):
        shell.info("Updating console to PiTFT...")
        if not uninstall_fbcp():
            shell.bail("Unable to uninstall fbcp")
        if not install_console():
            shell.bail("Unable to configure console")
    else:
        shell.info("Making sure console doesn't use PiTFT")
        if not uninstall_console():
            shell.bail("Unable to configure console")

        if install_type == "fbcp" or (install_type is None and shell.prompt("Would you like the HDMI display to mirror to the PiTFT display?")):
            shell.info("Adding FBCP support...")
            if not install_fbcp():
                shell.bail("Unable to configure fbcp")

            if shell.exists("/etc/lightdm"):
                shell.info("Updating X11 default calibration...")
                if not update_xorg():
                    shell.bail("Unable to update calibration")
        else:
            if not uninstall_fbcp():
                shell.bail("Unable to uninstall fbcp")
    success()

# Main function
if __name__ == "__main__":
    shell.require_root()
    main()
