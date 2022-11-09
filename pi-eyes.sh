#!/bin/bash

if [ $(id -u) -ne 0 ]; then
  echo "Installer must be run as root."
  echo "Try 'sudo bash $0'"
  exit 1
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

clear

echo "This script installs Adafruit Snake Eyes Bonnet"
echo "software for Raspberry Pi. It's best to dedicate"
echo "a card to this, not for systems in regular use."
echo
echo "Target system (may be different than current host):"
selectN "Raspberry Pi 4, Pi 400, or Compute Module 4" "All other models"
#if [[ $? -eq "1" ]]; then
if [ $? -eq "1" ]; then
  IS_PI4=1
fi

if [ $IS_PI4 ]; then
  # Verify this is Raspbian Desktop OS (X11 should exist)
  if [ ! -d "/usr/bin/X11" ]; then
    echo "Target system is Pi 4/400/CM4 but this appears to"
    echo "be a \"Lite\" OS. \"Desktop\" OS is required."
    echo -n "Continue anyway? [y/N]"
    read
    if [[ ! "$REPLY" =~ ^(yes|y|Y)$ ]]; then
      echo "Canceled."
      exit 0
    fi
  fi
else
  # Verify this is Raspbian Lite OS (X11 should NOT exist)
  if [ -d "/usr/bin/X11" ]; then
    echo "Target system is not Pi 4/400/CM4 yet this appears to"
    echo "be a \"Desktop\" OS. \"Lite\" OS (Legacy) is required."
    echo -n "Continue anyway? [y/N]"
    read
    if [[ ! "$REPLY" =~ ^(yes|y|Y)$ ]]; then
      echo "Canceled."
      exit 0
    fi
  fi
fi

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

echo -n "Install Bonnet ADC support? [y/N] "
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
echo "Bonnet ADC support: ${OPTION_NAMES[$INSTALL_ADC]}"
echo "Ethernet USB gadget support: ${OPTION_NAMES[$INSTALL_GADGET]}"
if [ $SCREEN_SELECT -eq 3 ]; then
  echo "Video resolution will be set to 1280x720, no overscan"
else
  echo "Video resolution will be set to 640x480, no overscan"
fi

echo
echo "Installation steps include:"
echo "- Update package index files (apt-get update)"
echo "- Install Python libraries: numpy, pi3d, svg.path,"
echo "  rpi-gpio, python3-dev, python3-pil"
echo "- Install Adafruit eye code and data in /boot"
echo "- Set HDMI resolution, GPU RAM, disable overscan"
if [ $IS_PI4 ]; then
	echo "- Disable desktop, configure video driver"
fi
echo "- Enable SPI0 and SPI1 peripherals if needed"
echo
echo "THIS IS A ONE-WAY OPERATION, NO UNINSTALL PROVIDED."
echo "EXISTING INSTALLATION, IF ANY, WILL BE OVERWRITTEN."
echo "Run time ~10 minutes. Reboot required."
echo
echo -n "Do you understand and want to proceed? [y/N]"
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
# WAS: apt-get install -y --force-yes python-pip python-dev python-imaging python-smbus
apt-get install -y python3-pip python3-dev python3-pil python3-smbus libatlas-base-dev
# WAS: pip3 install numpy pi3d==2.34 svg.path rpi-gpio adafruit-ads1x15
pip3 install numpy pi3d svg.path rpi-gpio adafruit-blinka adafruit-circuitpython-ads1x15
# smbus and Blinka+ADC libs are installed regardless whether ADC is
# enabled; simplifies the Python code a little (no "uncomment this")

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

if [ $IS_PI4 ]; then
  # Make desktop system to boot to console (from raspi-config script):
  systemctl set-default multi-user.target
  ln -fs /lib/systemd/system/getty@.service /etc/systemd/system/getty.target.wants/getty@tty1.service
  rm -f /etc/systemd/system/getty@tty1.service.d/autologin.conf

  # Pi3D requires "fake" KMS overlay to work. Check /boot/config.txt for
  # vc4-fkms-v3d overlay present and active. If so, nothing to do here,
  # module's already configured.
  grep '^dtoverlay=vc4-fkms-v3d' /boot/config.txt >/dev/null
  if [ $? -ne 0 ]; then
    # fkms overlay not present, or is commented out. Check if vc4-kms-v3d
    # (no 'f') is present and active. That's normally the default.
    grep '^dtoverlay=vc4-kms-v3d' /boot/config.txt >/dev/null
    if [ $? -eq 0 ]; then
      # It IS present. Comment out that line for posterity, and insert the
      # 'fkms' item on the next line.
      sed -i "s/^dtoverlay=vc4-kms-v3d/#&\ndtoverlay=vc4-fkms-v3d/g" /boot/config.txt >/dev/null
    else
      # It's NOT present. Silently append 'fkms' overlay to end of file.
      echo dtoverlay=vc4-fkms-v3d | sudo tee -a /boot/config.txt >/dev/null
    fi
  fi

  # Disable screen blanking in X config
  echo "Section \"ServerFlags\"
  Option \"BlankTime\" \"0\"
  Option \"StandbyTime\" \"0\"
  Option \"SuspendTime\" \"0\"
  Option \"OffTime\" \"0\"
  Option \"dpms\" \"false\"
EndSection" > /etc/X11/xorg.conf

fi

# Disable overscan compensation (use full screen):
raspi-config nonint do_overscan 1

# Dedicate 128 MB to the GPU:
sudo raspi-config nonint do_memory_split 128

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
    if [ $IS_PI4 ]; then
      sed -i "s/^.*eyes.py.*$/cd \/boot\/Pi_Eyes;xinit \/usr\/bin\/python3 eyes.py --radius $RADIUS \:0 \&/g" /etc/rc.local >/dev/null
    else
      sed -i "s/^.*eyes.py.*$/cd \/boot\/Pi_Eyes;python3 eyes.py --radius $RADIUS \&/g" /etc/rc.local >/dev/null
    fi
  else
    # Insert eyes.py into rc.local before final 'exit 0'
    if [ $IS_PI4 ]; then
      sed -i "s/^exit 0/cd \/boot\/Pi_Eyes;xinit \/usr\/bin\/python3 eyes.py --radius $RADIUS \:0 \&\\nexit 0/g" /etc/rc.local >/dev/null
    else
      sed -i "s/^exit 0/cd \/boot\/Pi_Eyes;python3 eyes.py --radius $RADIUS \&\\nexit 0/g" /etc/rc.local >/dev/null
    fi
  fi

else

  # Auto-start cyclops.py on boot
  grep cyclops.py /etc/rc.local >/dev/null
  if [ $? -eq 0 ]; then
    # cyclops.py already in rc.local, but make sure correct:
    if [ $IS_PI4 ]; then
      sed -i "s/^.*cyclops.py.*$/cd \/boot\/Pi_Eyes;xinit \/usr\/bin\/python3 cyclops.py \:0 \&/g" /etc/rc.local >/dev/null
    else
      sed -i "s/^.*cyclops.py.*$/cd \/boot\/Pi_Eyes;python3 cyclops.py \&/g" /etc/rc.local >/dev/null
    fi
  else
    # Insert cyclops.py into rc.local before final 'exit 0'
    if [ $IS_PI4 ]; then
      sed -i "s/^exit 0/cd \/boot\/Pi_Eyes;xinit \/usr\/bin\/python3 cyclops.py \:0 \&\\nexit 0/g" /etc/rc.local >/dev/null
    else
      sed -i "s/^exit 0/cd \/boot\/Pi_Eyes;python3 cyclops.py \&\\nexit 0/g" /etc/rc.local >/dev/null
    fi
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
