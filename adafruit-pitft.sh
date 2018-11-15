#!/bin/bash

# Instructions!
# cd ~
# wget https://raw.githubusercontent.com/adafruit/Raspberry-Pi-Installer-Scripts/master/adafruit-pitft.sh
# chmod +x adafruit-pitft.sh
# sudo ./adafruit-pitft.sh

if [ $(id -u) -ne 0 ]; then
	echo "Installer must be run as root."
	echo "Try 'sudo bash $0'"
	exit 1
fi


UPDATE_DB=false


############################ CALIBRATIONS ############################
# For TSLib
POINTERCAL_28r0="4232 11 -879396 1 5786 -752768 65536"
POINTERCAL_28r90="33 -5782 21364572 4221 35 -1006432 65536"
POINTERCAL_28r180="-4273 61 16441290 4 -5772 21627524 65536"
POINTERCAL_28r270="-9 5786 -784608 -4302 19 16620508 65536"

POINTERCAL_35r0="5724 -6 -1330074 26 8427 -1034528 65536"
POINTERCAL_35r90="5 8425 -978304 -5747 61 22119468 65536"
POINTERCAL_35r180="-5682 -1 22069150 13 -8452 32437698 65536"
POINTERCAL_35r270="3 -8466 32440206 5703 -1 -1308696 65536"

POINTERCAL_28c="320 65536 0 -65536 0 15728640 65536"

# for PIXEL desktop
TRANSFORM_28r0="0.988809 -0.023645 0.060523 -0.028817 1.003935 0.034176 0 0 1"
TRANSFORM_28r90="0.014773 -1.132874 1.033662 1.118701 0.009656 -0.065273 0 0 1"
TRANSFORM_28r180="-1.115235 -0.010589 1.057967 -0.005964 -1.107968 1.025780 0 0 1"
TRANSFORM_28r270="-0.033192 1.126869 -0.014114 -1.115846 0.006580 1.050030 0 0 1"

TRANSFORM_35r0="-1.098388 0.003455 1.052099 0.005512 -1.093095 1.026309 0 0 1"
TRANSFORM_35r90="-0.000087 1.094214 -0.028826 -1.091711 -0.004364 1.057821 0 0 1"
TRANSFORM_35r180="1.102807 0.000030 -0.066352 0.001374 1.085417 -0.027208 0 0 1"
TRANSFORM_35r270="0.003893 -1.087542 1.025913 1.084281 0.008762 -0.060700 0 0 1"

TRANSFORM_28c0="-1 0 1 0 -1 1 0 0 1"
TRANSFORM_28c90="0 1 0 -1 0 1 0 0 1"
TRANSFORM_28c180="1 0 0 0 1 0 0 0 1"
TRANSFORM_28c270="0 -1 1 1 0 0 0 0 1"


warning() { 
	echo WARNING : $1
}

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


function print_version() {
    echo "Adafruit PiTFT Helper v2.0.0"
    exit 1
}

function print_help() {
    echo "Usage: $0 "
    echo "    -h            Print this help"
    echo "    -v            Print version information"
    echo "    -u [homedir]  Specify path of primary user's home directory (defaults to /home/pi)"
    exit 1
}

group=ADAFRUIT
function info() {
    system="$1"
    group="${system}"
    shift
    FG="1;32m"
    BG="40m"
    echo -e "[\033[${FG}\033[${BG}${system}\033[0m] $*"
}

