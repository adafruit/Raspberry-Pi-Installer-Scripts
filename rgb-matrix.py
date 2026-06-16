# SPDX-FileCopyrightText: 2018 Phillip Burgess for Adafruit Industries
#
# SPDX-License-Identifier: MIT

# INSTALLER SCRIPT FOR ADAFRUIT RGB MATRIX BONNET OR HAT

import os

try:
    from adafruit_shell import Shell
except ImportError:
    raise RuntimeError(
        "The library 'adafruit_shell' was not found. To install, try typing: "
        "sudo pip3 install adafruit-python-shell"
    )

shell = Shell()
shell.group = "RGB-Matrix"

# hzeller/rpi-rgb-led-matrix sees lots of active development!
# That's cool and all, BUT, to avoid tutorial breakage,
# we reference a specific commit (update this as needed):
GITUSER = "https://github.com/hzeller"
REPO = "rpi-rgb-led-matrix"
# This is the first commit with Pi 5 (RP1) support; older commits build a
# driver that cannot drive the matrix on a Pi 5.
COMMIT = "4e326c1b34bed36847711e5c1a421aecb879b9bb"
# Previously: COMMIT=7a503494378a67f3baa4ac680cecbae2703cc58f
# Previously: COMMIT=a3eea997a9254b83ab2de97ae80d83588f696387
# Previously: COMMIT=45d3ab5d6cff6e0c14da58930d662822627471fc
# Previously: COMMIT=21410d2b0bac006b4a1661594926af347b3ce334
# Previously: COMMIT=e3dd56dcc0408862f39cccc47c1d9dea1b0fb2d2

INTERFACES = (
    "Adafruit RGB Matrix Bonnet",
    "Adafruit RGB Matrix HAT + RTC",
)

QUALITY_OPTS = (
    "Quality (disables sound, requires soldering on single matrix Bonnet/HAT)",
    "Convenience (sound on, no soldering)",
)

ISOLCPUS_OPTS = (
    "Do not reserve a core for driving the display",
    "Reserve a core for driving the display (recommended)",
)


def set_isolcpus(cmdline_file, reserve, isolcpu_token):
    """Idempotently set the isolcpus=N token in cmdline.txt.

    cmdline.txt is a single line; strip any previously-added isolcpus token
    first (re-running the installer, or moving the SD card to a Pi with a
    different core count), then append the new one if a core is reserved.
    """
    line = shell.read_text_file(cmdline_file).strip()
    tokens = [t for t in line.split() if not t.startswith("isolcpus=")]
    if reserve:
        tokens.append(isolcpu_token)
    shell.write_text_file(cmdline_file, " ".join(tokens) + "\n", append=False)


