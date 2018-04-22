#!/bin/bash

if [ $(id -u) -ne 0 ]; then
	echo "Installer must be run as root."
	echo "Try 'sudo bash $0'"
	exit 1
fi

clear

echo "This script installs software for the Adafruit"
echo "Snake Eyes Bonnet for Raspberry Pi. Steps include:"
echo "- Update package index files (apt-get update)"
echo "- Install Python libraries: numpy, pi3d, svg.path,"
echo "  python-dev, python-imaging"
echo "- Install Adafruit eye code and data in /boot"
echo "- Enable SPI0 and SPI1 peripherals if needed"
echo "- Set HDMI resolution, disable overscan"
echo "Run time ~25 minutes. Reboot required."
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

INSTALL_HALT=0
INSTALL_ADC=0
INSTALL_GADGET=0

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

SCREEN_VALUES=(-o -t -i)
SCREEN_NAMES=("OLED (128x128)" "TFT (128x128)" "IPS (240x240)" HDMI)
RADIUS_VALUES=(128 128 240)
OPTION_NAMES=(NO YES)
echo
echo "Select screen type:"
selectN "${SCREEN_NAMES[0]}" \
        "${SCREEN_NAMES[1]}" \
        "${SCREEN_NAMES[2]}" \
        "${SCREEN_NAMES[3]}"
SCREEN_SELECT=$?

echo -n "Install GPIO-halt utility? [y/N] "
read
if [[ "$REPLY" =~ (yes|y|Y)$ ]]; then
	INSTALL_HALT=1
	echo -n "GPIO pin for halt: "
	read
	HALT_PIN=$REPLY
fi

echo -n "Install ADC support? [y/N] "
read
if [[ "$REPLY" =~ (yes|y|Y)$ ]]; then
	INSTALL_ADC=1
fi

echo -n "Install USB Ethernet gadget support? (Pi Zero) [y/N] "
read
if [[ "$REPLY" =~ (yes|y|Y)$ ]]; then
	INSTALL_GADGET=1
fi

echo
echo "Screen type: ${SCREEN_NAMES[$SCREEN_SELECT-1]}"
if [ $INSTALL_HALT -eq 1 ]; then
	echo "Install GPIO-halt: YES (GPIO$HALT_PIN)"
else
	echo "Install GPIO-halt: NO"
fi
echo "ADC support: ${OPTION_NAMES[$INSTALL_ADC]}"
echo "Ethernet USB gadget support: ${OPTION_NAMES[$INSTALL_GADGET]}"
if [ $SCREEN_SELECT -eq 3 ]; then
	echo "Video resolution will be set to 1280x720, no overscan"
else
	echo "Video resolution will be set to 640x480, no overscan"
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

# Same as above, but appends to same line rather than new line
reconfig2() {
	grep $2 $1 >/dev/null
	if [ $? -eq 0 ]; then
		# Pattern found; replace in file
		sed -i "s/$2/$3/g" $1 >/dev/null
	else
		# Not found; append to line (silently)
                sed -i "s/$/ $3/g" $1 >/dev/null

	fi
}

echo
echo "Starting installation..."
echo "Updating package index files..."
apt-get update

echo "Installing Python libraries..."
apt-get install -y --force-yes python-pip python-dev python-imaging python-smbus
pip install numpy pi3d svg.path adafruit-ads1x15
# smbus and ads1x15 Python libs are installed regardless whether ADC
# is enabled; simplifies the Python code a little (no "uncomment this")

echo "Installing Adafruit code and data in /boot..."
cd /tmp
curl -LO https://github.com/adafruit/Pi_Eyes/archive/master.zip
unzip master.zip
# Moving between filesystems requires copy-and-delete:
cp -r Pi_Eyes-master /boot/Pi_Eyes
rm -rf master.zip Pi_Eyes-master
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

# Disable overscan compensation (use full screen):
raspi-config nonint do_overscan 1

