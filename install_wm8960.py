# SPDX-FileCopyrightText: 2025 Melissa LeBlanc-Williams for Adafruit Industries
#
# SPDX-License-Identifier: MIT

import os

try:
    from adafruit_shell import Shell
except ImportError:
    raise RuntimeError("The library 'adafruit_shell' was not found. To install, try typing: sudo pip3 install adafruit-python-shell")

shell = Shell()
shell.group = "WM8960"

REPO = "https://github.com/waveshare/WM8960-Audio-HAT"
CLONE_DIR = "WM8960-Audio-HAT"
MODULE = "wm8960-soundcard"
VERSION = "1.0"
MARKER = "0.0.0"


def append_if_missing(path, line):
    """grep -q '^line$' file || echo line >> file"""
    if not shell.pattern_search(path, f"^{line}$"):
        shell.write_text_file(path, line, append=True)


def install_module(src):
    """Build and install the DKMS module for every installed kernel >= 6.5."""
    marker_dir = f"/var/lib/dkms/{MODULE}/{VERSION}/{MARKER}"
    if shell.exists(marker_dir):
        os.rmdir(marker_dir)

    if shell.exists(f"/usr/src/{MODULE}-{VERSION}") or shell.exists(
        f"/var/lib/dkms/{MODULE}/{VERSION}"
    ):
        shell.run_command(f"dkms remove --force -m {MODULE} -v {VERSION} --all || true")
        shell.remove(f"/usr/src/{MODULE}-{VERSION}")

    shell.run_command(f"mkdir -p /usr/src/{MODULE}-{VERSION}")
    shell.run_command(f"cp -a {src}/* /usr/src/{MODULE}-{VERSION}/")
    shell.run_command(f"dkms add -m {MODULE} -v {VERSION}")

    # Build/install only for kernels >= 6.5.
    for kernel in os.listdir("/lib/modules"):
        try:
            major, minor = (int(p) for p in kernel.split(".")[:2])
        except ValueError:
            continue
        if (major, minor) < (6, 5):
            continue
        if shell.run_command(
            f'dkms build "{kernel}" -k "{kernel}" '
            f'--kernelsourcedir "/lib/modules/{kernel}/build" '
            f"-m {MODULE} -v {VERSION}"
        ):
            shell.run_command(
                f'dkms install --force "{kernel}" -k "{kernel}" -m {MODULE} -v {VERSION}'
            )

    shell.run_command(f"mkdir -p {marker_dir}")


def main():
    shell.require_root()
    if not shell.is_raspberry_pi():
        shell.bail("Sorry, this driver only works on a Raspberry Pi")

    config = shell.get_boot_config()
    if config is None:
        shell.bail("No Device Tree Detected, not supported")

    # Download the archive
    shell.remove(CLONE_DIR)
    shell.run_command(f"git clone {REPO}")
    shell.chdir(CLONE_DIR)

    shell.run_command("apt-get -y update")
    shell.run_command(
        "apt-get -y install raspberrypi-kernel-headers "
        "--no-install-recommends --no-install-suggests"
    )
    shell.run_command(
        "apt-get -y install dkms git i2c-tools libasound2-plugins "
        "--no-install-recommends --no-install-suggests"
    )
    shell.run_command("apt-get -y clean")

    install_module("./")

    # Install device tree overlay
    shell.copy("wm8960-soundcard.dtbo", "/boot/overlays")

    # Set kernel modules
    append_if_missing("/etc/modules", "i2c-dev")
    append_if_missing("/etc/modules", "snd-soc-wm8960")
    append_if_missing("/etc/modules", "snd-soc-wm8960-soundcard")

    # Set modprobe blacklist
    append_if_missing("/etc/modprobe.d/raspi-blacklist.conf", "blacklist snd_bcm2835")

    # Set dtoverlays (uncomment if present, else append)
    shell.reconfig(config, "^#?dtparam=i2s=on", "dtparam=i2s=on")
    shell.reconfig(config, "^#?dtparam=i2c_arm=on", "dtparam=i2c_arm=on")
    append_if_missing(config, "dtoverlay=i2s-mmap")
    append_if_missing(config, "dtoverlay=wm8960-soundcard")

    # Install config files
    shell.run_command("mkdir -p /etc/wm8960-soundcard")
    shell.run_command("cp *.conf /etc/wm8960-soundcard")
    shell.run_command("cp *.state /etc/wm8960-soundcard")

    # Set service
    shell.copy("wm8960-soundcard", "/usr/bin/")
    shell.run_command("chmod -x wm8960-soundcard.service")
    shell.copy("wm8960-soundcard.service", "/lib/systemd/system/")
    shell.run_command("systemctl enable wm8960-soundcard.service")

    # Cleanup
    shell.chdir("..")
    shell.remove(CLONE_DIR)

    print("------------------------------------------------------")
    print("Please reboot your Raspberry Pi to apply all settings")
    print("Enjoy!")
    print("------------------------------------------------------")
    shell.prompt_reboot()


# Main function
if __name__ == "__main__":
    main()
