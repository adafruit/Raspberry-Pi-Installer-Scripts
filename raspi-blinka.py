"""
Adafruit Raspberry Pi Blinka Setup Script
(C) Adafruit Industries, Creative Commons 3.0 - Attribution Share Alike

Written by Melissa LeBlanc-Williams for Adafruit Industries
"""

import os
import sys
from pkg_resources import packaging

try:
    from adafruit_shell import Shell
except ImportError:
    raise RuntimeError("The library 'adafruit_shell' was not found. To install, try typing: sudo pip3 install adafruit-python-shell")

shell = Shell()
shell.group="Blinka"
default_python = 3
blinka_minimum_python_version = "3.7.0"
python_command="'import platform; print(platform.python_version())'"

def default_python_version():
    return shell.run_command("python -c " + python_command, suppress_message=True, return_output=True)

def get_python3_version():
    return shell.run_command("python3 -c " + python_command, suppress_message=True, return_output=True)

def check_blinka_python_version():
    """
    Check the Python 3 version for Blinka (which may be a later version than we're running this script with)
    """
    print("Making sure the required version of Python is installed")
    current = packaging.version.parse(get_python3_version())
    required = packaging.version.parse(blinka_minimum_python_version)

    if current >= required:
        return

    shell.bail("Blinka requires a minimum of Python version {} to install; the current version is {}. Please update your OS!".format(blinka_minimum_python_version, current))

def sys_update():
    print("Updating System Packages")
    if not shell.run_command("sudo apt-get update --allow-releaseinfo-change"):
        shell.bail("Apt failed to update indexes!")
    print("Upgrading packages...")
    if not shell.run_command("sudo apt-get -y upgrade"):
        shell.bail("Apt failed to install software!")

def set_raspiconfig():
    """
    Enable various Raspberry Pi interfaces
    """
    print("Enabling I2C")
    shell.run_command("sudo raspi-config nonint do_i2c 0")
    print("Enabling SPI")
    shell.run_command("sudo raspi-config nonint do_spi 0")
    print("Enabling Serial")
    shell.run_command("sudo raspi-config nonint do_serial 0")
    print("Enabling SSH")
    shell.run_command("sudo raspi-config nonint do_ssh 0")
    print("Enabling Camera")
    shell.run_command("sudo raspi-config nonint do_camera 0")
    print("Disable raspi-config at Boot")
    shell.run_command("sudo raspi-config nonint disable_raspi_config_at_boot 0")

def update_python():
    print("Making sure Python 3 is the default")
    if default_python < 3:
        shell.run_command("sudo apt-get install -y python3 git python3-pip")
        shell.run_command("sudo update-alternatives --install /usr/bin/python python $(which python2) 1")
        shell.run_command("sudo update-alternatives --install /usr/bin/python python $(which python3) 2")
        shell.run_command("sudo update-alternatives --skip-auto --config python")

def update_pip():
    print("Making sure PIP is installed")
    shell.run_command("sudo apt-get install -y python3-pip")
    shell.run_command("sudo pip3 install --upgrade setuptools")

def install_blinka(user=False):
    print("Installing latest version of Blinka locally")
    shell.run_command("sudo apt-get install -y i2c-tools libgpiod-dev")
    pip_command = "pip3 install --upgrade"
    username = None
    if user:
        username = os.environ["SUDO_USER"]
    shell.run_command(f"{pip_command} RPi.GPIO", run_as_user=username)
    shell.run_command(f"{pip_command} adafruit-blinka", run_as_user=username)

def main():
    global default_python
    shell.clear()
    # Check Raspberry Pi and Bail
    pi_model = shell.get_board_model()
    print("""This script configures your
Raspberry Pi and installs Blinka
""")
    print("{} detected.\n".format(pi_model))
    if not shell.is_raspberry_pi():
        shell.bail("Non-Raspberry Pi board detected. This must be run on a Raspberry Pi")
    os_identifier = shell.get_os()
    if os_identifier != "Raspbian":
        shell.bail("Sorry, the OS detected was {}. This script currently only runs on Raspberry Pi OS.".format(os_identifier))
    if not shell.is_python3():
        shell.bail("You must be running Python 3. Older versions have now been deprecated.")
    shell.check_kernel_update_reboot_required()
    python_version = default_python_version()
    if not python_version:
        shell.warn("WARNING No Default System python tied to the `python` command. It will be set to Version 3.")
        default_python = 0
        if not shell.prompt("Continue?"):
            shell.exit()
    elif packaging.version.parse(default_python_version()) < packaging.version.parse("3.0.0"):
        shell.warn("WARNING Default System python version is {}. It will be updated to Version 3.".format(default_python_version(False)))
        default_python = 2
        if not shell.prompt("Continue?"):
            shell.exit()
    sys_update()
    check_blinka_python_version()
    set_raspiconfig()
    update_python()
    update_pip()
    install_blinka(True)

    # Done
    print("""DONE.

Settings take effect on next boot.
""")
    shell.prompt_reboot()

# Main function
if __name__ == "__main__":
    shell.require_root()
    main()
