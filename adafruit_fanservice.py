try:
    from adafruit_shell import Shell
except ImportError:
    raise RuntimeError("The library 'adafruit_shell' was not found. To install, try typing: sudo pip3 install adafruit-python-shell")

shell = Shell()
shell.group = 'ADAFRUIT'

def main():
    shell.clear()
    print("""This script will install Adafruit
fan service, which will turn on an
external fan controlled by a given pin

Operations performed include:
- In /boot/config.txt, enable camera
- apt-get update
- Install Python libraries:
  picamera, pygame, PIL
- Downgrade SDL library for pygame
  touch compatibility
- Download Dropbox Updater and
  Adafruit Pi Cam software

Run time 1+ minutes. Reboot not required.

""")

    if not shell.argument_exists('y'):
        if not shell.prompt("CONTINUE?", default='n'):
            print("Canceled.")
            shell.exit()
    print("Continuing...")
    # check init system (technique borrowed from raspi-config):
    shell.group = 'FAN'
    shell.info('Checking init system...')
    if shell.run_command("which systemctl", True) and shell.run_command("systemctl | grep '\-\.mount'", True):
      print("Found systemd, OK!")
    elif os.path.isfile("/etc/init.d/cron") and not os.path.islink("/etc/init.d/cron"):
      shell.bail("Found sysvinit, but we require systemd")
    else:
      shell.bail("Unrecognised init system")

    shell.info('Adding adafruit_fan.service')
    contents = """[Unit]
Description=Fan service for some Adafruit boards
After=network.target

[Service]
Type=oneshot
ExecStartPre=-/bin/bash -c 'echo 4 >/sys/class/gpio/export'
ExecStartPre=/bin/bash -c 'echo out >/sys/class/gpio/gpio4/direction'
ExecStart=/bin/bash -c 'echo 1 >/sys/class/gpio/gpio4/value'

RemainAfterExit=true
ExecStop=/bin/bash -c 'echo 0 >/sys/class/gpio/gpio4/value'
StandardOutput=journal

[Install]
WantedBy=multi-user.target"""
    shell.write_text_file("/etc/systemd/system/adafruit_fan.service", contents, append=False)
    
    shell.info('Enabling adafruit_fan.service')
    shell.run_command("sudo systemctl enable adafruit_fan.service")
    shell.run_command("sudo systemctl start adafruit_fan.service")
    shell.info('Done!')
    print("You can stop the fan service with 'sudo systemctl stop adafruit_fan.service'")
    print("You can start the fan service with 'sudo systemctl start adafruit_fan.service'")


# Main function
if __name__ == "__main__":
    shell.require_root()
    main()
