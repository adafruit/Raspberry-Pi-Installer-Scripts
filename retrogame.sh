#!/bin/bash

if [ $(id -u) -ne 0 ]; then
	echo "Installer must be run as root."
	echo "Try 'sudo bash $0'"
	exit 1
fi

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

# Given a filename, a regex pattern to match and a replacement string,
# perform replacement if found, else append replacement to end of file.
# (# $1 = filename, $2 = pattern to match, $3 = replacement)
reconfig() {
	grep $2 $1 >/dev/null
	if [ $? -eq 0 ]; then
		# Pattern found; replace in file
		sed -i s/$2/$3/g $1 >/dev/null
	else
		# Not found; append (silently)
		echo $3 | sudo tee -a $1 >/dev/null
	fi
}

clear
echo "This script downloads and installs"
echo "retrogame, a GPIO-to-keypress utility"
echo "for adding buttons and joysticks, plus"
echo "one of several configuration files."
echo "Run time <1 minute. Reboot recommended."
echo

echo "Select configuration:"
selectN "PiGRRL 2 controls" \
        "Two buttons + joystick" \
        "Six buttons + joystick" \
        "Adafruit Arcade Bonnet" \
        "Quit without installing"
RETROGAME_SELECT=$?
# These are the retrogame.cfg.* filenames on Github corresponding in
# order to each of the above selections (e.g. retrogame.cfg.pigrrl2):
CONFIGNAME=(pigrrl2 2button 6button bonnet)

if [ $RETROGAME_SELECT -lt 5 ]; then
	if [ -e /boot/retrogame.cfg ]; then
		echo "/boot/retrogame.cfg already exists."
		echo "Continuing will overwrite file."
		echo -n "CONTINUE? [y/N] "
		read
		if [[ ! "$REPLY" =~ ^(yes|y|Y)$ ]]; then
			echo "Canceled."
			exit 0
		fi
	fi

	echo -n "Downloading, installing retrogame..."
	curl -f -s -o /usr/local/bin/retrogame https://raw.githubusercontent.com/adafruit/Adafruit-Retrogame/master/retrogame
	if [ $? -eq 0 ]; then
		chmod 755 /usr/local/bin/retrogame
		echo "OK"
	else
		echo "ERROR"
	fi

	echo -n "Downloading, installing retrogame.cfg..."
	curl -f -s -o /boot/retrogame.cfg https://raw.githubusercontent.com/adafruit/Adafruit-Retrogame/master/configs/retrogame.cfg.${CONFIGNAME[$RETROGAME_SELECT-1]}
	if [ $? -eq 0 ]; then
		echo "OK"
	else
		echo "ERROR"
	fi

	echo -n "Performing other system configuration..."

	# Add udev rule (will overwrite if present)
	echo "SUBSYSTEM==\"input\", ATTRS{name}==\"retrogame\", ENV{ID_INPUT_KEYBOARD}=\"1\"" > /etc/udev/rules.d/10-retrogame.rules

	if [ $RETROGAME_SELECT -eq 4 ]; then
		# If bonnet, make sure I2C is enabled in /boot/config.txt
		reconfig /boot/config.txt ^.*dtparam=i2c_arm.*$ dtparam=i2c_arm=on 
	fi

	# Start on boot
	grep retrogame /etc/rc.local >/dev/null
	if [ $? -eq 0 ]; then
		# retrogame already in rc.local, but make sure correct:
		sed -i "s/^.*retrogame.*$/\/usr\/local\/bin\/retrogame \&/g" /etc/rc.local >/dev/null
	else
		# Insert retrogame into rc.local before final 'exit 0'
		sed -i "s/^exit 0/\/usr\/local\/bin\/retrogame \&\\nexit 0/g" /etc/rc.local >/dev/null
	fi
	echo "OK"

	echo
	echo -n "REBOOT NOW? [y/N]"
	read
	if [[ "$REPLY" =~ ^(yes|y|Y)$ ]]; then
		echo "Reboot started..."
		reboot
	#else
		echo
		echo "Done"
	fi
fi
