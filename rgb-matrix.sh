#!/bin/bash

# INSTALLER SCRIPT FOR ADAFRUIT RGB MATRIX BONNET OR HAT

# hzeller/rpi-rgb-led-matrix sees lots of active development!
# That's cool and all, BUT, to avoid tutorial breakage,
# we reference a specific commit (update this as needed):
GITUSER=https://github.com/hzeller
REPO=rpi-rgb-led-matrix
COMMIT=21410d2b0bac006b4a1661594926af347b3ce334
# Previously: COMMIT=e3dd56dcc0408862f39cccc47c1d9dea1b0fb2d2 

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
echo "- Install RGB matrix driver software and examples"
echo "- Configure boot options"
echo "Run time ~15 minutes. Some options require reboot."
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
#SLOWDOWN_GPIO=5
#MATRIX_SIZE=3

# Given a list of strings representing options, display each option
# preceded by a number (1 to N), display a prompt, check input until
# a valid number within the selection range is entered.
selectN() {
	args=("${@}")
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

OPTION_NAMES=(NO YES)

INTERFACES=( \
  "Adafruit RGB Matrix Bonnet" \
  "Adafruit RGB Matrix HAT + RTC" \
)

QUALITY_OPTS=( \
  "Quality (disables sound, requires soldering)" \
  "Convenience (sound on, no soldering)" \
)

#SLOWDOWN_OPTS=( \
#  "0" \
#  "1" \
#  "2" \
#  "3" \
#  "4" \
#  "None -- specify at runtime with --led-slowdown-gpio" \
#)

# Default matrix dimensions are currently fixed at 32x32 in RGB matrix lib.
# If that's compile-time configurable in the future, it'll happen here...
#MATRIX_WIDTHS=(32 32 64)
#MATRIX_HEIGHTS=(16 32 32)
#SIZE_OPTS=( \
#  "${MATRIX_WIDTHS[0]} x ${MATRIX_HEIGHTS[0]}" \
#  "${MATRIX_WIDTHS[1]} x ${MATRIX_HEIGHTS[1]}" \
#  "${MATRIX_WIDTHS[2]} x ${MATRIX_HEIGHTS[2]}" \
#  "None/other -- specify at runtime with --led-cols and --led-rows" \
#)

echo
echo "Select interface board type:"
selectN "${INTERFACES[@]}"
INTERFACE_TYPE=$?

if [ $INTERFACE_TYPE -eq 1 ]; then
	# For matrix HAT, ask about RTC install
	echo
	echo -n "Install realtime clock support? [y/N] "
	read
	if [[ "$REPLY" =~ (yes|y|Y)$ ]]; then
		INSTALL_RTC=1
	fi
fi

#echo
#echo "OPTIONAL: GPIO throttling can be compiled-in so"
#echo "there's no need to specify this every time."
#echo "For Raspberry Pi 4, it's usually 4, sometimes 3."
#echo "Smaller values work for earlier, slower Pi models."
#echo "If unsure, test different settings with the"
#echo "--led-slowdown-gpio flag at runtime, then re-run"
#echo "this installer, selecting the minimum slowdown value"
#echo "that works reliably with your Pi and matrix."
#echo "GPIO slowdown setting:"
#selectN "${SLOWDOWN_OPTS[@]}"
#SLOWDOWN_GPIO=$?

#echo
#echo "OPTIONAL: matrix size can be compiled-in so"
#echo "there's no need to specify this every time."
#echo "Some common Adafruit matrix sizes:"
#selectN "${SIZE_OPTS[@]}"
#MATRIX_SIZE=$?

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
echo "Interface board type: ${INTERFACES[$INTERFACE_TYPE]}"
if [ $INTERFACE_TYPE -eq 1 ]; then
	echo "Install RTC support: ${OPTION_NAMES[$INSTALL_RTC]}"
fi
#echo "GPIO slowdown: ${SLOWDOWN_OPTS[$SLOWDOWN_GPIO]}"
#echo "Matrix size: ${SIZE_OPTS[$MATRIX_SIZE]}"
echo "Optimize: ${QUALITY_OPTS[$QUALITY_MOD]}"
if [ $QUALITY_MOD -eq 0 ]; then
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
apt-get install -y --force-yes python2.7-dev python-pillow python3-dev python3-pillow

echo "Downloading RGB matrix software..."
curl -L $GITUSER/$REPO/archive/$COMMIT.zip -o $REPO-$COMMIT.zip
unzip -q $REPO-$COMMIT.zip
rm $REPO-$COMMIT.zip
mv $REPO-$COMMIT rpi-rgb-led-matrix
echo "Building RGB matrix software..."
cd rpi-rgb-led-matrix
USER_DEFINES=""
#if [ $SLOWDOWN_GPIO -lt 5 ]; then
#	USER_DEFINES+=" -DRGB_SLOWDOWN_GPIO=$SLOWDOWN_GPIO"
#fi
#if [ $MATRIX_SIZE --lt 3 ]; then
#	USER_DEFINES+=" -DLED_COLS=${MATRIX_WIDTHS[$MATRIX_SIZE]}"
#	USER_DEFINES+=" -DLED_ROWS=${MATRIX_HEIGHTS[$MATRIX_SIZE]}"
#fi
if [ $QUALITY_MOD -eq 0 ]; then
	# Build and install for Python 2.7...
	make clean
	make install-python HARDWARE_DESC=adafruit-hat-pwm USER_DEFINES="$USER_DEFINES" PYTHON=$(which python2)
	# Do over for Python 3...
	make clean
	make install-python HARDWARE_DESC=adafruit-hat-pwm USER_DEFINES="$USER_DEFINES" PYTHON=$(which python3)
else
	# Build then install for Python 2.7...
	USER_DEFINES+=" -DDISABLE_HARDWARE_PULSES"
	make clean
	make install-python HARDWARE_DESC=adafruit-hat USER_DEFINES="$USER_DEFINES" PYTHON=$(which python2)
	# Do over for Python 3...
	make clean
	make install-python HARDWARE_DESC=adafruit-hat USER_DEFINES="$USER_DEFINES" PYTHON=$(which python3)
fi
# Change ownership to user calling sudo
chown -R $SUDO_USER:$(id -g $SUDO_USER) `pwd`


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

if [ $QUALITY_MOD -eq 0 ]; then
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
sleep infinity
