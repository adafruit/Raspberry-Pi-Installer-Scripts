#!/bin/bash

# INSTALLER SCRIPT FOR ADAFRUIT SPECTRO PROJECT

if [ $(id -u) -ne 0 ]; then
	echo "Installer must be run as root."
	echo "Try 'sudo bash $0'"
	exit 1
fi

clear

echo "This script installs software for the Adafruit"
echo "Spectro project for Raspberry Pi."
echo "Steps include:"
echo "- Update package index files (apt-get update)"
echo "- Install prerequisite software"
echo "- Install Spectro software"
echo "- Configure hardware and boot options"
echo "Run time ~10 minutes."
echo
echo "EXISTING INSTALLATION, IF ANY, WILL BE OVERWRITTEN."
echo "If you've edited any Spectro-related files, cancel"
echo "the installation and back up those files first."
echo
echo -n "CONTINUE? [y/N] "
read
if [[ ! "$REPLY" =~ ^(yes|y|Y)$ ]]; then
	echo "Canceled."
	exit 0
fi

# FEATURE PROMPTS ----------------------------------------------------------
# Installation doesn't begin until after all user input is taken.

MATRIX_SIZE=0
SLOWDOWN_GPIO=0
ENABLE_MIC=0
ENABLE_ACCEL=0
HDMI_SIZE=0

OPTION_NAMES=(NO YES)
MATRIX_WIDTHS=(64 32)
MATRIX_HEIGHTS=(32 16)
SIZE_OPTS=( \
  "${MATRIX_WIDTHS[0]} x ${MATRIX_HEIGHTS[0]}" \
  "${MATRIX_WIDTHS[1]} x ${MATRIX_HEIGHTS[1]}" \
)
SLOWDOWN_OPTS=( \
  "0" \
  "1" \
  "2" \
  "3" \
  "4" \
)
HDMI_OPTS=( \
  "640x480" \
  "320x240" \
)

