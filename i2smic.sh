#!/bin/bash
#-------------------------------------------------------------------------
# Installer script for I2S microphone support on Raspberry Pi
#
# 2020/04/15
#-------------------------------------------------------------------------

############################ Script assisters ############################

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

function ask() {
    # http://djm.me/ask
    while true; do

        if [ "${2:-}" = "Y" ]; then
            prompt="Y/n"
            default=Y
        elif [ "${2:-}" = "N" ]; then
            prompt="y/N"
            default=N
        else
            prompt="y/n"
            default=
        fi

        # Ask the question
        read -p "$1 [$prompt] " REPLY

        # Default?
        if [ -z "$REPLY" ]; then
            REPLY=$default
        fi

        # Check if the reply is valid
        case "$REPLY" in
            Y*|y*) return 0 ;;
            N*|n*) return 1 ;;
        esac
    done
}

####################################################### MAIN

clear
echo "This script downloads and installs"
echo "I2S microphone support."
echo

echo "Select Pi Model:"
selectN "Pi 0 or 0W" \
        "Pi 2 or 3" \
        "Pi 4"
PIMODEL_SELECT=$(($?-1))

ask "Auto load module at boot?"
AUTO_LOAD=$?

echo
echo "Installing..."

# System update and install
apt-get -y update
apt-get -y upgrade
apt-get -y install git dkms raspberrypi-kernel-headers

# Clone the repo
git clone https://github.com/adafruit/Raspberry-Pi-Installer-Scripts.git

# Install and build module
cd Raspberry-Pi-Installer-Scripts/i2s_mic_module
cp -R . /usr/src/snd-i2smic-rpi-0.1.0
dkms add -m snd-i2smic-rpi -v 0.1.0
dkms build -m snd-i2smic-rpi -v 0.1.0
dkms install -m snd-i2smic-rpi -v 0.1.0

# Setup auto load at boot if selected
if [ $AUTO_LOAD = 0 ]; then
  cat > /etc/modules-load.d/snd-i2smic-rpi.conf<<EOF
snd-i2smic-rpi
EOF
  cat > /etc/modprobe.d/snd-i2smic-rpi.conf<<EOF
options snd-i2smic-rpi rpi_platform_generation=$PIMODEL_SELECT
EOF
fi

# Enable I2S overlay
sed -i -e 's/#dtparam=i2s/dtparam=i2s/g' /boot/config.txt

# Done
echo "DONE."
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
