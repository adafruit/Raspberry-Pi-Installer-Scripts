#!/bin/bash

# CREDIT TO THESE TUTORIALS:
# petr.io/en/blog/2015/11/09/read-only-raspberry-pi-with-jessie
# hallard.me/raspberry-pi-read-only
# k3a.me/how-to-make-raspberrypi-truly-read-only-reliable-and-trouble-free

if [ $(id -u) -ne 0 ]; then
	echo "Installer must be run as root."
	echo "Try 'sudo bash $0'"
	exit 1
fi

clear

echo "This script configures a Raspberry Pi"
echo "SD card to boot into read-only mode,"
echo "obviating need for clean shutdown."
echo "NO FILES ON THE CARD CAN BE CHANGED"
echo "WHEN PI IS BOOTED IN THIS STATE. Either"
echo "the filesystems must be remounted in"
echo "read/write mode, card must be mounted"
echo "R/W on another system, or an optional"
echo "jumper can be used to enable read/write"
echo "on boot."
echo
echo "Links to original tutorials are in"
echo "script source. THIS IS A ONE-WAY"
echo "OPERATION. THERE IS NO SCRIPT TO"
echo "REVERSE THIS SETUP! ALL other system"
echo "config should be complete before using"
echo "this script. MAKE A BACKUP FIRST."
echo
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

INSTALL_RW_JUMPER=0
INSTALL_HALT=0
INSTALL_WATCHDOG=0

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

SYS_TYPES=(Pi\ 3\ /\ Pi\ Zero\ W All\ other\ models)
WATCHDOG_MODULES=(bcm2835_wdog bcm2708_wdog)
OPTION_NAMES=(NO YES)

echo -n "Enable boot-time read/write jumper? [y/N] "
read
if [[ "$REPLY" =~ (yes|y|Y)$ ]]; then
	INSTALL_RW_JUMPER=1
	echo -n "GPIO pin for R/W jumper: "
	read
	RW_PIN=$REPLY
fi

echo -n "Install GPIO-halt utility? [y/N] "
read
if [[ "$REPLY" =~ (yes|y|Y)$ ]]; then
	INSTALL_HALT=1
	echo -n "GPIO pin for halt button: "
	read
	HALT_PIN=$REPLY
fi

echo -n "Enable kernel panic watchdog? [y/N] "
read
if [[ "$REPLY" =~ (yes|y|Y)$ ]]; then
	INSTALL_WATCHDOG=1
	echo "Target system type:"
	selectN "${SYS_TYPES[0]}" \
		"${SYS_TYPES[1]}"
	WD_TARGET=$?
fi

# VERIFY SELECTIONS BEFORE CONTINUING --------------------------------------

echo
if [ $INSTALL_RW_JUMPER -eq 1 ]; then
	echo "Boot-time R/W jumper: YES (GPIO$RW_PIN)"
else
	echo "Boot-time R/W jumper: NO"
fi
if [ $INSTALL_HALT -eq 1 ]; then
	echo "Install GPIO-halt: YES (GPIO$HALT_PIN)"
else
	echo "Install GPIO-halt: NO"
fi
if [ $INSTALL_WATCHDOG -eq 1 ]; then
	echo "Enable watchdog: YES (${SYS_TYPES[WD_TARGET-1]})"
else
	echo "Enable watchdog: NO"
fi
echo
echo -n "CONTINUE? [y/N] "
read
if [[ ! "$REPLY" =~ ^(yes|y|Y)$ ]]; then
	echo "Canceled."
	exit 0
fi

# START INSTALL ------------------------------------------------------------
# All selections have been validated at this point...

# Given a filename, a regex pattern to match and a replacement string:
# Replace string if found, else no change.
# (# $1 = filename, $2 = pattern to match, $3 = replacement)
replace() {
	grep $2 $1 >/dev/null
	if [ $? -eq 0 ]; then
		# Pattern found; replace in file
		sed -i "s/$2/$3/g" $1 >/dev/null
	fi
}

# Given a filename, a regex pattern to match and a replacement string:
# If found, perform replacement, else append file w/replacement on new line.
replaceAppend() {
	grep $2 $1 >/dev/null
	if [ $? -eq 0 ]; then
		# Pattern found; replace in file
		sed -i "s/$2/$3/g" $1 >/dev/null
	else
		# Not found; append on new line (silently)
		echo $3 | sudo tee -a $1 >/dev/null
	fi
}

# Given a filename, a regex pattern to match and a string:
# If found, no change, else append file with string on new line.
append1() {
	grep $2 $1 >/dev/null
	if [ $? -ne 0 ]; then
		# Not found; append on new line (silently)
		echo $3 | sudo tee -a $1 >/dev/null
	fi
}

# Given a filename, a regex pattern to match and a string:
# If found, no change, else append space + string to last line --
# this is used for the single-line /boot/cmdline.txt file.
append2() {
	grep $2 $1 >/dev/null
	if [ $? -ne 0 ]; then
		# Not found; insert in file before EOF
		sed -i "s/\'/ $3/g" $1 >/dev/null
	fi
}

echo
echo "Starting installation..."
echo "Updating package index files..."
apt-get update

