#!/usr/bin/env bash

set -o xtrace
set -o errexit
set -o pipefail
set -o nounset

if [[ $EUID -ne 0 ]]; then
   echo "This script must be run as root (use sudo)" 1>&2
   exit 1
fi

if [ ! -f /etc/rpi-issue ]; then
  echo "Sorry, this drivers only works on raspberry pi"
  exit 1
fi


#download the archive
rm -rf WM8960-Audio-HAT
git clone https://github.com/waveshare/WM8960-Audio-HAT
cd WM8960-Audio-HAT

apt-get -y update
apt-get -y install raspberrypi-kernel-headers --no-install-recommends --no-install-suggests
apt-get -y install dkms git i2c-tools libasound2-plugins --no-install-recommends --no-install-suggests
apt-get -y clean

# locate currently installed kernels (may be different to running kernel if
# it's just been updated)
kernels=$(ls /lib/modules)

function install_module {
  ver="1.0"
  # we create a dir with this version to ensure that 'dkms remove' won't delete
  # the sources during kernel updates
  marker="0.0.0"

  src=$1
  mod=$2

  if [[ -d /var/lib/dkms/$mod/$ver/$marker ]]; then
    rmdir /var/lib/dkms/$mod/$ver/$marker
  fi

  if [[ -e /usr/src/$mod-$ver || -e /var/lib/dkms/$mod/$ver ]]; then
    dkms remove --force -m $mod -v $ver --all || true
    rm -rf /usr/src/$mod-$ver
  fi
  mkdir -p /usr/src/$mod-$ver
  cp -a $src/* /usr/src/$mod-$ver/
  dkms add -m $mod -v $ver
  for kernel in $kernels
  do
    # It works for kernels greater than or equal 6.5
    if [ $(echo "$kernel 6.5" | awk '{if ($1 >= $2) print 1; else print 0}') -eq 0 ]; then
      continue
    fi
    dkms build "$kernel" -k "$kernel" --kernelsourcedir "/lib/modules/$kernel/build" -m $mod -v $ver &&
      dkms install --force "$kernel" -k "$kernel" -m $mod -v $ver
  done

  mkdir -p /var/lib/dkms/$mod/$ver/$marker
}

install_module "./" "wm8960-soundcard"

# install dtbos
cp wm8960-soundcard.dtbo /boot/overlays


#set kernel modules
grep -q "^i2c-dev$" /etc/modules || \
  echo "i2c-dev" >> /etc/modules  
grep -q "^snd-soc-wm8960$" /etc/modules || \
  echo "snd-soc-wm8960" >> /etc/modules  
grep -q "^snd-soc-wm8960-soundcard$" /etc/modules || \
  echo "snd-soc-wm8960-soundcard" >> /etc/modules  

# set modprobe blacklist
grep -q "^blacklist snd_bcm2835$" /etc/modprobe.d/raspi-blacklist.conf || \
  echo "blacklist snd_bcm2835" >> /etc/modprobe.d/raspi-blacklist.conf
  
#set dtoverlays
sed -i -e 's:#dtparam=i2s=on:dtparam=i2s=on:g'  /boot/firmware/config.txt || true
sed -i -e 's:#dtparam=i2c_arm=on:dtparam=i2c_arm=on:g'  /boot/firmware/config.txt || true
grep -q "^dtoverlay=i2s-mmap$" /boot/firmware/config.txt || \
  echo "dtoverlay=i2s-mmap" >> /boot/firmware/config.txt

grep -q "^dtparam=i2s=on$" /boot/firmware/config.txt || \
  echo "dtparam=i2s=on" >> /boot/firmware/config.txt

grep -q "^dtoverlay=wm8960-soundcard$" /boot/firmware/config.txt || \
  echo "dtoverlay=wm8960-soundcard" >> /boot/firmware/config.txt
  
#install config files
mkdir -p /etc/wm8960-soundcard
cp *.conf /etc/wm8960-soundcard
cp *.state /etc/wm8960-soundcard

#set service 
cp wm8960-soundcard /usr/bin/
chmod -x wm8960-soundcard.service
cp wm8960-soundcard.service /lib/systemd/system/
systemctl enable wm8960-soundcard.service 

#cleanup
cd ..
rm -rf WM8960-Audio-HAT

echo "------------------------------------------------------"
echo "Please reboot your raspberry pi to apply all settings"
echo "Enjoy!"
echo "------------------------------------------------------"
