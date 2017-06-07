#!/bin/bash

if [ $(id -u) -ne 0 ]; then
	echo "Installer must be run as root."
	echo "Try 'sudo bash $0'"
	exit 1
fi

clear

echo "This script installs software for the Adafruit"
echo "Joy Bonnet for Raspberry Pi. Steps include:"
echo "- Update package index files (apt-get update)."
echo "- Install Python libraries: smbus, evdev."
echo "- Install joyBonnet.py in /boot and"
echo "  configure /etc/rc.local to auto-start script."
echo "- Enable I2C bus."
echo "- OPTIONAL: disable overscan."
echo "Run time ~10 minutes. Reboot required."
echo "EXISTING INSTALLATION, IF ANY, WILL BE OVERWRITTEN."
echo
echo -n "CONTINUE? [y/N] "
read
if [[ ! "$REPLY" =~ ^(yes|y|Y)$ ]]; then
	echo "Canceled."
	exit 0
fi

# FEATURE PROMPTS ----------------------------------------------------------
# Installation doesn't begin until after all user input is taken.

DISABLE_OVERSCAN=0
INSTALL_HALT=0

# Given a list of strings representing options, display each option
# preceded by a number (1 to N), display a prompt, check input until
# a valid number within the selection range is entered.
selectN() {
	for ((i=1; i<=$#; i++)); do
		echo $i. ${!i}
	done
	echo
	REPLY=""
	while :
	do
		echo -n "SELECT 1-$#: "
		read
		if [[ $REPLY -ge 1 ]] && [[ $REPLY -le $# ]]; then
			return $REPLY
		fi
	done
}

echo -n "Disable overscan? [y/N] "
read
if [[ "$REPLY" =~ (yes|y|Y)$ ]]; then
	DISABLE_OVERSCAN=1
fi

echo -n "Install GPIO-halt utility? [y/N] "
read
if [[ "$REPLY" =~ (yes|y|Y)$ ]]; then
	INSTALL_HALT=1
	echo -n "GPIO pin for halt: "
	read
	HALT_PIN=$REPLY
fi

echo
if [ $DISABLE_OVERSCAN -eq 1 ]; then
	echo "Overscan: disable."
else
	echo "Overscan: keep current setting."
fi
if [ $INSTALL_HALT -eq 1 ]; then
        echo "Install GPIO-halt: YES (GPIO$HALT_PIN)"
else
        echo "Install GPIO-halt: NO"
fi
echo
echo -n "CONTINUE? [y/N] "
read
if [[ ! "$REPLY" =~ ^(yes|y|Y)$ ]]; then
	echo "Canceled."
	exit 0
fi

# START INSTALL ------------------------------------------------------------
# All selections are validated at this point...

# Given a filename, a regex pattern to match and a replacement string,
# perform replacement if found, else append replacement to end of file.
# (# $1 = filename, $2 = pattern to match, $3 = replacement)
reconfig() {
	grep $2 $1 >/dev/null
	if [ $? -eq 0 ]; then
		# Pattern found; replace in file
		sed -i "s/$2/$3/g" $1 >/dev/null
	else
		# Not found; append (silently)
		echo $3 | sudo tee -a $1 >/dev/null
	fi
}

echo
echo "Starting installation..."
echo "Updating package index files..."
apt-get update

echo "Installing Python libraries..."
apt-get install -y --force-yes python-pip python-dev python-smbus
pip install evdev --upgrade

echo "Installing Adafruit code in /boot..."
cd /tmp
curl -LO https://raw.githubusercontent.com/adafruit/Adafruit-Retrogame/master/joyBonnet.py
# Moving between filesystems requires copy-and-delete:
cp -r joyBonnet.py /boot
rm -f joyBonnet.py
if [ $INSTALL_HALT -ne 0 ]; then
	echo "Installing gpio-halt in /usr/local/bin..."
	curl -LO https://github.com/adafruit/Adafruit-GPIO-Halt/archive/master.zip
	unzip master.zip
	cd Adafruit-GPIO-Halt-master
	make
	mv gpio-halt /usr/local/bin
	cd ..
	rm -rf Adafruit-GPIO-Halt-master
fi

# CONFIG -------------------------------------------------------------------

echo "Configuring system..."

# Enable I2C using raspi-config
raspi-config nonint do_i2c 0

# Disable overscan compensation (use full screen):
if [ $DISABLE_OVERSCAN -eq 1 ]; then
	raspi-config nonint do_overscan 1
fi

if [ $INSTALL_HALT -ne 0 ]; then
	# Add gpio-halt to /rc.local:
	grep gpio-halt /etc/rc.local >/dev/null
	if [ $? -eq 0 ]; then
		# gpio-halt already in rc.local, but make sure correct:
		sed -i "s/^.*gpio-halt.*$/\/usr\/local\/bin\/gpio-halt $HALT_PIN \&/g" /etc/rc.local >/dev/null
	else
		# Insert gpio-halt into rc.local before final 'exit 0'
		sed -i "s/^exit 0/\/usr\/local\/bin\/gpio-halt $HALT_PIN \&\\nexit 0/g" /etc/rc.local >/dev/null
	fi
fi

# Auto-start joyBonnet.py on boot
grep joyBonnet.py /etc/rc.local >/dev/null
if [ $? -eq 0 ]; then
	# joyBonnet.py already in rc.local, but make sure correct:
	sed -i "s/^.*joyBonnet.py.*$/cd \/boot;python joyBonnet.py \&/g" /etc/rc.local >/dev/null
else
	# Insert joyBonnet.py into rc.local before final 'exit 0'
sed -i "s/^exit 0/cd \/boot;python joyBonnet.py \&\\nexit 0/g" /etc/rc.local >/dev/null
fi

# Add udev rule (will overwrite if present)
echo "SUBSYSTEM==\"input\", ATTRS{name}==\"retrogame\", ENV{ID_INPUT_KEYBOARD}=\"1\"" > /etc/udev/rules.d/10-retrogame.rules

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
