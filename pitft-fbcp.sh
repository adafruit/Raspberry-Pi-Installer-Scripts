#!/bin/bash

if [ $(id -u) -ne 0 ]; then
	echo "Installer must be run as root."
	echo "Try 'sudo bash $0'"
	exit 1
fi

clear

echo "This script enables basic PiTFT display"
echo "support for portable gaming, etc.  Does"
echo "not cover X11, touchscreen or buttons"
echo "(see adafruit-pitft-helper for those)."
echo "HDMI output is set to PiTFT resolution,"
echo "not all monitors support this, PiTFT"
echo "may be only display after reboot."
echo "Run time ~5 minutes. Reboot required."
echo
echo -n "CONTINUE? [y/N] "
read
if [[ ! "$REPLY" =~ ^(yes|y|Y)$ ]]; then
	echo "Canceled."
	exit 0
fi

# FEATURE PROMPTS ----------------------------------------------------------
# Installation doesn't begin until after all user input is taken.

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

echo
echo "Select project:"
selectN "PiGRRL 2" \
        "Pocket PiGRRL" \
        "PiGRRL Zero" \
        "Cupcade (horizontal screen)" \
        "Cupcade (vertical screen)" \
        "Configure options manually"
PROJ_SELECT=$?

PITFT_VALUES=(pitft22 pitft28-resistive pitft28-capacitive pitft35-resistive)
WIDTH_VALUES=(320 320 320 480)
HEIGHT_VALUES=(240 240 240 320)
HZ_VALUES=(80000000 80000000 80000000 32000000)
# Framebuffer (HDMI out) rotation:
FBROTATE_VALUES=(0 1 2 3)
# PiTFT (MADCTL) rotation:
TFTROTATE_VALUES=(0 90 180 270)

if [ $PROJ_SELECT -lt 6 ]; then

	# Use preconfigured settings per-project

	# 3 elements per project; first is index (1+) into
	# PITFT_VALUES, second and third are index into
	# FBROTATE_VALUES and TFTROTATE_VALUES:
	PROJ_VALUES=(2 1 4   1 1 4   1 1 4   2 1 2   2 2 2)
	# FBROTATE index is almost always 1, except for HDMI portrait mode

	PITFT_SELECT=${PROJ_VALUES[($PROJ_SELECT-1)*3]}
	FBROTATE_SELECT=${PROJ_VALUES[($PROJ_SELECT-1)*3+1]}
	TFTROTATE_SELECT=${PROJ_VALUES[($PROJ_SELECT-1)*3+2]}

else

	# Configure options manually

	echo
	echo "Select display type:"
	#        123456789012345678901234567890123456789
	selectN "PiTFT 2.2\" HAT" \
		"PiTFT / PiTFT Plus resistive 2.4-3.2\"" \
		"PiTFT / PiTFT Plus 2.8\" capacitive" \
		"PiTFT / PiTFT Plus 3.5\""
	PITFT_SELECT=$?

	echo
	echo "HDMI rotation:"
	selectN "Normal (landscape)" \
		"90° clockwise (portrait)" \
		"180° (landscape)" \
		"90° counterclockwise (portrait)"
	FBROTATE_SELECT=$?

	echo
	echo "TFT (MADCTL) rotation:"
	selectN "0" \
		"90" \
		"180" \
		"270"
	TFTROTATE_SELECT=$?

fi

# START INSTALL ------------------------------------------------------------

echo
echo "Device: ${PITFT_VALUES[$PITFT_SELECT-1]}"
echo "HDMI framebuffer rotate: ${FBROTATE_VALUES[$FBROTATE_SELECT-1]}"
echo "TFT MADCTL rotate: ${TFTROTATE_VALUES[$TFTROTATE_SELECT-1]}"
echo
echo -n "CONTINUE? [y/N] "
read
if [[ ! "$REPLY" =~ ^(yes|y|Y)$ ]]; then
	echo "Canceled."
	exit 0
fi

# All selections are validated at this point...
# *_SELECT variables will have numeric index of 1+

echo
echo "Starting installation..."
echo "Updating package index files..."
apt-get update

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

# FBCP INSTALL -------------------------------------------------------------

echo "Downloading and installing fbcp..."
apt-get --yes --force-yes install cmake
cd /tmp
curl -LO https://github.com/tasanakorn/rpi-fbcp/archive/master.zip
unzip master.zip
cd rpi-fbcp-master
mkdir build
cd build
cmake ..
make
install fbcp /usr/local/bin/fbcp
cd ../..
rm -rf rpi-fbcp-master

# Add fbcp to /rc.local:
grep fbcp /etc/rc.local >/dev/null
if [ $? -eq 0 ]; then
	# fbcp already in rc.local, but make sure correct:
	sed -i "s/^.*fbcp.*$/\/usr\/local\/bin\/fbcp \&/g" /etc/rc.local >/dev/null
else
	# Insert fbcp into rc.local before final 'exit 0'
sed -i "s/^exit 0/\/usr\/local\/bin\/fbcp \&\\nexit 0/g" /etc/rc.local >/dev/null
fi

# PITFT SETUP (/boot/config.txt mostly) ------------------------------------

echo "Configuring PiTFT..."

# Enable SPI using raspi-config
raspi-config nonint do_spi 0

# Set up PiTFT device tree overlay
reconfig /boot/config.txt "^.*dtoverlay=pitft.*$" "dtoverlay=${PITFT_VALUES[PITFT_SELECT-1]},rotate=${TFTROTATE_VALUES[TFTROTATE_SELECT-1]},speed=${HZ_VALUES[PITFT_SELECT-1]},fps=60"

# Set up framebuffer rotation
reconfig /boot/config.txt "^.*display_rotate.*$" "display_rotate=${FBROTATE_VALUES[FBROTATE_SELECT-1]}"

# Disable overscan compensation (use full screen):
raspi-config nonint do_overscan 1
# Set up HDMI parameters:
reconfig /boot/config.txt "^.*hdmi_force_hotplug.*$" "hdmi_force_hotplug=1"
reconfig /boot/config.txt "^.*hdmi_group.*$" "hdmi_group=2"
reconfig /boot/config.txt "^.*hdmi_mode.*$" "hdmi_mode=87"
reconfig /boot/config.txt "^.*hdmi_cvt.*$" "hdmi_cvt=${WIDTH_VALUES[PITFT_SELECT-1]} ${HEIGHT_VALUES[PITFT_SELECT-1]} 60 1 0 0 0"

# Use smaller console font:
reconfig /etc/default/console-setup "^.*FONTFACE.*$" "FONTFACE=\"Terminus\""
reconfig /etc/default/console-setup "^.*FONTSIZE.*$" "FONTSIZE=\"6x12\""

# Enable Retropie video smoothing
reconfig /opt/retropie/configs/all/retroarch.cfg "^.*video_smooth.*$" "video_smooth = \"true\""

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
