"""
Adafruit Pi Touch Cam Setup Script
(C) Adafruit Industries, Creative Commons 3.0 - Attribution Share Alike

Converted to Python by Melissa LeBlanc-Williams for Adafruit Industries

Note: Currently Untested
"""

try:
    from adafruit_shell import Shell
except ImportError:
    raise RuntimeError("The library 'adafruit_shell' was not found. To install, try typing: sudo pip3 install adafruit-python-shell")
import os

shell = Shell()
shell.group="Retrogame"

def main():
    shell.clear()
    print("""This script will install and/or modify
packages needed for the Adafruit Pi
Camera project. It requires that the
adafruit-pitft.sh installer script (for
PiTFT display support) was run first.

Operations performed include:
- In /boot/config.txt, enable camera
- apt-get update
- Install Python libraries:
  picamera, pygame, PIL
- Downgrade SDL library for pygame
  touch compatibility
- Download Dropbox Updater and
  Adafruit Pi Cam software

Run time 5+ minutes. Reboot required.
""")

    if not shell.prompt("CONTINUE?", default='n'):
        print("Canceled.")
        shell.exit()
    print("Continuing...")


    if shell.grep("dtoverlay=pitft", "/boot/config.txt"):
        shell.bail("PiTFT overlay not in /boot/config.txt.\n"
        "Download & run adafruit-pitft.py first.\n"
        "Canceling.")

    print("Configuring camera + PiTFT settings...")

    # Set PiTFT speed to 80 MHz, 60 Hz
    shell.pattern_replace("/boot/config.txt", "speed=.*,fps=.*", "speed=80000000,fps=60")

    # Check if Pi camera is enabled. If not, add it...
    shell.reconfig("/boot/config.txt", "^start_x=.*", "start_x=1")

    # gpu_mem must be >= 128 MB for camera to work
    result = shell.pattern_search("/boot/config.txt", "^gpu_mem=", return_match=True)
    if not result:
        # gpu_mem isn't set. Add to config
        shell.write_text_file("/boot/config.txt", "\ngpu_mem=128", append=True)
    elif result.group(1) < 128:
        # gpu_mem present but too small; increase to 128MB
        shell.reconfig("/boot/config.txt", "^gpu_mem=.*", "gpu_mem=128")

    print("Installing prerequisite packages...")

    # Enable Wheezy package sources (for SDL downgrade)
    shell.write_text_file("/etc/apt/sources.list.d/wheezy.list", "deb http://archive.raspbian.org/raspbian wheezy main\n", append=True)

    # Set 'stable' as default package source (current OS)
    shell.write_text_file("/etc/apt/apt.conf.d/10defaultRelease", "APT::Default-release \"stable\";\n", append=True)

    # Set priority for libsdl from Wheezy higher than current package
    shell.write_text_file("/etc/apt/preferences.d/libsdl", (
        "Package: libsdl1.2debian\n"
        "Pin: release n=stretch\n"
        "Pin-Priority: -10\n"
        "Pin: release n=jessie\n"
        "Pin-Priority: -10\n"
        "Package: libsdl1.2debian\n"
        "Pin: release n=wheezy\n"
        "Pin-Priority:900\n"
    ))

    # Update the APT package index files, install Python libraries
    print("Updating System Packages")
    if not shell.run_command("sudo apt-get update"):
        shell.bail("Apt failed to update indexes!")
    print("Installing packages...")
    if not shell.run_command("sudo apt-get -y --force-yes install python-picamera python-pygame python-imaging"):
        shell.bail("Apt failed to install software!")

    print("Downgrading SDL library...")

    if not shell.run_command("apt-get -y --force-yes install libsdl1.2debian/wheezy"):
        shell.bail("Apt failed to downgrade SDL library!")

    print("Downloading Dropbox uploader and")
    print("Adafruit Pi Cam to home directory...")

    shell.chdir("~pi")
    shell.run_command("wget https://github.com/andreafabrizi/Dropbox-Uploader/archive/master.zip")
    shell.run_command("unzip master.zip")
    shell.remove("master.zip")
    shell.move("Dropbox-Uploader-master", "Dropbox-Uploader")

    shell.run_command("wget https://github.com/adafruit/adafruit-pi-cam/archive/master.zip")
    shell.run_command("unzip master.zip")
    shell.remove("master.zip")
    shell.chown("Dropbox-Uploader", "pi", recursive=True)
    shell.chown("adafruit-pi-cam-master", "pi", recursive=True)

    # Add lines to /etc/rc.local (commented out by default):
    shell.pattern_replace("/etc/rc.local", "^exit 0", "# Enable this line to run camera at startup:\n# cd /home/pi/adafruit-pi-cam-master ; sudo python cam.py\n\nexit 0")

    # Prompt to reboot!
    print("\nCamera and PiTFT settings won't take")
    print("effect until next boot.")
    shell.prompt_reboot()

# Main function
if __name__ == "__main__":
    shell.require_root()
    main()