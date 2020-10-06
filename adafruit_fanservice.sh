#!/bin/bash

if [ $(id -u) -ne 0 ]; then
	echo "Installer must be run as root."
	echo "Try 'sudo bash $0'"
	exit 1
fi

clear
echo "This script will install Adafruit"
echo "fan service, which will turn on an"
echo "external fan controlled by a given pin"
echo
echo "Operations performed include:"
echo "- Create a Fan Service File"
echo "- Enable Fan Service"
echo "- Automatically Start Fan Service"
echo "  on System startup"
echo
echo "Run time < 1 minute. Reboot not required."
echo

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

if [ "$1" != '-y' ]; then
	echo -n "CONTINUE? [y/N]"
	read
	if [[ ! "$REPLY" =~ ^(yes|y|Y)$ ]]; then
		echo "Canceled."
		exit 0
	fi
fi

echo "Continuing..."
# check init system (technique borrowed from raspi-config):
info FAN 'Checking init system...'
if command -v systemctl > /dev/null && systemctl | grep -q '\-\.mount'; then
  echo "Found systemd, OK!"
elif [ -f /etc/init.d/cron ] && [ ! -h /etc/init.d/cron ]; then
  bail "Found sysvinit, but we require systemd"
else
  bail "Unrecognised init system"
fi

info FAN 'Adding adafruit_fan.service'
cat > /etc/systemd/system/adafruit_fan.service <<EOF
[Unit]
Description=Fan service for some Adafruit boards
After=network.target

[Service]
Type=oneshot
ExecStartPre=-/bin/bash -c 'echo 4 >/sys/class/gpio/export'
ExecStartPre=/bin/bash -c 'echo out >/sys/class/gpio/gpio4/direction'
ExecStart=/bin/bash -c 'echo 1 >/sys/class/gpio/gpio4/value'

RemainAfterExit=true
ExecStop=/bin/bash -c 'echo 0 >/sys/class/gpio/gpio4/value'
StandardOutput=journal

[Install]
WantedBy=multi-user.target
EOF

info FAN 'Enabling adafruit_fan.service'
sudo systemctl enable adafruit_fan.service
sudo systemctl start adafruit_fan.service
info FAN 'Done!'
echo "You can stop the fan service with 'sudo systemctl stop adafruit_fan.service'"
echo "You can start the fan service with 'sudo systemctl start adafruit_fan.service'"
