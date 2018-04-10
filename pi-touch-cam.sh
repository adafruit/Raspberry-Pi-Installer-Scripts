#!/bin/bash

if [ $(id -u) -ne 0 ]; then
	echo "Installer must be run as root."
	echo "Try 'sudo bash $0'"
	exit 1
fi

clear
echo "This script will install and/or modify"
echo "packages needed for the Adafruit Pi"
echo "Camera project. It requires that the"
echo "adafruit-pitft.sh installer script (for"
echo "PiTFT display support) was run first."
echo
echo "Operations performed include:"
echo "- In /boot/config.txt, enable camera"
echo "- apt-get update"
echo "- Install Python libraries:"
echo "  picamera, pygame, PIL"
echo "- Downgrade SDL library for pygame"
echo "  touch compatibility"
echo "- Download Dropbox Updater and"
echo "  Adafruit Pi Cam software"
echo
echo "Run time 5+ minutes. Reboot required."
echo

if [ "$1" != '-y' ]; then
	echo -n "CONTINUE? [y/N]"
	read
	if [[ ! "$REPLY" =~ ^(yes|y|Y)$ ]]; then
		echo "Canceled."
		exit 0
	fi
fi

echo "Continuing..."

if ! grep -q "dtoverlay=pitft" /boot/config.txt ; then
	echo "PiTFT overlay not in /boot/config.txt."
	echo "Download & run adafruit-pitft.sh first."
	echo "Canceling."
	exit 1
fi

echo "Configuring camera + PiTFT settings..."

# Set PiTFT speed to 80 MHz, 60 Hz
sed -i 's/speed=.*,fps=.*/speed=80000000,fps=60/g' /boot/config.txt

# Check if Pi camera is enabled. If not, add it...
if ! grep -q "^start_x=" /boot/config.txt ; then
	# start_x (camera) line not present, add it
	echo "start_x=1" >> /boot/config.txt
else
	# start_x exists, make sure it's set to 1
	sed -i 's/^start_x=.*/start_x=1/g' /boot/config.txt
fi

# gpu_mem must be >= 128 MB for camera to work
NUMBER=$(grep "^gpu_mem=" /boot/config.txt | sed 's/[^0-9]*//g')
if [ -z $NUMBER ]; then
	# gpu_mem isn't set. Add to config
	echo "gpu_mem=128" >> /boot/config.txt
elif [ $NUMBER -lt 128 ] ; then
	# gpu_mem present but too small; increase to 128MB
	sed -i 's/^gpu_mem=.*/gpu_mem=128/g' /boot/config.txt
fi # else gpu_mem OK as-is

echo "Installing prerequisite packages..."

# Enable Wheezy package sources (for SDL downgrade)
echo "deb http://archive.raspbian.org/raspbian wheezy main
" > /etc/apt/sources.list.d/wheezy.list
 
# Set 'stable' as default package source (current OS)
echo "APT::Default-release \"stable\";
" > /etc/apt/apt.conf.d/10defaultRelease

# Set priority for libsdl from Wheezy higher than current package
echo "Package: libsdl1.2debian
Pin: release n=stretch
Pin-Priority: -10
Pin: release n=jessie
Pin-Priority: -10
Package: libsdl1.2debian
Pin: release n=wheezy
Pin-Priority: 900
" > /etc/apt/preferences.d/libsdl

# Update the APT package index files, install Python libraries
sudo apt-get update
sudo apt-get -y --force-yes install python-picamera python-pygame python-imaging

echo "Downgrading SDL library..."

apt-get -y --force-yes install libsdl1.2debian/wheezy
 
echo "Downloading Dropbox uploader and"
echo "Adafruit Pi Cam to home directory..."

cd ~pi
wget https://github.com/andreafabrizi/Dropbox-Uploader/archive/master.zip
unzip master.zip
rm master.zip
mv Dropbox-Uploader-master Dropbox-Uploader

wget https://github.com/adafruit/adafruit-pi-cam/archive/master.zip
unzip master.zip
rm master.zip

chown -R pi:pi Dropbox-Uploader adafruit-pi-cam-master

# Add lines to /etc/rc.local (commented out by default):
sed -i 's/^exit 0/# Enable this line to run camera at startup:\n# cd \/home\/pi\/adafruit-pi-cam-master ; sudo python cam.py\n\nexit 0/g' /etc/rc.local
# Prompt to reboot!

echo
echo "Camera and PiTFT settings won't take"
echo "effect until next boot."
echo
echo -n "REBOOT NOW? [y/N]"
read
if [[ ! "$REPLY" =~ ^(yes|y|Y)$ ]]; then
	echo "Exiting without reboot."
	exit 0
fi
echo "Reboot started..."
reboot
