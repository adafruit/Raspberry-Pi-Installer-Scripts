"""
Adafruit Raspberry Pi Blinka Setup Script
(C) Adafruit Industries, Creative Commons 3.0 - Attribution Share Alike

Written by Melissa LeBlanc-Williams for Adafruit Industries
"""

import os

try:
    from adafruit_shell import Shell
except ImportError:
    raise RuntimeError("The library 'adafruit_shell' was not found. To install, try typing: sudo pip3 install adafruit-python-shell")

shell = Shell()
shell.group="Blinka"
default_python = 3
blinka_minimum_python_version = 3.8

def default_python_version(numeric=True):
    version = shell.run_command("python -c 'import platform; print(platform.python_version())'", suppress_message=True, return_output=True)
    if numeric:
        try:
            return float(version[0:version.rfind(".")])
        except ValueError:
            return None
    return version

def get_python3_version(numeric=True):
    version = shell.run_command("python3 -c 'import platform; print(platform.python_version())'", suppress_message=True, return_output=True)
    if numeric:
        return float(version[0:version.rfind(".")])
    return version

def check_blinka_python_version():
    """
    Check the Python 3 version for Blinka (which may be a later version than we're running this script with)
    """
    print("Making sure the required version of Python is installed")
    current = get_python3_version(False)
    current_major, current_minor = current.split(".")[0:2]
    required_major, required_minor = str(blinka_minimum_python_version).split(".")[0:2]

    if int(current_major) >= int(required_major) and int(current_minor) >= int(required_minor):
        return

    shell.bail("Blinka requires a minimum of Python version {} to install, current one is {}. Please update your OS!".format(blinka_minimum_python_version, current))

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
    if not shell.run_command("sudo raspi-config nonint do_serial_hw 0", suppress_message=True):
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
    print("Making sure PIP and setuptools is installed")
    shell.run_command("sudo apt-get install --upgrade -y python3-pip python3-setuptools")

def install_blinka(user=False):
    print("Installing latest version of Blinka locally")
    shell.run_command("sudo apt-get install -y i2c-tools libgpiod-dev python3-libgpiod")
    pip_command = "pip3 install --upgrade"
    username = None
    if user:
        username = os.environ["SUDO_USER"]
    shell.run_command(f"{pip_command} adafruit-blinka", run_as_user=username)

# Custom function to run additional commands for Pi 5
def check_and_install_for_pi5(pi_model, user=False):
    if shell.is_pi5_or_newer():
        username = None
        if user:
            # Username should be used for PIP install commands
            username = os.environ["SUDO_USER"]
        print("Detected Raspberry Pi 5, applying additional fixes...")
        if shell.exists("lg"):
            shell.remove("lg")
        shell.run_command("sudo apt-get install -y wget swig python3-dev python3-setuptools")
        # Temporarily install setuptools to as root for the build process
        shell.run_command("sudo pip3 install -U setuptools", run_as_user=username)
        shell.run_command("wget http://abyz.me.uk/lg/lg.zip")
        shell.run_command("unzip lg.zip")
        if shell.exists("lg.zip"):
            shell.remove("lg.zip")
        shell.chdir("lg")
        shell.run_command("make")
        shell.run_command("sudo make install")
        # Remove setuptools after the build process is complete
        shell.run_command("sudo pip3 uninstall -y setuptools", run_as_user=username)
    else:
        print(f"Detected {pi_model}, no additional fixes needed.")

def check_user_groups():
    # Check if the user has the groups i2c, spi, gpio, input, and video. If the user is not in a group, then they need to be added.
    groups = shell.run_command("groups", suppress_message=True, return_output=True).split()
    required_groups = ["i2c", "spi", "gpio", "input", "video"]
    for group in required_groups:
        if group not in groups:
            print(f"Adding user to the group: {group}.")
            shell.run_command(f"sudo usermod -aG {group} {os.environ['SUDO_USER']}")

def main():
    global default_python
    shell.clear()
    # Check Raspberry Pi and Bail
    pi_model = shell.get_board_model()
    if not shell.is_raspberry_pi():
        shell.bail("This model of Raspberry Pi is not currently supported by Blinka")
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
    elif int(default_python_version()) < 3:
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
    check_user_groups()

    # Check and install any Pi 5 fixes if detected
    check_and_install_for_pi5(pi_model, True)

    # Done
    print("""DONE.

Settings take effect on next boot.
""")
    shell.prompt_reboot()

# Main function
if __name__ == "__main__":
    shell.require_root()
    main()