def main():
    shell.require_root()

    num_cores = os.cpu_count() or 1
    # Reserve the highest-numbered core (isolcpus is 0-indexed).
    isolcpu_token = f"isolcpus={num_cores - 1}"

    config = shell.get_boot_config()
    if config is None:
        shell.bail("No Device Tree Detected, not supported")

    # Boot config locations. Bookworm and later use /boot/firmware/;
    # pre-Bookworm releases use /boot/.
    cmdline_file = "/boot/firmware/cmdline.txt"
    if not shell.exists(cmdline_file):
        cmdline_file = "/boot/cmdline.txt"

    shell.clear()
    print("This script installs software for the Adafruit")
    print("RGB Matrix Bonnet or HAT for Raspberry Pi.")
    print("Steps include:")
    print("- Update package index files (apt-get update)")
    print("- Install prerequisite software")
    print("- Install RGB matrix driver software and examples")
    print("- Configure boot options")
    print("Run time ~15 minutes. Some options require reboot.")
    print("EXISTING INSTALLATION, IF ANY, WILL BE OVERWRITTEN.")
    print("")
    if not shell.prompt("CONTINUE?", default="n"):
        print("Canceled.")
        shell.exit(0)

    # FEATURE PROMPTS ------------------------------------------------------
    # Installation doesn't begin until after all user input is taken.

    print("")
    print("Select interface board type:")
    interface_type = shell.select_n("", INTERFACES)

    install_rtc = False
    if interface_type == 2:
        # For matrix HAT, ask about RTC install.
        print("")
        install_rtc = shell.prompt("Install realtime clock support?")

    print("")
    print("Now you must choose between QUALITY and CONVENIENCE.")
    print("")
    print("QUALITY: best output from the LED matrix requires")
    print("commandeering hardware normally used for sound, plus")
    print("some soldering on the single matrix Bonnet/HAT.  If")
    print("you choose this option, there will")
    print("be NO sound from the audio jack or HDMI (USB audio")
    print("adapters will work and sound best anyway), AND you")
    print("must SOLDER a wire between GPIO4 and GPIO18 on the")
    print("single matrix Bonnet or HAT board. For the Triple LED")
    print("Matrix Bonnet choose QUALITY, and No soldering is")
    print("required.")
    print("")
    print("CONVENIENCE: sound works normally, no extra soldering.")
    print("Images on the LED matrix are not quite as steady, but")
    print("maybe OK for most uses.  If eager to get started, use")
    print("'CONVENIENCE' for now, you can make the change and")
    print("reinstall using this script later!")
    print("")
    print("What is thy bidding?")
    quality_mod = shell.select_n("", QUALITY_OPTS)

    # Default: don't reserve a core (e.g. single-core Pi where the menu is
    # skipped). select_n() returns 1 = "Do not reserve", 2 = "Reserve".
    isol_cpu = 1
    if num_cores >= 2:
        print("")
        print(f"Your Pi has {num_cores} CPU cores. You can dedicate one")
        print("to driving the display. This reduces flicker when the")
        print("system is busy with other work, at the cost of one core")
        print("being unavailable for general use. This is the upstream")
        print("recommendation from hzeller/rpi-rgb-led-matrix.")
        isol_cpu = shell.select_n("", ISOLCPUS_OPTS)

    # VERIFY SELECTIONS BEFORE CONTINUING ----------------------------------

    print("")
    print(f"Interface board type: {INTERFACES[interface_type - 1]}")
    if interface_type == 2:
        print(f"Install RTC support: {'YES' if install_rtc else 'NO'}")
    print(f"Optimize: {QUALITY_OPTS[quality_mod - 1]}")
    if quality_mod == 1:
        print("Reminder: you must SOLDER a wire between GPIO4")
        print("and GPIO18, and internal sound is DISABLED!")
    if num_cores >= 2:
        print(f"Isolate CPU for display driving: {ISOLCPUS_OPTS[isol_cpu - 1]}")
    print("")
    if not shell.prompt("CONTINUE?", default="n"):
        print("Canceled.")
        shell.exit(0)

    # START INSTALL --------------------------------------------------------
    # All selections are validated at this point.

    print("")
    print("Starting installation...")
    print("Updating package index files...")
    shell.run_command("apt-get update")

    print("Downloading prerequisites...")
    shell.run_command(
        "apt-get install -y python3-dev python3-pillow cython3 python3-setuptools"
    )

    print("Downloading RGB matrix software...")
    shell.run_command(
        f"curl -L {GITUSER}/{REPO}/archive/{COMMIT}.zip -o {REPO}-{COMMIT}.zip"
    )
    shell.run_command(f"unzip -q {REPO}-{COMMIT}.zip")
    shell.remove(f"{REPO}-{COMMIT}.zip")
    shell.remove("rpi-rgb-led-matrix")
    shell.run_command(f"mv {REPO}-{COMMIT} rpi-rgb-led-matrix")

    print("Building RGB matrix software...")
    shell.chdir("rpi-rgb-led-matrix")
    user_defines = ""
    if quality_mod == 2:
        user_defines = " -DDISABLE_HARDWARE_PULSES"
    shell.run_command("make clean")
    shell.run_command(f'make build-python USER_DEFINES="{user_defines}"')

    # Change ownership to the user who called sudo.
    sudo_user = os.environ.get("SUDO_USER")
    if sudo_user:
        shell.run_command(f"chown -R {sudo_user}:{sudo_user} {os.getcwd()}")

    # CONFIG ---------------------------------------------------------------

    print("Configuring system...")

    if install_rtc:
        # Enable I2C for the RTC.
        shell.run_raspi_config("do_i2c 0")
        # Blank any existing dtoverlay=i2c-rtc line, then add the DS1307.
        shell.pattern_replace(config, r"^dtoverlay\s*=\s*i2c-rtc.*$")
        shell.write_text_file(config, "dtoverlay=i2c-rtc,ds1307", append=True)
        shell.run_command("apt-get -y remove fake-hwclock")
        shell.run_command("update-rc.d -f fake-hwclock remove")
        if shell.exists("/lib/udev/hwclock-set"):
            # Comment out the systemd-guarded block so the kernel hwclock sync runs.
            shell.run_command(
                "sed --in-place "
                "'/if \\[ -e \\/run\\/systemd\\/system \\] ; then/,+2 s/^#*/#/' "
                "/lib/udev/hwclock-set"
            )

    if quality_mod == 1:
        # Quality: disable onboard sound via blacklist.
        shell.write_text_file(
            "/etc/modprobe.d/blacklist-rgb-matrix.conf",
            "blacklist snd_bcm2835",
            append=False,
        )
    else:
        # Convenience: remove the blacklist if present.
        shell.remove("/etc/modprobe.d/blacklist-rgb-matrix.conf")

    # Reserve a core for the matrix driver (upstream recommendation).
    set_isolcpus(cmdline_file, isol_cpu == 2, isolcpu_token)

    # PROMPT FOR REBOOT ----------------------------------------------------

    print("Done.")
    print("")
    print("Settings take effect on next boot.")
    if install_rtc:
        print("RTC will be enabled then but time must be set")
        print("up using the 'date' and 'hwclock' commands.")
        print(
            "ref: https://learn.adafruit.com/adding-a-real-time-clock-to-"
            "raspberry-pi/set-rtc-time#sync-time-from-pi-to-rtc"
        )
    print("")
    shell.prompt_reboot()


# Main function
if __name__ == "__main__":
    main()
