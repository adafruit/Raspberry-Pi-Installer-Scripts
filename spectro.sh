#!/bin/bash

if [ $(id -u) -ne 0 ]; then
	echo "Installer must be run as root."
	echo "Try 'sudo bash $0'"
	exit 1
fi

if [ $PWD -ne /home/pi ]; then
	echo "Script should be run from the /home/pi directory."
	exit 2
fi

if [! -d ./rpi-rgb-led-matrix not present]; then
	echo "Please run RGB matrix installer (rgb-matrix.sh) first."
	exit 2
fi

clear

echo "This script installs software for the Adafruit"
echo "Spectro project for Raspberry Pi. Steps include:"
echo "- Update package index files (apt-get update)"
echo "- Install Python libraries: python3-dev, python3-pil,"
echo "  python3-rpi.gpio"
echo "- Download Adafruit Spectro directory in current"
echo "  location (MUST be adjacent to rpi-rgb-led-matrix"
echo "  directory in /home/pi)"
echo "- Set Spectro task-switch button (GPIO25) to run"
echo "  on startup"
echo "RGB MATRIX INSTALLER (rgb-matrix.sh) MUST BE RUN FIRST."
echo "Run time <5 minutes. Reboot required."
echo "EXISTING INSTALLATION, IF ANY, WILL BE OVERWRITTEN."
echo
echo -n "CONTINUE? [y/N] "
read
if [[ ! "$REPLY" =~ ^(yes|y|Y)$ ]]; then
	echo "Canceled."
	exit 0
fi

# START INSTALL ------------------------------------------------------------

echo
echo "Starting installation..."
echo "Updating package index files..."
apt-get update

echo "Installing Python libraries..."
apt-get install -y python3-dev python3-pil python3-rpi.gpio

echo "Installing Adafruit code and data..."
cd /tmp
curl -LO https://github.com/adafruit/Adafruit_Spectro_Pi/archive/master.zip
unzip -o master.zip
mv Adafruit_Spectro_Pi-master /home/pi/Adafruit_Spectro_Pi
chown -R pi:pi /home/pi/Adafruit_Spectro_Pi

# CONFIG -------------------------------------------------------------------

echo "Configuring system..."

# Auto-start selector.py on boot
grep selector.py /etc/rc.local >/dev/null
if [ $? -eq 0 ]; then
	# selector.py already in rc.local, but make sure correct:
	sed -i "s/^.*selector.py.*$/cd \/home\/pi\/Adafruit_Spectro_Pi;python3 selector.py \&/g" /etc/rc.local >/dev/null
else
	# Insert selector.py into rc.local before final 'exit 0'
sed -i "s/^exit 0/cd \/home\/pi\/Adafruit_Spectro_Pi;python3 selector.py \&\\nexit 0/g" /etc/rc.local >/dev/null
fi

# PROMPT FOR REBOOT --------------------------------------------------------

echo "Done."
echo
echo "Settings take effect on next boot."
echo
echo -n "REBOOT NOW? [y/N] "
read
if [[ ! "$REPLY" =~ ^(yes|y|Y)$ ]]; then
	echo "Exiting without reboot."
	exit 0
fi
echo "Reboot started..."
reboot
exit 0
