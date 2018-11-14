#!/bin/sh

# Instructions!
# cd ~
# wget https://raw.githubusercontent.com/adafruit/Raspberry-Pi-Installer-Scripts/master/libgpiod.sh
# chmod +x libgpiod.sh
# ./adafruit-pitft.sh


echo "Installing build requirements - this may take a few minutes!"
echo

sudo apt-get update && sudo apt-get install -y \
   autoconf \
   autoconf-archive \
   automake \
   build-essential \
   git \
   libtool \
   pkg-config \
   python3 \
   python3-dev \
   python3-setuptools \
   raspberrypi-kernel-headers \
   swig3.0 \
   wget

build_dir=`mktemp -d /tmp/libgpiod.XXXX`
echo "Cloning libgpiod repository to $build_dir"
echo

cd "$build_dir"
git clone git://git.kernel.org/pub/scm/libs/libgpiod/libgpiod.git .

echo "Building libgpiod"
echo

include_path=`python3 -c "from sysconfig import get_paths; print(get_paths()['include'])"`

export PYTHON_VERSION=3
./autogen.sh --enable-tools=yes --prefix=/usr/local/ --enable-bindings-python CFLAGS="-I/$include_path" \
   && make \
   && sudo make install \
   && sudo ldconfig

# This is not the right way to do this:
sudo cp bindings/python/.libs/gpiod.so /usr/local/lib/python3.5/dist-packages/
sudo cp bindings/python/.libs/gpiod.la /usr/local/lib/python3.5/dist-packages/
sudo cp bindings/python/.libs/gpiod.a /usr/local/lib/python3.5/dist-packages/

exit 0
