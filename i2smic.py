# SPDX-FileCopyrightText: 2020 Melissa LeBlanc-Williams for Adafruit Industries
#
# SPDX-License-Identifier: MIT

import subprocess

try:
    from adafruit_shell import Shell
    from clint.textui import colored
except ImportError:
    raise RuntimeError("The library 'adafruit_shell' was not found. To install, try typing: sudo pip3 install adafruit-python-shell")

shell = Shell()

PRODUCT_NAME = "I2S Microphone"
OVERLAY = "googlevoicehat-soundcard"
CARD_NAME_FALLBACK = "sndrpigooglevoi"


def get_card_name(overlay):
    """Load overlay at runtime and discover the ALSA card id from arecord -l."""
    active = subprocess.run(["dtoverlay", "-l"], capture_output=True, text=True)
    if overlay not in active.stdout:
        subprocess.run(["dtoverlay", overlay], check=False)
    try:
        output = subprocess.check_output(["arecord", "-l"], stderr=subprocess.DEVNULL).decode()
        for line in output.splitlines():
            if "googlevoice" in line.lower():
                # Line looks like: "card 1: sndrpigooglevoi [snd_rpi_..."
                return line.split(":")[1].strip().split(" ")[0]
    except Exception:
        pass
    return CARD_NAME_FALLBACK


def main():
    reboot = False
    shell.clear()
    if not shell.is_raspberry_pi():
        shell.bail("Non-Raspberry Pi board detected.")
    print("\nThis script will install everything needed to use\n"
        f"an {PRODUCT_NAME}.\n")
    print(colored.red("--- Warning ---"))
    print("\nAlways be careful when running scripts and commands\n"
        "copied from the internet. Ensure they are from a\n"
        "trusted source.\n")
    if not shell.prompt("Do you wish to continue?"):
        print("\nAborting...")
        shell.exit()

    print("\nChecking hardware requirements...")

    # Locate boot config
    config = shell.get_boot_config()
    if config is None:
        shell.bail("No Device Tree Detected, not supported")

    print(f"\nAdding Device Tree Entry to {config}")

    if shell.pattern_search(config, f"^dtoverlay={OVERLAY}$"):
        print("dtoverlay already active")
    else:
        shell.write_text_file(config, f"dtoverlay={OVERLAY}")
        reboot = True

    print("\nLoading overlay and detecting ALSA card name...")
    card_name = get_card_name(OVERLAY)
    print(f"Card name: {card_name}")

    print("\n" + colored.green("All done!"))
    print(f"""
After rebooting, you can list capture devices with:

    arecord -l

And record a mono WAV with:

    arecord -D plughw:{card_name} -c1 -r 48000 -f S32_LE -t wav -V mono -v test.wav

Or stereo (two mics, one wired SEL=GND, one wired SEL=3.3V):

    arecord -D plughw:{card_name} -c2 -r 48000 -f S32_LE -t wav -V stereo -v test.wav

See the learn guide for full wiring and volume-control instructions:
  https://learn.adafruit.com/adafruit-i2s-mems-microphone-breakout/raspberry-pi-wiring-test
""")

    if reboot and not shell.argument_exists('noreboot'):
        shell.prompt_reboot(force_arg="reboot")


# Main function
if __name__ == "__main__":
    shell.require_root()
    main()
