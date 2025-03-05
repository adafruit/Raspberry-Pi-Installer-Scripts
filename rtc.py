"""
Adafruit Raspberry Pi Real Time Clock Setup Script

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES
OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT
HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY,
WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR
OTHER DEALINGS IN THE SOFTWARE.

This script is licensed under the terms of the MIT license.
Unless otherwise noted, code reproduced herein
was written for this script.

Originally written by the - The Pimoroni Crew -

Converted to Python by Melissa LeBlanc-Williams for Adafruit Industries


Note: Currently Untested
"""

try:
    from adafruit_shell import Shell
except ImportError:
    raise RuntimeError("The library 'adafruit_shell' was not found. To install, try typing: sudo pip3 install adafruit-python-shell")

shell = Shell()

productname = "Real Time Clock module" # the name of the product to install
rtcsubtype = "ds1307"
baseurl = "http://www.adafru.it"
scriptname = "rtc.py" # the name of this script

spacereq = 1 # minimum size required on root partition in MB
debugmode = False # whether the script should use debug routines
debuguser = None # optional test git user to use in debug mode
debugpoint = None # optional git repo branch or tag to checkout
forcesudo = True # whether the script requires to be ran with root privileges
promptreboot = False # whether the script should always prompt user to reboot
customcmd = True # whether to execute commands specified before exit
i2creq = True # whether the i2c interface is required
i2sreq = False # whether the i2s interface is required
spireq = False # whether the spi interface is required
uartreq = False # whether uart communication is required
armhfonly = True # whether the script is allowed to run on other arch
armv6 = True # whether armv6 processors are supported
armv7 = True # whether armv7 processors are supported
armv8 = True # whether armv8 processors are supported
raspbianonly = True # whether the script is allowed to run on other OSes
macosxsupport = False # whether Mac OS X is supported by the script
osreleases = ( "Raspbian" ) # list os-releases supported
oswarning = ( "Debian", "Ubuntu", "Mate" ) # list experimental os-releases
squeezesupport = False # whether Squeeze is supported
wheezysupport = False # whether Wheezy is supported
jessiesupport = True # whether Jessie is supported

DEVICE_TREE = True
ASK_TO_REBOOT = False
CURRENT_SETTING = False
UPDATED_DB = False

BOOTCMD = "/boot/cmdline.txt"
CONFIG = shell.get_boot_config()
APTSRC = "/etc/apt/sources.list"
INITABCONF = "/etc/inittab"
BLACKLIST = "/etc/modprobe.d/raspi-blacklist.conf"
LOADMOD = "/etc/modules"
DTBODIR = "/boot/overlays"

def raspbian_old():
    return shell.get_raspbian_version() in ("wheezy", "squeeze")

def dt_check():
    # Check if /boot/firmware/config.txt exists and de
    return shell.exists(CONFIG) and not shell.pattern_search(CONFIG, "^device_tree=$")

#Perform all global variables declarations as well as function definition
#above this section for clarity, thanks!

def main():
    os_release = shell.get_raspbian_version()
    IS_SUPPORTED = os_release in osreleases
    IS_EXPERIMENTAL = os_release in oswarning

    if not shell.is_armhf() or shell.is_arm64():
        shell.bail("This hardware is not supported, sorry!\n"
            "Config files have been left untouched")

    if shell.is_raspberry_pi_os():
        if not wheezysupport and raspbian_old():
            shell.bail(
                "\n--- Warning ---\n"
                f"The {productname} installer\n"
                "does not work on this version of Raspbian.\n"
                r"Check https://github.com/{gitusername}/{gitreponame}"
                "\nfor additional information and support")
    elif raspbianonly:
            shell.bail("This script is intended for Raspbian on a Raspberry Pi!")
    else:
        if not IS_SUPPORTED and not IS_EXPERIMENTAL:
            shell.bail(
                "Your operating system is not supported, sorry!\n"
                "Config files have been left untouched")

    if forcesudo:
        shell.require_root()

    print(f"\nThis script will install everything needed to use {productname}\n")
    shell.warn(
        "--- Warning ---\n"
        "Always be careful when running scripts and commands\n"
        "copied from the internet. Ensure they are from a\n"
        "trusted source.\n"
        "\n"
        "If you want to see what this script does before\n"
        "running it, you should run:\n"
        "    \curl -sS $baseurl/$scriptname\n"
        "\n"
    )

    if shell.prompt("Do you wish to continue?", force_arg="y", default="n"):
        print("\nChecking hardware requirements...")

        if i2creq == "yes":
            print()
            if shell.prompt("Hardware requires I2C, enable now?", force_arg="y", default="n"):
                shell.run_command("sudo raspi-config nonint do_i2c 0")

        if not dt_check():
            shell.bail(
                "Device Tree support required!\n"
                "Config files have been left untouched\n"
            )

        rtc_values = ("ds1307", "ds3231", "pcf8523")
        rtcsubtype = rtc_values[shell.select_n("What RTC would you like to install?", rtc_values) - 1]

        print("Disabling any current RTC")
        shell.run_command(f"sudo sed --in-place '/dtoverlay[[:space:]]*=[[:space:]]*i2c-rtc/d' {CONFIG}")

        print(f"Adding DT overlay for {rtcsubtype}")
        shell.write_text_file(CONFIG, f"dtoverlay=i2c-rtc,{rtcsubtype}", append=True)

        print("Removing fake-hwclock")
        shell.run_command("sudo apt-get -y remove fake-hwclock")
        shell.run_command("sudo update-rc.d -f fake-hwclock remove")

        if not shell.exists("/lib/udev/hwclock-set"):
            shell.bail("Couldn't find /lib/udev/hwclock-set")

        shell.warn("Configuring HW Clock")
        shell.run_command("sudo sed --in-place '/if \[ -e \/run\/systemd\/system \] ; then/,+2 s/^#*/#/' /lib/udev/hwclock-set")
        shell.prompt_reboot()

    else:
        shell.warn("\nAborting...")

# Main function
if __name__ == "__main__":
    main()