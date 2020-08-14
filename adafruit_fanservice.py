import sys
import os
import subprocess

group = 'ADAFRUIT'

class ColorPrint:
    @staticmethod
    def print_fail(message, system=None, end = '\n'):
        if system is None:
            system = group
        sys.stdout.write('\x1b[1;31m\x1b[40m' + system.strip() + '\x1b[0m ' + message.strip() + end)

    @staticmethod
    def print_pass(message, system=None, end = '\n'):
        if system is None:
            system = group
        sys.stdout.write('\x1b[1;32m\x1b[40m' + group.strip() + '\x1b[0m ' + message.strip() + end)

    @staticmethod
    def print_warn(message, system=None, end = '\n'):
        if system is None:
            system = group
        sys.stdout.write('\x1b[1;33m\x1b[40m' + group.strip() + '\x1b[0m ' + message.strip() + end)

    @staticmethod
    def print_info(message, system=None, end = '\n'):
        if system is None:
            system = group
        sys.stdout.write('\x1b[1;34m\x1b[40m' + group.strip() + '\x1b[0m ' + message.strip() + end)

    @staticmethod
    def print_bold(message, system=None, end = '\n'):
        if system is None:
            system = group
        sys.stdout.write('\x1b[1;37m\x1b[40m' + group.strip() + '\x1b[0m ' + message.strip() + end)

def info(system, message):
    group = system
    ColorPrint.print_pass(message)

def bail(message = None):
    if message is None:
        ColorPrint.print_fail("Exiting due to error")
    else:
        ColorPrint.print_fail("Exiting due to error: {message}".format(message=message))
    sys.exit(1)

def run_command(cmd, suppress_message = False):
    proc = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE,
                          stderr=subprocess.PIPE)
    r = proc.wait()
    out = proc.stdout.read()
    err = proc.stderr.read()
    if r == 0:
        return True
    else:
        if not suppress_message:
            ColorPrint.print_fail(err.decode("utf-8"))
        return False

def main():
    os.system('clear')
    print("This script will install Adafruit")
    print("fan service, which will turn on an")
    print("external fan controlled by a given pin")
    print("")
    print("Operations performed include:")
    print("- In /boot/config.txt, enable camera")
    print("- apt-get update")
    print("- Install Python libraries:")
    print("  picamera, pygame, PIL")
    print("- Downgrade SDL library for pygame")
    print("  touch compatibility")
    print("- Download Dropbox Updater and")
    print("  Adafruit Pi Cam software")
    print("")
    print("Run time 1+ minutes. Reboot not required.")
    print("")

    if '-y' not in sys.argv:
        reply = input("CONTINUE? [y/N]")
        if reply not in ('y', 'Y', 'yes'):
            print("Canceled.")
            sys.exit(0)
    print("Continuing...")
    # check init system (technique borrowed from raspi-config):
    info('FAN', 'Checking init system...')
    if run_command("which systemctl", True) and run_command("systemctl | grep '\-\.mount'", True):
      print("Found systemd, OK!")
    elif os.path.isfile("/etc/init.d/cron") and not os.path.islink("/etc/init.d/cron"):
      bail("Found sysvinit, but we require systemd")
    else:
      bail("Unrecognised init system")

    info('FAN', 'Adding adafruit_fan.service')
    service_file = open("/etc/systemd/system/adafruit_fan.service", "wt")

    service_file.write("""[Unit]
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
WantedBy=multi-user.target""")
    service_file.close()
    
    info('FAN', 'Enabling adafruit_fan.service')
    run_command("sudo systemctl enable adafruit_fan.service")
    run_command("sudo systemctl start adafruit_fan.service")
    info('FAN', 'Done!')
    print("You can stop the fan service with 'sudo systemctl stop adafruit_fan.service'")
    print("You can start the fan service with 'sudo systemctl start adafruit_fan.service'")


# Main function
if __name__ == "__main__":
    if os.geteuid() != 0:
        print("Installer must be run as root.")
        print("Try 'sudo python3 {}'".format(sys.argv[0]))
        sys.exit(1)
    main()
