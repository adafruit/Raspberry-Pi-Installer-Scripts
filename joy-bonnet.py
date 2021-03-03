try:
    from adafruit_shell import Shell
except ImportError:
    raise RuntimeError("The library 'adafruit_shell' was not found. To install, try typing: sudo pip3 install adafruit-python-shell")

shell = Shell()
shell.group = "JOY"

def main():
    shell.clear()
    print("""This script installs software for the Adafruit
Joy Bonnet for Raspberry Pi. Steps include:
- Update package index files (apt-get update).
- Install Python libraries: smbus, evdev.
- Install joyBonnet.py in /boot and
  configure /etc/rc.local to auto-start script.
- Enable I2C bus.
- OPTIONAL: disable overscan.
Run time ~10 minutes. Reboot required.
EXISTING INSTALLATION, IF ANY, WILL BE OVERWRITTEN.
""")
    if not shell.prompt("CONTINUE?", default='n'):
        print("Canceled.")
        shell.exit()
    print("Continuing...")
    disable_overscan = shell.prompt("Disable overscan?", default='n')
    install_halt = shell.prompt("Install GPIO-halt utility?", default='n')
    if install_halt:
        #halt_pin = shell.prompt("Install GPIO-halt utility?"
        halt_pin = input("GPIO pin for halt: ").strip()
    print("\n")
    if disable_overscan:
        print("Overscan: disable.")
    else:
        print("Overscan: keep current setting.")

    if install_halt:
        print("Install GPIO-halt: YES (GPIO{})".format(halt_pin))
    else:
        print("Install GPIO-halt: NO")

    if not shell.prompt("CONTINUE?", default='n'):
        print("Canceled.")
        shell.exit()

    # START INSTALL ------------------------------------------------------------
    # All selections are validated at this point...

    print("""
Starting installation...
Updating package index files...""")
    shell.run_command('sudo apt-get update', True)

    print("Installing Python libraries...")
    shell.run_command('sudo apt-get install -y python3-pip python3-dev python3-smbus')
    shell.run_command('pip3 install evdev --upgrade')

    print("Installing Adafruit code in /boot...")
    shell.chdir("/tmp")
    shell.run_command("curl -LO https://raw.githubusercontent.com/adafruit/Adafruit-Retrogame/master/joyBonnet.py")
    # Moving between filesystems requires copy-and-delete:
    shell.copy("joyBonnet.py", "/boot")
    shell.remove("joyBonnet.py")
    if install_halt:
        print("Installing gpio-halt in /usr/local/bin...")
        shell.run_command("curl -LO https://github.com/adafruit/Adafruit-GPIO-Halt/archive/master.zip")
        shell.run_command("unzip -u master.zip")
        shell.chdir("Adafruit-GPIO-Halt-master")
        shell.run_command("make")
        shell.move("gpio-halt", "/usr/local/bin")
        shell.chdir("..")
        shell.remove("Adafruit-GPIO-Halt-master")

    # CONFIG -------------------------------------------------------------------

    print("Configuring system...")

    # Enable I2C using raspi-config
    shell.run_command("sudo raspi-config nonint do_i2c 0")

    # Disable overscan compensation (use full screen):
    if disable_overscan:
        shell.run_command("sudo raspi-config nonint do_overscan 1")

    if install_halt:
        if shell.pattern_search("/etc/rc.local", "gpio-halt"):
            # gpio-halt already in rc.local, but make sure correct:
            shell.pattern_replace("/etc/rc.local", "^.*gpio-halt.*$", "/usr/local/bin/gpio-halt {} &".format(halt_pin))
        else:
            # Insert gpio-halt into rc.local before final 'exit 0'
            shell.pattern_replace("/etc/rc.local", "^exit 0", "/usr/local/bin/gpio-halt {} &\\nexit 0".format(halt_pin))

    # Auto-start joyBonnet.py on boot
    if shell.pattern_search("/etc/rc.local", "joyBonnet.py"):
        # joyBonnet.py already in rc.local, but make sure correct:
        shell.pattern_replace("/etc/rc.local", "^.*joyBonnet.py.*$", "cd /boot;python3 joyBonnet.py &")
    else:
        # Insert joyBonnet.py into rc.local before final 'exit 0'
        shell.pattern_replace("/etc/rc.local", "^exit 0", "cd /boot;python3 joyBonnet.py &\\nexit 0")

    # Add udev rule (will overwrite if present)
    shell.write_text_file("/etc/udev/rules.d/10-retrogame.rules", "SUBSYSTEM==\"input\", ATTRS{name}==\"retrogame\", ENV{ID_INPUT_KEYBOARD}=\"1\"", append=False)

    # PROMPT FOR REBOOT --------------------------------------------------------
    print("""DONE.

Settings take effect on next boot.
""")
    shell.prompt_reboot()
    
# Main function
if __name__ == "__main__":
    shell.require_root()
    main()