function bail() {
    FG="1;31m"
    BG="40m"
    echo -en "[\033[${FG}\033[${BG}${group}\033[0m] "
    if [ -z "$1" ]; then
        echo "Exiting due to error"
    else
        echo "Exiting due to error: $*"
    fi
    exit 1
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

function has_repo() {
    # Checks for the right raspbian repository
    # http://mirrordirector.raspbian.org/raspbian/ stretch main contrib non-free rpi firmware
    if [[ $(grep -h ^deb /etc/apt/sources.list /etc/apt/sources.list.d/* | grep "mirrordirector.raspbian.org") ]]; then
        return 0
    else
        return 1
    fi
}

progress() {
    count=0
    until [ $count -eq $1 ]; do
        echo -n "..." && sleep 1
        ((count++))
    done
    echo
}

sysupdate() {
    if ! $UPDATE_DB; then
	# echo "Checking for correct software repositories..."
	# has_repo || { warning "Missing Apt repo, please add deb http://mirrordirector.raspbian.org/raspbian/ stretch main contrib non-free rpi firmware to /etc/apt/sources.list.d/raspi.list" && exit 1; }
        echo "Updating apt indexes..." && progress 3 &
        sudo apt-get update 1> /dev/null || { warning "Apt failed to update indexes!" && exit 1; }
        echo "Reading package lists..."
        progress 3 && UPDATE_DB=true
    fi
}


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


############################ Sub-Scripts ############################

function softwareinstall() {
    echo "Installing Pre-requisite Software...This may take a few minutes!"
    apt-get install -y bc fbi git python-dev python-pip python-smbus python-spidev evtest tslib libts-bin 1> /dev/null  || { warning "Apt failed to install software!" && exit 1; }
    pip install evdev 1> /dev/null  || { warning "Pip failed to install software!" && exit 1; }
}

# update /boot/config.txt with appropriate values
function update_configtxt() {
    if grep -q "adafruit-pitft-helper" "/boot/config.txt"; then
        echo "Already have an adafruit-pitft-helper section in /boot/config.txt."
	echo "Removing old section..."
        cp /boot/config.txt /boot/configtxt.bak
	sed -i -e "/^# --- added by adafruit-pitft-helper/,/^# --- end adafruit-pitft-helper/d" /boot/config.txt
    fi

    if [ "${pitfttype}" == "22" ]; then
        overlay="dtoverlay=pitft22,rotate=${pitftrot},speed=64000000,fps=30"
    fi

    if [ "${pitfttype}" == "28r" ]; then
        overlay="dtoverlay=pitft28-resistive,rotate=${pitftrot},speed=64000000,fps=30"
    fi

    if [ "${pitfttype}" == "28c" ]; then
        overlay="dtoverlay=pitft28-capacitive,rotate=${pitftrot},speed=64000000,fps=30"
    fi

    if [ "${pitfttype}" == "35r" ]; then
        overlay="dtoverlay=pitft35-resistive,rotate=${pitftrot},speed=20000000,fps=20"
    fi


    date=`date`

    cat >> /boot/config.txt <<EOF
# --- added by adafruit-pitft-helper $date ---
dtparam=spi=on
dtparam=i2c1=on
dtparam=i2c_arm=on
$overlay
# --- end adafruit-pitft-helper $date ---
EOF
}

function update_udev() {
    cat > /etc/udev/rules.d/95-touchmouse.rules <<EOF
SUBSYSTEM=="input", ATTRS{name}=="touchmouse", ENV{DEVNAME}=="*event*", SYMLINK+="input/touchscreen"
EOF
    cat > /etc/udev/rules.d/95-ftcaptouch.rules <<EOF
SUBSYSTEM=="input", ATTRS{name}=="EP0110M09", ENV{DEVNAME}=="*event*", SYMLINK+="input/touchscreen"
EOF
    cat > /etc/udev/rules.d/95-stmpe.rules <<EOF
SUBSYSTEM=="input", ATTRS{name}=="*stmpe*", ENV{DEVNAME}=="*event*", SYMLINK+="input/touchscreen"
EOF
}


function update_pointercal() {
    if [ "${pitfttype}" == "28r" ] || [ "${pitfttype}" == "35r" ]; then
       echo $(eval echo "\$POINTERCAL_$pitfttype$pitftrot") > /etc/pointercal
    fi

    if [ "${pitfttype}" == "28c" ]; then
       echo $(eval echo "\$POINTERCAL_$pitfttype") > /etc/pointercal
    fi
}


function install_console() {
    echo "Set up main console turn on"
    if ! grep -q 'fbcon=map:10 fbcon=font:VGA8x8' /boot/cmdline.txt; then
        echo "Updating /boot/cmdline.txt"
        sed -i 's/rootwait/rootwait fbcon=map:10 fbcon=font:VGA8x8/g' "/boot/cmdline.txt"
    else
        echo "/boot/cmdline.txt already updated"
    fi

    echo "Turning off console blanking"
    # pre-stretch this is what you'd do:
    if [ -e /etc/kbd/config ]; then
      sed -i 's/BLANK_TIME=.*/BLANK_TIME=0/g' "/etc/kbd/config"
    fi
    # as of stretch....
    # removing any old version
    sed -i -e '/^# disable console blanking.*/d' /etc/rc.local
    sed -i -e '/^sudo sh -c "TERM=linux setterm -blank.*/d' /etc/rc.local
    sed -i -e "s|^exit 0|# disable console blanking on PiTFT\\nsudo sh -c \"TERM=linux setterm -blank 0 >/dev/tty0\"\\nexit 0|" /etc/rc.local

    reconfig /etc/default/console-setup "^.*FONTFACE.*$" "FONTFACE=\"Terminus\""
    reconfig /etc/default/console-setup "^.*FONTSIZE.*$" "FONTSIZE=\"6x12\""

    echo "Setting raspi-config to boot to console w/o login..."
    (cd "$target_homedir" && raspi-config nonint do_boot_behaviour B2)

    # remove fbcp
    sed -i -e "/^.*fbcp.*$/d" /etc/rc.local
}


function uninstall_console() {
    echo "Removing console fbcon map from /boot/cmdline.txt"
    sed -i 's/rootwait fbcon=map:10 fbcon=font:VGA8x8/rootwait/g' "/boot/cmdline.txt"
    echo "Screen blanking time reset to 10 minutes"
    if [ -e "/etc/kbd/config" ]; then
      sed -i 's/BLANK_TIME=0/BLANK_TIME=10/g' "/etc/kbd/config"
    fi
    sed -i -e '/^# disable console blanking.*/d' /etc/rc.local
    sed -i -e '/^sudo sh -c "TERM=linux.*/d' /etc/rc.local
}

function install_fbcp() {
    echo "Installing cmake..."
    apt-get --yes --force-yes install cmake 1> /dev/null  || { warning "Apt failed to install software!" && exit 1; }
    echo "Downloading rpi-fbcp..."
    cd /tmp
    #curl -sLO https://github.com/tasanakorn/rpi-fbcp/archive/master.zip
    curl -sLO https://github.com/adafruit/rpi-fbcp/archive/master.zip
    echo "Uncompressing rpi-fbcp..."
    rm -rf /tmp/rpi-fbcp-master
    unzip master.zip 1> /dev/null  || { warning "Failed to uncompress fbcp!" && exit 1; }
    cd rpi-fbcp-master
    mkdir build
    cd build
    echo "Building rpi-fbcp..."
    echo -e "\nset (CMAKE_C_FLAGS \"-std=gnu99 ${CMAKE_C_FLAGS}\")" >> ../CMakeLists.txt
    cmake ..  1> /dev/null  || { warning "Failed to cmake fbcp!" && exit 1; }
    make  1> /dev/null  || { warning "Failed to make fbcp!" && exit 1; }
    echo "Installing rpi-fbcp..."
    install fbcp /usr/local/bin/fbcp
    cd ~
    rm -rf /tmp/rpi-fbcp-master

    # Start fbcp in the appropriate place, depending on init system:
    if [ "$SYSTEMD" == "0" ]; then
        # Add fbcp to /etc/rc.local:
        echo "We have sysvinit, so add fbcp to /etc/rc.local..."
        grep fbcp /etc/rc.local >/dev/null
        if [ $? -eq 0 ]; then
            # fbcp already in rc.local, but make sure correct:
            sed -i "s|^.*fbcp.*$|/usr/local/bin/fbcp \&|g" /etc/rc.local >/dev/null
        else
            # Insert fbcp into rc.local before final 'exit 0':
            sed -i "s|^exit 0|/usr/local/bin/fbcp \&\\nexit 0|g" /etc/rc.local >/dev/null
        fi
    else
        # Install fbcp systemd unit, first making sure it's not in rc.local:
        uninstall_fbcp_rclocal
        echo "We have systemd, so install fbcp systemd unit..."
        install_fbcp_unit || bail "Unable to install fbcp unit file"
        sudo systemctl enable fbcp.service
    fi

    # if there's X11 installed...
    if [ -e /etc/lightdm ]; then
	echo "Setting raspi-config to boot to desktop w/o login..."
	raspi-config nonint do_boot_behaviour B4
    fi

    # Disable overscan compensation (use full screen):
    raspi-config nonint do_overscan 1
    # Set up HDMI parameters:
    echo "Configuring boot/config.txt for forced HDMI"
    reconfig /boot/config.txt "^.*hdmi_force_hotplug.*$" "hdmi_force_hotplug=1"
    reconfig /boot/config.txt "^.*hdmi_group.*$" "hdmi_group=2"
    reconfig /boot/config.txt "^.*hdmi_mode.*$" "hdmi_mode=87"

    # if there's X11 installed...
    if [ -e /etc/lightdm ]; then
	if [ "${pitfttype}" == "35r" ]; then
	    echo "Using x1.5 resolution"
	    SCALE=1.5
	else
	    echo "Using x2 resolution"
	    SCALE=2.0
	fi
    else
	echo "Using native resolution"
	SCALE=1
    fi
    WIDTH=`python -c "print(int(${WIDTH_VALUES[PITFT_SELECT-1]} * ${SCALE}))"`
    HEIGHT=`python -c "print(int(${HEIGHT_VALUES[PITFT_SELECT-1]} * ${SCALE}))"`
    reconfig /boot/config.txt "^.*hdmi_cvt.*$" "hdmi_cvt=${WIDTH} ${HEIGHT} 60 1 0 0 0"

    if [ "${pitftrot}" == "90" ] || [ "${pitftrot}" == "270" ]; then
	# dont rotate HDMI on 90 or 270
	reconfig /boot/config.txt "^.*display_hdmi_rotate.*$" ""
    fi

    if [ "${pitftrot}" == "0" ]; then
	reconfig /boot/config.txt "^.*display_hdmi_rotate.*$" "display_hdmi_rotate=1"
	# this is a hack but because we rotate HDMI we have to 'unrotate' the TFT!
	pitftrot=90
	update_configtxt || bail "Unable to update /boot/config.txt"
	pitftrot=0
    fi
    if [ "${pitftrot}" == "180" ]; then
	reconfig /boot/config.txt "^.*display_hdmi_rotate.*$" "display_hdmi_rotate=3"
	# this is a hack but because we rotate HDMI we have to 'unrotate' the TFT!
	pitftrot=90
	update_configtxt || bail "Unable to update /boot/config.txt"
	pitftrot=180
    fi

}

function install_fbcp_unit() {
    cat > /etc/systemd/system/fbcp.service <<EOF
[Unit]
Description=Framebuffer copy utility for PiTFT
After=network.target

[Service]
Type=simple
ExecStart=/usr/local/bin/fbcp

[Install]
WantedBy=multi-user.target
EOF
}

function uninstall_fbcp() {
    uninstall_fbcp_rclocal
    # Enable overscan compensation
    raspi-config nonint do_overscan 0
    # Set up HDMI parameters:
    echo "Configuring boot/config.txt for default HDMI"
    reconfig /boot/config.txt "^.*hdmi_force_hotplug.*$" "hdmi_force_hotplug=0"
    sed -i -e '/^hdmi_group=2.*$/d' /boot/config.txt
    sed -i -e '/^hdmi_mode=87.*$/d' /boot/config.txt
    sed -i -e '/^hdmi_cvt=.*$/d' /boot/config.txt
}

function uninstall_fbcp_rclocal() {
    # Remove fbcp from /etc/rc.local:
    echo "Remove fbcp from /etc/rc.local, if it's there..."
    sed -i -e '/^.*fbcp.*$/d' /etc/rc.local
}

function update_xorg() {
    if [ "${pitfttype}" == "28r" ] || [ "${pitfttype}" == "35r" ]; then
	matrix=$(eval echo "\$TRANSFORM_$pitfttype$pitftrot")
	transform="Option \"TransformationMatrix\" \"${matrix}\""
        cat > /usr/share/X11/xorg.conf.d/20-calibration.conf <<EOF
Section "InputClass"
        Identifier "STMPE Touchscreen Calibration"
        MatchProduct "stmpe"
        MatchDevicePath "/dev/input/event*"
        Driver "libinput"
        ${transform}
EndSection
EOF
    fi

    if [ "${pitfttype}" == "28c" ]; then
	matrix=$(eval echo "\$TRANSFORM_$pitfttype$pitftrot")
	transform="Option \"TransformationMatrix\" \"${matrix}\""
        cat > /usr/share/X11/xorg.conf.d/20-calibration.conf <<EOF
Section "InputClass"
        Identifier "FocalTech Touchscreen Calibration"
        MatchProduct "EP0110M09"
        MatchDevicePath "/dev/input/event*"
        Driver "libinput"
        ${transform}
EndSection
EOF
    fi
}

####################################################### MAIN
target_homedir="/home/pi"


clear
echo "This script downloads and installs"
echo "PiTFT Support using userspace touch"
echo "controls and a DTO for display drawing."
echo "one of several configuration files."
echo "Run time of up to 5 minutes. Reboot required!"
echo

echo "Select configuration:"
selectN "PiTFT 2.4\", 2.8\" or 3.2\" resistive (240x320)" \
        "PiTFT 2.2\" no touch (240x320)" \
        "PiTFT 2.8\" capacitive touch (240x320)" \
        "PiTFT 3.5\" resistive touch (320x480)" \
        "Quit without installing"
PITFT_SELECT=$?
if [ $PITFT_SELECT -gt 4 ]; then
    exit 1
fi

echo "Select rotation:"
selectN "90 degrees (landscape)" \
        "180 degrees (portait)" \
        "270 degrees (landscape)" \
        "0 degrees (portait)"
PITFT_ROTATE=$?
if [ $PITFT_ROTATE -gt 4 ]; then
    exit 1
fi

PITFT_ROTATIONS=("90" "180" "270" "0")
PITFT_TYPES=("28r" "22" "28c" "35r")
WIDTH_VALUES=(320 320 320 480)
HEIGHT_VALUES=(240 240 240 320)
HZ_VALUES=(64000000 64000000 64000000 32000000)



args=$(getopt -uo 'hvri:o:b:u:' -- $*)
[ $? != 0 ] && print_help
set -- $args

for i
do
    case "$i"
    in
        -h)
            print_help
            ;;
        -v)
            print_version
            ;;
        -u)
            target_homedir="$2"
            echo "Homedir = ${2}"
            shift
            shift
            ;;
    esac
done

# check init system (technique borrowed from raspi-config):
info PITFT 'Checking init system...'
if command -v systemctl > /dev/null && systemctl | grep -q '\-\.mount'; then
  echo "Found systemd"
  SYSTEMD=1
elif [ -f /etc/init.d/cron ] && [ ! -h /etc/init.d/cron ]; then
  echo "Found sysvinit"
  SYSTEMD=0
else
  bail "Unrecognised init system"
fi

if grep -q boot /proc/mounts; then
    echo "/boot is mounted"
else
    echo "/boot must be mounted. if you think it's not, quit here and try: sudo mount /dev/mmcblk0p1 /boot"
    if ask "Continue?"; then
        echo "Proceeding."
    else
        bail "Aborting."
    fi
fi

if [[ ! -e "$target_homedir" || ! -d "$target_homedir" ]]; then
    bail "$target_homedir must be an existing directory (use -u /home/foo to specify)"
fi

pitfttype=${PITFT_TYPES[$PITFT_SELECT-1]}
pitftrot=${PITFT_ROTATIONS[$PITFT_ROTATE-1]}


if [ "${pitfttype}" != "28r" ] && [ "${pitfttype}" != "28c" ] && [ "${pitfttype}" != "35r" ] && [ "${pitfttype}" != "22" ]; then
    echo "Type must be one of:"
    echo "  '28r' (2.8\" resistive, PID 1601)"
    echo "  '28c' (2.8\" capacitive, PID 1983)"
    echo "  '35r' (3.5\" Resistive)"
    echo "  '22'  (2.2\" no touch)"
    echo
    print_help
fi

info PITFT "System update"
sysupdate || bail "Unable to apt-get update"

info PITFT "Installing Python libraries & Software..."
softwareinstall || bail "Unable to install software"

info PITFT "Updating /boot/config.txt..."
update_configtxt || bail "Unable to update /boot/config.txt"

if [ "${pitfttype}" == "28r" ] || [ "${pitfttype}" == "35r" ]  || [ "${pitfttype}" == "28c" ] ; then
   info PITFT "Updating SysFS rules for Touchscreen..."
   update_udev || bail "Unable to update /etc/udev/rules.d"

   info PITFT "Updating TSLib default calibration..."
   update_pointercal || bail "Unable to update /etc/pointercal"
fi

# ask for console access
if ask "Would you like the console to appear on the PiTFT display?"; then
    info PITFT "Updating console to PiTFT..."
    uninstall_fbcp  || bail "Unable to uninstall fbcp"
    install_console || bail "Unable to configure console"
else
    info PITFT "Making sure console doesn't use PiTFT"
    uninstall_console || bail "Unable to configure console"

    if ask "Would you like the HDMI display to mirror to the PiTFT display?"; then
	info PITFT "Adding FBCP support..."
	install_fbcp || bail "Unable to configure fbcp"

	if [ -e /etc/lightdm ]; then
	    info PITFT "Updating X11 default calibration..."
	    update_xorg || bail "Unable to update calibration"
	fi
    fi
fi


#info PITFT "Updating X11 setup tweaks..."
#update_x11profile || bail "Unable to update X11 setup"

#if [ "${pitfttype}" != "35r" ]; then
#    # ask for 'on/off' button
#    if ask "Would you like GPIO #23 to act as a on/off button?"; then
#        info PITFT "Adding GPIO #23 on/off to PiTFT..."
#        install_onoffbutton || bail "Unable to add on/off button"
#    fi
#fi

# update_bootprefs || bail "Unable to set boot preferences"


info PITFT "Success!"
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
