from clint.textui import colored
import sys
import os
import subprocess

group = 'ADAFRUIT'

def info(system, message):
    group = system
    print(colored.green(system) + " " + message)

def bail(message = None):
    if message is None:
        print(colored.red(system) + " Exiting due to error")
    else:
        print(colored.red(system) + " Exiting due to error: {}".format(message))
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
            print(colored.red(system) + " " + err.decode("utf-8"))
        return False

def main():
    os.system('clear')
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
