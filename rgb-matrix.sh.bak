#!/bin/bash

# INSTALLER SCRIPT FOR ADAFRUIT RGB MATRIX BONNET OR HAT

# hzeller/rpi-rgb-led-matrix sees lots of active development!
# That's cool and all, BUT, to avoid tutorial breakage,
# we reference a specific commit (update this as needed):
GITUSER=https://github.com/hzeller
REPO=rpi-rgb-led-matrix
COMMIT=58830f7bb5dfb47fc24f1fd26cd7c4e3a20f13f7

if [ $(id -u) -ne 0 ]; then
	echo "Installer must be run as root."
	echo "Try 'sudo bash $0'"
	exit 1
fi

clear

echo "This script installs software for the Adafruit"
echo "RGB Matrix Bonnet or HAT for Raspberry Pi."
echo "Steps include:"
echo "- Update package index files (apt-get update)"
echo "- Install prerequisite software"
echo "- Install RGB matrix driver software"
echo "- Configure boot options"
echo "Run time ~10 minutes. Some options require reboot."
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

INTERFACE_TYPE=0
INSTALL_RTC=0
QUALITY_MOD=0

# Given a list of strings representing options, display each option
# preceded by a number (1 to N), display a prompt, check input until
# a valid number within the selection range is entered.
# Can we pass an array?
selectN() {
	args=("${@}")
	for ((i=0; i<$#; i++)); do
		echo $((i+1)). ${args[$i]}
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

OPTION_NAMES=(NO YES)

INTERFACES=( \
  "Adafruit RGB Matrix Bonnet" \
  "Adafruit RGB Matrix HAT + RTC" \
)

QUALITY_OPTS=( \
  "Quality (disables sound, requires soldering)" \
  "Convenience (sound on, no soldering)" \
)

echo
echo "Select interface board type:"
selectN "${INTERFACES[@]}"
INTERFACE_TYPE=$?

if [ $INTERFACE_TYPE -eq 2 ]; then
	# For matrix HAT, ask about RTC install
	echo
	echo -n "Install realtime clock support? [y/N] "
	read
	if [[ "$REPLY" =~ (yes|y|Y)$ ]]; then
		INSTALL_RTC=1
	fi
fi

echo
echo "Now you must choose between QUALITY and CONVENIENCE."
echo
echo "QUALITY: best output from the LED matrix requires"
echo "commandeering hardware normally used for sound, plus"
echo "some soldering.  If you choose this option, there will"
echo "be NO sound from the audio jack or HDMI (USB audio"
echo "adapters will work and sound best anyway), AND you"
echo "must SOLDER a wire between GPIO4 and GPIO18 on the"
echo "Bonnet or HAT board."
echo
echo "CONVENIENCE: sound works normally, no extra soldering."
echo "Images on the LED matrix are not quite as steady, but"
echo "maybe OK for most uses.  If eager to get started, use"
echo "'CONVENIENCE' for now, you can make the change and"
echo "reinstall using this script later!"
echo
echo "What is thy bidding?"
selectN "${QUALITY_OPTS[@]}"
QUALITY_MOD=$?

# VERIFY SELECTIONS BEFORE CONTINUING --------------------------------------

echo
echo "Interface board type: ${INTERFACES[$INTERFACE_TYPE-1]}"
if [ $INTERFACE_TYPE -eq 2 ]; then
	echo "Install RTC support: ${OPTION_NAMES[$INSTALL_RTC]}"
fi
echo "Optimize: ${QUALITY_OPTS[$QUALITY_MOD-1]}"
if [ $QUALITY_MOD -eq 1 ]; then
	echo "Reminder: you must SOLDER a wire between GPIO4"
	echo "and GPIO18, and internal sound is DISABLED!"
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

echo "Downloading prerequisites..."
apt-get install -y --force-yes python-dev python-imaging

echo "Downloading RGB matrix software..."
curl -L $GITUSER/$REPO/archive/$COMMIT.zip -o $REPO-$COMMIT.zip
unzip -q $REPO-$COMMIT.zip
rm $REPO-$COMMIT.zip
mv $REPO-$COMMIT rpi-rgb-led-matrix
echo "Building RGB matrix software..."
cd rpi-rgb-led-matrix
if [ $QUALITY_MOD -eq 1 ]; then
	HARDWARE_DESC=adafruit-hat-pwm make
	cd bindings/python
	python setup.py install
else
	HARDWARE_DESC=adafruit-hat make USER_DEFINES="-DDISABLE_HARDWARE_PULSES"
	cd bindings/python
	python setup.py install
fi
# Change ownership to user calling sudo
cd ../../..
chown -R $SUDO_USER:$(id -g $SUDO_USER) rpi-rgb-led-matrix


# CONFIG -------------------------------------------------------------------

echo "Configuring system..."

if [ $INSTALL_RTC -ne 0 ]; then
	# Enable I2C for RTC
	raspi-config nonint do_i2c 0
	# Do additional RTC setup for DS1307
	reconfig /boot/config.txt "^.*dtoverlay=i2c-rtc.*$" "dtoverlay=i2c-rtc,ds1307"
	apt-get -y remove fake-hwclock
	update-rc.d -f fake-hwclock remove
	sudo sed --in-place '/if \[ -e \/run\/systemd\/system \] ; then/,+2 s/^#*/#/' /lib/udev/hwclock-set

fi

if [ $QUALITY_MOD -eq 1 ]; then
	# Disable sound ('easy way' -- kernel module not blacklisted)
	reconfig /boot/config.txt "^.*dtparam=audio.*$" "dtparam=audio=off"
else
	# Enable sound (ditto)
	reconfig /boot/config.txt "^.*dtparam=audio.*$" "dtparam=audio=on"
fi

# PROMPT FOR REBOOT --------------------------------------------------------

echo "Done."
echo
echo "Settings take effect on next boot."
if [ $INSTALL_RTC -ne 0 ]; then
	echo "RTC will be enabled then but time must be set"
	echo "up using the 'date' and 'hwclock' commands."
fi
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