# Given a list of strings representing options, display each option
# preceded by a number (1 to N), display a prompt, check input until
# a valid number within the selection range is entered.
selectN() {
	args=("${@}")
	# If first item in list is the literal number '0', make the list
	# indexed from 0 rather than 1. This is to avoid confusion when
	# entering the GPIO slowdown setting (e.g. entering '1' for a
	# value of '0' is awkward). In all other cases, list is indexed
	# from 1 as this is more human.
	if [[ ${args[0]} = "0" ]]; then
		OFFSET=0
	else
		OFFSET=1
	fi
	for ((i=0; i<$#; i++)); do
		echo $((i+$OFFSET)). ${args[$i]}
	done
	echo
	REPLY=""
	let LAST=$#+$OFFSET-1
	while :
	do
		echo -n "SELECT $OFFSET-$LAST: "
		read
		if [[ $REPLY -ge $OFFSET ]] && [[ $REPLY -le $LAST ]]; then
			let RESULT=$REPLY-$OFFSET
			return $RESULT
		fi
	done
}

echo
echo "What size LED matrix are you using with Spectro?"
selectN "${SIZE_OPTS[@]}"
MATRIX_SIZE=$?

echo
echo "Faster Pi boards require dialing back GPIO speed"
echo "to work with the LED matrix. For Raspberry Pi 4,"
echo "this usually means the max '4' slowdown setting."
echo "For Pi 2 or 3, try the '1' or '2' settings. There"
echo "is no hard-set rule to this, it can vary with"
echo "matrix and cabling as well. If the Spectro display"
echo "is glitchy, just re-run this installer, selecting"
echo "a higher setting until you find a stable value."
echo "GPIO slowdown setting:"
selectN "${SLOWDOWN_OPTS[@]}"
SLOWDOWN_GPIO=$?

echo
echo -n "OPTIONAL: Enable USB microphone support? [y/N] "
read
if [[ "$REPLY" =~ (yes|y|Y)$ ]]; then
	ENABLE_MIC=1
fi

echo
echo -n "OPTIONAL: Enable LIS3DH accelerometer support? [y/N] "
read
if [[ "$REPLY" =~ (yes|y|Y)$ ]]; then
	ENABLE_ACCEL=1
fi

# HDMI resolution selection might be handled later; right now nothing
# requires it. But in the future if anything relies on fb2matrix.py,
# HDMI resolution ultimately determines the frame rate that's possible,
# flipside being that some monitors can't handle extremely low resolutions.
# So an option might be presented here, set to 320x240 or 640x480 (the
# latter being the minimum resolution some displays can support).

# VERIFY SELECTIONS BEFORE CONTINUING --------------------------------------

echo
echo "LED matrix size: ${SIZE_OPTS[$MATRIX_SIZE]}"
echo "GPIO slowdown: ${SLOWDOWN_OPTS[$SLOWDOWN_GPIO]}"
echo "Enable USB microphone support: ${OPTION_NAMES[$ENABLE_MIC]}"
echo "Enable LIS3DH support: ${OPTION_NAMES[$ENABLE_ACCEL]}"
#echo "HDMI resolution: ${HDMI_OPTS[$HDMI_SIZE]}"
echo
echo -n "CONTINUE? [y/N] "
read
if [[ ! "$REPLY" =~ ^(yes|y|Y)$ ]]; then
	echo "Canceled."
	exit 0
fi

# Check whether RGB matrix library is present.
# If not, offer to download and run that script first (then return here).
echo
echo "Updating package index files..."
apt-get update
apt-get -qq install python3-pip python-pip
echo -n "Checking for RGB matrix library..."
pip3 freeze | grep rgbmatrix > /dev/null
if [ $? -eq 0 ]; then
	echo "OK."
else
	echo "not present."
	echo "Would you like to download and install the RGB matrix"
	echo "library (required by Spectro) first? If so, DO NOT REBOOT"
	echo "when prompted. You’ll return to this script for more"
	echo "Spectro configuration."
	echo -n "Run RGB matrix installer? [y/N] "
	read
	if [[ "$REPLY" =~ (yes|y|Y)$ ]]; then
		wget https://raw.githubusercontent.com/adafruit/Raspberry-Pi-Installer-Scripts/master/rgb-matrix.sh -O rgb-matrix.sh
		bash rgb-matrix.sh
		echo
		echo "You are now back in the main Spectro installer script."
		echo "When prompted about reboot again, now it's OK!"
	fi
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

# Same as above, but skips if pattern not found
reconfig2() {
        grep $2 $1 >/dev/null
        if [ $? -eq 0 ]; then
                # Pattern found; replace in file
                sed -i "s/$2/$3/g" $1 >/dev/null
        fi
}

echo
echo "Starting installation..."

# Although Spectro is all Python3-ready, user additions might rely on
# Python2, so we'll install the prerequisite libraries for both 2 and 3...
echo "Downloading prerequisites..."
pip3 install psutil RPi.GPIO
pip install psutil RPi.GPIO
apt-get install -y --allow-unauthenticated python3-dev python3-pillow python2.7-dev python-pillow 
if [ $ENABLE_MIC -ne 0 ]; then
	apt-get install -y --allow-unauthenticated python3-pyaudio python3-numpy python-pyaudio python-numpy
fi
if [ $ENABLE_ACCEL -ne 0 ]; then
	pip3 install adafruit-circuitpython-busdevice adafruit-circuitpython-lis3dh
	pip install adafruit-circuitpython-busdevice adafruit-circuitpython-lis3dh
fi

echo "Downloading Spectro software..."
curl -L https://github.com/adafruit/Adafruit_Spectro_Pi/archive/master.zip -o Adafruit_Spectro_Pi.zip
unzip -q -o Adafruit_Spectro_Pi.zip
rm Adafruit_Spectro_Pi.zip
mv Adafruit_Spectro_Pi-master Adafruit_Spectro_Pi
chown -R pi:pi Adafruit_Spectro_Pi

# CONFIG -------------------------------------------------------------------

echo "Configuring system..."

if [ $ENABLE_MIC -ne 0 ]; then
	# Change ALSA settings to allow USB mic use
	reconfig2 /usr/share/alsa/alsa.conf "^defaults.ctl.card.*0" "defaults.ctl.card 1"
	reconfig2 /usr/share/alsa/alsa.conf "^defaults.pcm.card.*0" "defaults.pcm.card 1"
fi

if [ $ENABLE_ACCEL -ne 0 ]; then
	# Enable I2C for accelerometer
	raspi-config nonint do_i2c 0
fi

# Make default GIFs directory
mkdir /boot/gifs

# Set up LED columns, rows and slowdown in selector.py script
reconfig2 ./Adafruit_Spectro_Pi/selector.py "^FLAGS.*$" "FLAGS\ =\ [\"--led-cols=${MATRIX_WIDTHS[$MATRIX_SIZE]}\",\ \"--led-rows=${MATRIX_HEIGHTS[$MATRIX_SIZE]}\",\ \"--led-slowdown-gpio=${SLOWDOWN_OPTS[$SLOWDOWN_GPIO]}\"]"

# Force HDMI out so /dev/fb0 exists
reconfig /boot/config.txt "^.*hdmi_force_hotplug.*$" "hdmi_force_hotplug=1"
#reconfig /boot/config.txt "^.*hdmi_group.*$" "hdmi_group=2"
#reconfig /boot/config.txt "^.*hdmi_mode.*$" "hdmi_mode=87"

# Auto-start selector.py on boot
grep selector.py /etc/rc.local >/dev/null
if [ $? -ne 0 ]; then
	# Insert selector.py into rc.local before final 'exit 0'
	sed -i "s/^exit 0/cd \/home\/pi\/Adafruit_Spectro_Pi\;python3 selector.py \&\\nexit 0/g" /etc/rc.local >/dev/null
fi

# PROMPT FOR REBOOT --------------------------------------------------------

echo "Done."
echo
echo "Settings take effect on next boot."
echo "For proper clock time, set the time zone with raspi-config."
echo
echo -n "REBOOT NOW? [y/N] "
read
if [[ ! "$REPLY" =~ ^(yes|y|Y)$ ]]; then
	echo "Exiting without reboot."
	exit 0
fi
echo "Reboot started..."
reboot
sleep infinity
