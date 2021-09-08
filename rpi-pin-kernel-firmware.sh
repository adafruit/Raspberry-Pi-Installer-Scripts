#!/bin/sh
# rpi-pin-kernel-firmware: Pin a specific version of the rpi kernel and firmware

set -e

if [ $# -ne 1 ]; then
    echo "Usage: $0 kernel-version"
    echo
    echo "e.g., $0 1.20201126-1"
    exit 1
fi

if ! dpkg -l raspberrypi-kernel:armhf > /dev/null 2>&1; then
    echo "This command is designed to run only on Raspbian with the armhf kernel"
    echo 99
fi


if [ `id -u` -ne 0 ]; then
    echo "If necessary, enter your password to run this script as root"
    exec sudo sh "$0" "$1"
fi

version=$1
fileversion=$(echo $version | cut -d':' -f 2)
base=http://archive.raspberrypi.org/debian/pool/main/r/raspberrypi-firmware/
packagelist="libraspberrypi0 libraspberrypi-bin libraspberrypi-dev libraspberrypi-doc raspberrypi-bootloader raspberrypi-kernel raspberrypi-kernel-headers"

set --
for package in $packagelist; do
    filename="${package}_${fileversion}_armhf.deb"
    set -- "$@" "$filename"
    wget --continue -O "$filename" "$base/$filename"
done

dpkg -i "$@"

for package in $packagelist; do
    /usr/bin/printf "Package: $package\nPin: version ${version}\nPin-Priority:999\n\n"
done > /etc/apt/preferences.d/99-adafruit-pin-kernel
