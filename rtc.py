# SPDX-FileCopyrightText: 2020 Melissa LeBlanc-Williams for Adafruit Industries
#
# SPDX-License-Identifier: MIT

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
"""

try:
    from adafruit_shell import Shell
except ImportError:
    raise RuntimeError("The library 'adafruit_shell' was not found. To install, try typing: sudo pip3 install adafruit-python-shell")

shell = Shell()
shell.group = "RTC"

productname = "Real Time Clock module"  # the name of the product to install

i2creq = True  # whether the i2c interface is required
raspbianonly = True  # whether the script is allowed to run on other OSes
# os-releases supported (must be a tuple — single-element tuples require a
# trailing comma, otherwise Python treats `("Raspbian")` as a bare string and
# the `in` check below falls back to substring matching against the release
# name)
osreleases = ("Raspbian",)
oswarning = ("Debian", "Ubuntu", "Mate")  # list experimental os-releases
wheezysupport = False  # whether Wheezy is supported

CONFIG = shell.get_boot_config()


def raspbian_old():
    return shell.get_raspbian_version() in ("wheezy", "squeeze")


def dt_check():
    # Device-tree is required. Bail only if config.txt explicitly disables
    # it via a bare `device_tree=` line (legacy non-DT mode).
    return shell.exists(CONFIG) and not shell.pattern_search(CONFIG, "^device_tree=$")


# Perform all global variables declarations as well as function definition
# above this section for clarity, thanks!


def main():
    os_release = shell.get_raspbian_version()
    is_supported = os_release in osreleases
    is_experimental = os_release in oswarning

    # All modern Raspberry Pi boards (Pi 2 and newer) are supported, including
    # 64-bit Bookworm/Trixie on Pi 4/5. The original arch check only allowed
    # 32-bit ARM, which incorrectly bailed out on every 64-bit Pi install.
    if not (shell.is_armhf() or shell.is_arm64()):
        shell.bail("This hardware is not supported, sorry!\n"
                   "Config files have been left untouched")

    if shell.is_raspberry_pi_os():
        if not wheezysupport and raspbian_old():
            shell.bail(
                "\n--- Warning ---\n"
                f"The {productname} installer\n"
                "does not work on this version of Raspbian.\n"
                "Check https://github.com/adafruit/Raspberry-Pi-Installer-Scripts\n"
                "for additional information and support")
    elif raspbianonly:
        shell.bail("This script is intended for Raspbian on a Raspberry Pi!")
    else:
        if not is_supported and not is_experimental:
            shell.bail(
                "Your operating system is not supported, sorry!\n"
                "Config files have been left untouched")

    print(f"\nThis script will install everything needed to use {productname}\n")
    shell.warn(
        "--- Warning ---\n"
        "Always be careful when running scripts and commands\n"
        "copied from the internet. Ensure they are from a\n"
        "trusted source.\n"
    )

    if not shell.prompt("Do you wish to continue?", force_arg="y", default="n"):
        shell.warn("\nAborting...")
        return

    print("\nChecking hardware requirements...")

    if i2creq:
        print()
        if shell.prompt("Hardware requires I2C, enable now?", force_arg="y", default="n"):
            shell.run_raspi_config("do_i2c 0")

    if not dt_check():
        shell.bail(
            "Device Tree support required!\n"
            "Config files have been left untouched\n"
        )

    rtc_choices = ("ds1307", "ds3231", "pcf8523")
    rtcsubtype = rtc_choices[shell.select_n(
        "What RTC would you like to install?", rtc_choices
    ) - 1]

    print("Disabling any current RTC")
    # Blank any existing `dtoverlay=i2c-rtc[,...]` line in config.txt. This
    # uses Python regex semantics (\s for whitespace) rather than the POSIX
    # `[[:space:]]` class used by the shell script's `sed` invocation.
    shell.pattern_replace(CONFIG, r"^dtoverlay\s*=\s*i2c-rtc.*$")

    print(f"Adding DT overlay for {rtcsubtype}")
    shell.write_text_file(CONFIG, f"dtoverlay=i2c-rtc,{rtcsubtype}", append=True)

    print("Removing fake-hwclock")
    shell.run_command("sudo apt-get -y remove fake-hwclock")
    shell.run_command("sudo update-rc.d -f fake-hwclock remove")

    if shell.exists("/lib/udev/hwclock-set"):
        shell.warn("Configuring HW Clock")
        # Comment out the systemd-guarded block so the kernel hwclock sync runs.
        shell.run_command(
            r"sudo sed --in-place '/if \[ -e \/run\/systemd\/system \] ; then/,+2 s/^#*/#/' /lib/udev/hwclock-set"
        )
    else:
        # Trixie+ util-linux dropped hwclock-set; systemd reads the kernel RTC directly.
        print(
            "Skipping hwclock-set configuration: /lib/udev/hwclock-set\n"
            "not present (modern util-linux). systemd will sync the\n"
            "system clock from the kernel RTC at boot."
        )

    shell.prompt_reboot()


# Main function
if __name__ == "__main__":
    shell.require_root()
    main()