echo "Removing unwanted packages..."
#apt-get remove -y --force-yes --purge triggerhappy cron logrotate dbus \
# dphys-swapfile xserver-common lightdm fake-hwclock
# Let's keep dbus...that includes avahi-daemon, a la 'raspberrypi.local',
# also keeping xserver & lightdm for GUI login (WIP, not working yet)
apt-get remove -y --force-yes --purge triggerhappy cron logrotate \
 dphys-swapfile fake-hwclock
apt-get -y --force-yes autoremove --purge

# Replace log management with busybox (use logread if needed)
echo "Installing busybox-syslogd..."
apt-get -y --force-yes install busybox-syslogd; dpkg --purge rsyslog

echo "Configuring system..."

# Install boot-time R/W jumper test if requested
GPIOTEST="gpio -g mode $RW_PIN up\n\
if [ \`gpio -g read $RW_PIN\` -eq 0 ] ; then\n\
\tmount -o remount,rw \/\n\
\tmount -o remount,rw \/boot\n\
fi\n"
if [ $INSTALL_RW_JUMPER -ne 0 ]; then
	apt-get install -y --force-yes wiringpi
	# Check if already present in rc.local:
	grep "gpio -g read" /etc/rc.local >/dev/null
	if [ $? -eq 0 ]; then
		# Already there, but make sure pin is correct:
		sed -i "s/^.*gpio\ -g\ read.*$/$GPIOTEST/g" /etc/rc.local >/dev/null

	else
		# Not there, insert before final 'exit 0'
		sed -i "s/^exit 0/$GPIOTEST\\nexit 0/g" /etc/rc.local >/dev/null
	fi
fi

# Install watchdog if requested
if [ $INSTALL_WATCHDOG -ne 0 ]; then
	apt-get install -y --force-yes watchdog
	# $MODULE is specific watchdog module name
	MODULE=${WATCHDOG_MODULES[($WD_TARGET-1)]}
	# Add to /etc/modules, update watchdog config file
	append1 /etc/modules $MODULE $MODULE
	replace /etc/watchdog.conf "#watchdog-device" "watchdog-device"
	replace /etc/watchdog.conf "#max-load-1" "max-load-1"
	# Start watchdog at system start and start right away
	# Raspbian Stretch needs this package installed first
	apt-get install -y --force-yes insserv
	insserv watchdog; /etc/init.d/watchdog start
	# Additional settings needed on Jessie
	append1 /lib/systemd/system/watchdog.service "WantedBy" "WantedBy=multi-user.target"
	systemctl enable watchdog
	# Set up automatic reboot in sysctl.conf
	replaceAppend /etc/sysctl.conf "^.*kernel.panic.*$" "kernel.panic = 10"
fi

# Install gpio-halt if requested
if [ $INSTALL_HALT -ne 0 ]; then
	apt-get install -y --force-yes wiringpi
	echo "Installing gpio-halt in /usr/local/bin..."
	cd /tmp
	curl -LO https://github.com/adafruit/Adafruit-GPIO-Halt/archive/master.zip
	unzip master.zip
	cd Adafruit-GPIO-Halt-master
	make
	mv gpio-halt /usr/local/bin
	cd ..
	rm -rf Adafruit-GPIO-Halt-master

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

# Add fastboot, noswap and/or ro to end of /boot/cmdline.txt
append2 /boot/cmdline.txt fastboot fastboot
append2 /boot/cmdline.txt noswap noswap
append2 /boot/cmdline.txt ro^o^t ro

# Move /var/spool to /tmp
rm -rf /var/spool
ln -s /tmp /var/spool

# Move /var/lib/lightdm and /var/cache/lightdm to /tmp
rm -rf /var/lib/lightdm
rm -rf /var/cache/lightdm
ln -s /tmp /var/lib/lightdm
ln -s /tmp /var/cache/lightdm

# Make SSH work
replaceAppend /etc/ssh/sshd_config "^.*UsePrivilegeSeparation.*$" "UsePrivilegeSeparation no"
# bbro method (not working in Jessie?):
#rmdir /var/run/sshd
#ln -s /tmp /var/run/sshd

# Change spool permissions in var.conf (rondie/Margaret fix)
replace /usr/lib/tmpfiles.d/var.conf "spool\s*0755" "spool 1777"

# Move dhcpd.resolv.conf to tmpfs
touch /tmp/dhcpcd.resolv.conf
rm /etc/resolv.conf
ln -s /tmp/dhcpcd.resolv.conf /etc/resolv.conf

# Make edits to fstab
# make / ro
# tmpfs /var/log tmpfs nodev,nosuid 0 0
# tmpfs /var/tmp tmpfs nodev,nosuid 0 0
# tmpfs /tmp     tmpfs nodev,nosuid 0 0
replace /etc/fstab "vfat\s*defaults\s" "vfat    defaults,ro "
replace /etc/fstab "ext4\s*defaults,noatime\s" "ext4    defaults,noatime,ro "
append1 /etc/fstab "/var/log" "tmpfs /var/log tmpfs nodev,nosuid 0 0"
append1 /etc/fstab "/var/tmp" "tmpfs /var/tmp tmpfs nodev,nosuid 0 0"
append1 /etc/fstab "\s/tmp"   "tmpfs /tmp    tmpfs nodev,nosuid 0 0"

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