# HDMI settings for Pi eyes
reconfig /boot/config.txt "^.*hdmi_force_hotplug.*$" "hdmi_force_hotplug=1"
reconfig /boot/config.txt "^.*hdmi_group.*$" "hdmi_group=2"
reconfig /boot/config.txt "^.*hdmi_mode.*$" "hdmi_mode=87"
if [ $SCREEN_SELECT -eq 3 ]; then
	# IPS display - set HDMI to 1280x720
	reconfig /boot/config.txt "^.*hdmi_cvt.*$" "hdmi_cvt=1280 720 60 1 0 0 0"
else
	# All others - set HDMI to 640x480
	reconfig /boot/config.txt "^.*hdmi_cvt.*$" "hdmi_cvt=640 480 60 1 0 0 0"
fi

# Enable I2C for ADC
if [ $INSTALL_ADC -ne 0 ]; then
	raspi-config nonint do_i2c 0
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

# If using OLED, TFT or IPS, enable SPI and install fbx2 and eyes.py,
# else (HDMI) skip SPI, fbx2 and install cyclops.py (single eye)
if [ $SCREEN_SELECT -ne 4 ]; then

	# Enable SPI0 using raspi-config
	raspi-config nonint do_spi 0

	# Enable SPI1 by adding overlay to /boot/config.txt
	reconfig /boot/config.txt "^.*dtparam=spi1.*$" "dtparam=spi1=on"
	reconfig /boot/config.txt "^.*dtoverlay=spi1.*$" "dtoverlay=spi1-3cs"

	# Adjust spidev buffer size to 8K (default is 4K)
	reconfig2 /boot/cmdline.txt "spidev\.bufsiz=.*" "spidev.bufsiz=8192"

	SCREEN_OPT=${SCREEN_VALUES[($SCREEN_SELECT-1)]}

	# Auto-start fbx2 on boot
	grep fbx2 /etc/rc.local >/dev/null
	if [ $? -eq 0 ]; then
		# fbx2 already in rc.local, but make sure correct:
		sed -i "s/^.*fbx2.*$/\/boot\/Pi_Eyes\/fbx2 $SCREEN_OPT \&/g" /etc/rc.local >/dev/null
	else
		# Insert fbx2 into rc.local before final 'exit 0'
	sed -i "s/^exit 0/\/boot\/Pi_Eyes\/fbx2 $SCREEN_OPT \&\\nexit 0/g" /etc/rc.local >/dev/null
	fi

	RADIUS=${RADIUS_VALUES[($SCREEN_SELECT-1)]}
	# Auto-start eyes.py on boot
	grep eyes.py /etc/rc.local >/dev/null
	if [ $? -eq 0 ]; then
		# eyes.py already in rc.local, but make sure correct:
		sed -i "s/^.*eyes.py.*$/cd \/boot\/Pi_Eyes;python eyes.py --radius $RADIUS \&/g" /etc/rc.local >/dev/null
	else
		# Insert eyes.py into rc.local before final 'exit 0'
	sed -i "s/^exit 0/cd \/boot\/Pi_Eyes;python eyes.py --radius $RADIUS \&\\nexit 0/g" /etc/rc.local >/dev/null
	fi

else

	# Auto-start cyclops.py on boot
	grep cyclops.py /etc/rc.local >/dev/null
	if [ $? -eq 0 ]; then
		# cyclops.py already in rc.local, but make sure correct:
		sed -i "s/^.*cyclops.py.*$/cd \/boot\/Pi_Eyes;python cyclops.py \&/g" /etc/rc.local >/dev/null
	else
		# Insert cyclops.py into rc.local before final 'exit 0'
	sed -i "s/^exit 0/cd \/boot\/Pi_Eyes;python cyclops.py \&\\nexit 0/g" /etc/rc.local >/dev/null
	fi

fi

if [ $INSTALL_GADGET -ne 0 ]; then
	reconfig /boot/config.txt "^.*dtoverlay=dwc2.*$" "dtoverlay=dwc2"
	grep "modules-load=dwc2,g_ether" /boot/cmdline.txt >/dev/null
	if [ $? -ne 0 ]; then
		# Insert ethernet gadget into config.txt after 'rootwait'
		sed -i "s/rootwait/rootwait modules-load=dwc2,g_ether/g" /boot/cmdline.txt >/dev/null
	fi
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
