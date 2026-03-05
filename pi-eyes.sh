#!/bin/bash
# Adafruit Snake Eyes Bonnet installer for Raspberry Pi OS Trixie (Debian 13).
# Supports Pi 3B, Pi 4, and Pi 5.
#
# Changes vs upstream pi-eyes.sh:
#   - Targets Trixie only; drops Buster/Bullseye legacy paths
#   - Boot config always at /boot/firmware (Trixie standard)
#   - Does not touch vc4-kms-v3d overlay (fkms was removed in Bookworm)
#   - Forces HDMI mode via video= kernel cmdline (works headless)
#   - pip installs into Python venv (PEP 668 / externally-managed-env)
#   - Code installed to /opt/Pi_Eyes (not /boot — FAT32 partition)
#   - Uses local fbx2.c if present next to this script
#   - fbx2 uses X11 MIT-SHM capture (replaces dispmanx, removed in Bookworm)
#   - fbx2 uses Linux GPIO character device (works on Pi 3B, 4 and 5)
#   - Uses xinit to launch eyes.py (pi3d requires EGL; dispmanx is gone)
#   - Uses rpi-lgpio on Pi 5 (RP1 GPIO controller, RPi.GPIO not supported)
#   - Autostart via systemd units (rc.local is deprecated in Trixie)

if [ $(id -u) -ne 0 ]; then
    echo "Installer must be run as root."
    echo "Try 'sudo bash $0'"
    exit 1
fi

# Trixie always uses /boot/firmware
CONFIG_TXT=/boot/firmware/config.txt
CMDLINE_TXT=/boot/firmware/cmdline.txt

if [ ! -f "$CONFIG_TXT" ]; then
    echo "ERROR: $CONFIG_TXT not found."
    echo "This installer requires Raspberry Pi OS Trixie (Debian 13)."
    exit 1
fi

# Detect Pi 5 — uses RP1 GPIO controller, needs rpi-lgpio instead of RPi.GPIO
PI_MODEL=$(cat /proc/device-tree/model 2>/dev/null | tr -d '\0')
IS_PI5=0
echo "$PI_MODEL" | grep -q "Raspberry Pi 5" && IS_PI5=1

# ---- FEATURE PROMPTS --------------------------------------------------------

selectN() {
    for ((i=1; i<=$#; i++)); do
        echo "$i. ${!i}"
    done
    echo
    REPLY=""
    while :; do
        echo -n "SELECT 1-$#: "
        read
        if [[ $REPLY -ge 1 ]] && [[ $REPLY -le $# ]]; then
            return $REPLY
        fi
    done
}

clear

echo "Adafruit Snake Eyes Bonnet installer"
echo "Raspberry Pi OS Trixie — Pi 3B / Pi 4 / Pi 5"
echo
echo "Running on: $PI_MODEL"
echo

SCREEN_OPTS=("-o" "-t" "-i" "")
SCREEN_NAMES=("OLED 128x128 (SSD1351)" "TFT 128x128 (ST7735)" "IPS 240x240 (ST7789)" "HDMI only (no SPI screens)")
RADIUS_VALUES=(128 128 240 240)

echo "Select screen type:"
selectN "${SCREEN_NAMES[@]}"
SCREEN_SELECT=$?
SCREEN_OPT=${SCREEN_OPTS[$((SCREEN_SELECT-1))]}
RADIUS=${RADIUS_VALUES[$((SCREEN_SELECT-1))]}

if [ $SCREEN_SELECT -eq 3 ]; then
    VIDEO_RES="1280x720"
else
    VIDEO_RES="640x480"
fi

INSTALL_HALT=0
HALT_PIN=21
echo -n "Install GPIO-halt utility? [y/N] "
read
if [[ "$REPLY" =~ ^(yes|y|Y)$ ]]; then
    INSTALL_HALT=1
    echo -n "GPIO pin number for halt button: "
    read
    HALT_PIN=$REPLY
fi

INSTALL_ADC=0
echo -n "Install Bonnet ADC support? [y/N] "
read
[[ "$REPLY" =~ ^(yes|y|Y)$ ]] && INSTALL_ADC=1

INSTALL_GADGET=0
echo -n "Install USB Ethernet gadget support? (Pi Zero) [y/N] "
read
[[ "$REPLY" =~ ^(yes|y|Y)$ ]] && INSTALL_GADGET=1

echo
echo "Summary:"
echo "  Screen:       ${SCREEN_NAMES[$((SCREEN_SELECT-1))]}"
echo "  Resolution:   ${VIDEO_RES}"
echo "  GPIO halt:    $([ $INSTALL_HALT -eq 1 ] && echo YES, GPIO$HALT_PIN || echo NO)"
echo "  ADC support:  $([ $INSTALL_ADC  -eq 1 ] && echo YES || echo NO)"
echo "  USB gadget:   $([ $INSTALL_GADGET -eq 1 ] && echo YES || echo NO)"
echo
echo "THIS IS A ONE-WAY OPERATION — NO UNINSTALL PROVIDED."
echo "Run time ~10-15 minutes. Reboot required."
echo
echo -n "Proceed? [y/N] "
read
if [[ ! "$REPLY" =~ ^(yes|y|Y)$ ]]; then
    echo "Canceled."
    exit 0
fi

# ---- HELPERS ----------------------------------------------------------------

reconfig() {
    # Replace matching line or append. $1=file $2=pattern $3=replacement
    grep -E "$2" "$1" >/dev/null 2>&1 \
        && sed -i "s|$2|$3|g" "$1" \
        || echo "$3" | tee -a "$1" >/dev/null
}

reconfig2() {
    # Replace on existing line or append to end of first line. $1=file $2=pattern $3=replacement
    grep -E "$2" "$1" >/dev/null 2>&1 \
        && sed -i "s|$2|$3|g" "$1" \
        || sed -i "s|$| $3|" "$1"
}

# ---- PACKAGES ---------------------------------------------------------------

echo
echo "Updating package index..."
apt-get update

echo "Installing system packages..."
apt-get install -y \
    build-essential \
    python3-venv python3-dev python3-full \
    libx11-dev libxext-dev \
    git curl unzip

# Python GPIO library: Pi 5 uses the RP1 controller; RPi.GPIO does not
# support it. rpi-lgpio is a drop-in compatible replacement via lgpio.
if [ $IS_PI5 -eq 1 ]; then
    echo "Pi 5: installing rpi-lgpio (RP1 GPIO controller)..."
    apt-get install -y python3-lgpio python3-rpi-lgpio python3-smbus i2c-tools
else
    apt-get install -y python3-rpi.gpio python3-smbus i2c-tools
fi

# ---- PYTHON VENV ------------------------------------------------------------

echo "Creating Python venv at /opt/pi-eyes-venv..."
# --system-site-packages lets the venv see system gpio/smbus without re-installing
python3 -m venv --system-site-packages /opt/pi-eyes-venv
PIP=/opt/pi-eyes-venv/bin/pip
$PIP install --upgrade pip --quiet

echo "Installing Python libraries..."
$PIP install --quiet numpy pi3d svg.path adafruit-blinka \
    adafruit-circuitpython-ads1x15

# ---- PI_EYES CODE -----------------------------------------------------------

echo "Downloading Pi_Eyes..."
cd /tmp
rm -f master.zip
rm -rf Pi_Eyes-master
curl -sLO https://github.com/adafruit/Pi_Eyes/archive/master.zip
unzip -q master.zip
mkdir -p /opt/Pi_Eyes
cp -r Pi_Eyes-master/. /opt/Pi_Eyes/
rm -rf master.zip Pi_Eyes-master

# Use local fbx2.c (Trixie-compatible) if it sits next to this script
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
if [ -f "${SCRIPT_DIR}/fbx2.c" ]; then
    echo "Using local fbx2.c from ${SCRIPT_DIR}..."
    cp "${SCRIPT_DIR}/fbx2.c" /opt/Pi_Eyes/fbx2.c
fi

echo "Compiling fbx2..."
cd /opt/Pi_Eyes
gcc -O2 -o fbx2 fbx2.c -lpthread -lm -lX11 -lXext 2>&1 | head -20
chmod +x fbx2

# ---- GPIO HALT --------------------------------------------------------------

if [ $INSTALL_HALT -ne 0 ]; then
    echo "Installing gpio-halt..."
    cd /tmp
    rm -f master.zip
    rm -rf Adafruit-GPIO-Halt-master
    curl -sLO https://github.com/adafruit/Adafruit-GPIO-Halt/archive/master.zip
    unzip -q master.zip
    cd Adafruit-GPIO-Halt-master
    make
    mv gpio-halt /usr/local/bin/
    cd /tmp
    rm -rf Adafruit-GPIO-Halt-master
fi

# ---- BOOT CONFIGURATION -----------------------------------------------------

echo "Configuring system..."

# Boot to console — eyes.py launches its own X via xinit
systemctl set-default multi-user.target
ln -fs /lib/systemd/system/getty@.service \
    /etc/systemd/system/getty.target.wants/getty@tty1.service
rm -f /etc/systemd/system/getty@tty1.service.d/autologin.conf

# Do NOT modify the vc4 overlay. vc4-kms-v3d is correct for Trixie.
# vc4-fkms-v3d was removed in Bookworm and must not be added.

# Disable X screen blanking
mkdir -p /etc/X11
cat > /etc/X11/xorg.conf << XORGEOF
Section "ServerFlags"
    Option "BlankTime"    "0"
    Option "StandbyTime"  "0"
    Option "SuspendTime"  "0"
    Option "OffTime"      "0"
    Option "dpms"         "false"
EndSection

Section "Monitor"
    Identifier "HDMI-1"
$(if [ "$VIDEO_RES" = "1280x720" ]; then
    echo '    Modeline "1280x720" 74.25 1280 1390 1430 1650 720 725 730 750 +hsync +vsync'
else
    echo '    Modeline "640x480"  25.18  640  656  752  800 480 490 492 525 -hsync -vsync'
fi)
EndSection

Section "Screen"
    Identifier  "Screen0"
    Monitor     "HDMI-1"
    DefaultDepth 24
    SubSection "Display"
        Depth 24
        Modes "${VIDEO_RES}"
    EndSubSection
EndSection
XORGEOF

# GPU memory: set via config.txt directly (raspi-config do_memory_split
# was removed in Trixie's raspi-config)
reconfig "$CONFIG_TXT" "^.*gpu_mem.*$" "gpu_mem=128"

# HDMI config — force hotplug and custom resolution.
# video= in cmdline forces the mode at the KMS level and enables the
# connector even when no physical display is connected ('e' flag).
reconfig "$CONFIG_TXT" "^.*hdmi_force_hotplug.*$" "hdmi_force_hotplug=1"
reconfig "$CONFIG_TXT" "^.*hdmi_group.*$"          "hdmi_group=2"
reconfig "$CONFIG_TXT" "^.*hdmi_mode.*$"           "hdmi_mode=87"

if [ "$VIDEO_RES" = "1280x720" ]; then
    reconfig  "$CONFIG_TXT"  "^.*hdmi_cvt.*$" "hdmi_cvt=1280 720 60 1 0 0 0"
    reconfig2 "$CMDLINE_TXT" "video=HDMI-A-1:[^ ]*" "video=HDMI-A-1:1280x720@60e"
else
    reconfig  "$CONFIG_TXT"  "^.*hdmi_cvt.*$" "hdmi_cvt=640 480 60 1 0 0 0"
    reconfig2 "$CMDLINE_TXT" "video=HDMI-A-1:[^ ]*" "video=HDMI-A-1:640x480@60e"
fi

# I2C for ADC
[ $INSTALL_ADC -ne 0 ] && raspi-config nonint do_i2c 0

# SPI for screen
if [ $SCREEN_SELECT -ne 4 ]; then
    raspi-config nonint do_spi 0
    reconfig  "$CONFIG_TXT"  "^.*dtparam=spi1.*$"   "dtparam=spi1=on"
    reconfig  "$CONFIG_TXT"  "^.*dtoverlay=spi1.*$"  "dtoverlay=spi1-3cs"
    reconfig2 "$CMDLINE_TXT" "spidev\.bufsiz=[^ ]*"  "spidev.bufsiz=8192"
fi

# USB Ethernet gadget (Pi Zero)
if [ $INSTALL_GADGET -ne 0 ]; then
    reconfig "$CONFIG_TXT" "^.*dtoverlay=dwc2.*$" "dtoverlay=dwc2"
    grep "modules-load=dwc2,g_ether" "$CMDLINE_TXT" >/dev/null 2>&1 || \
        sed -i "s/rootwait/rootwait modules-load=dwc2,g_ether/g" "$CMDLINE_TXT"
fi

# ---- SYSTEMD SERVICES -------------------------------------------------------

echo "Creating systemd service units..."

mkdir -p /etc/pi-eyes
cat > /etc/pi-eyes/env << ENVEOF
PYTHON=/opt/pi-eyes-venv/bin/python3
PI_EYES_DIR=/opt/Pi_Eyes
RADIUS=${RADIUS}
ENVEOF

if [ $SCREEN_SELECT -ne 4 ]; then
    # fbx2: copies X display to SPI screens.
    # DISPLAY=:0 required so fbx2 can connect to the X server started by
    # the pi-eyes service.  After= ensures eyes.py is up before fbx2 runs.
    cat > /etc/systemd/system/pi-eyes-fbx2.service << EOF
[Unit]
Description=Pi Eyes SPI framebuffer copy (fbx2)
After=pi-eyes.service
Requires=pi-eyes.service
StartLimitIntervalSec=0

[Service]
Type=simple
Environment=DISPLAY=:0
EnvironmentFile=/etc/pi-eyes/env
ExecStartPre=/bin/sleep 5
ExecStart=/opt/Pi_Eyes/fbx2 ${SCREEN_OPT}
Restart=on-failure
RestartSec=3

[Install]
WantedBy=multi-user.target
EOF
    systemctl enable pi-eyes-fbx2.service
fi

# pi-eyes: launches eyes.py under its own X server via xinit.
# Requires Desktop OS (xinit pre-installed).
cat > /etc/systemd/system/pi-eyes.service << EOF
[Unit]
Description=Pi Eyes animation
After=multi-user.target

[Service]
Type=simple
EnvironmentFile=/etc/pi-eyes/env
ExecStart=/bin/bash -c 'cd \${PI_EYES_DIR}; xinit \${PYTHON} $([ $SCREEN_SELECT -eq 4 ] && echo cyclops.py || echo "eyes.py --radius \${RADIUS}") :0'
Restart=on-failure
RestartSec=3

[Install]
WantedBy=multi-user.target
EOF
systemctl enable pi-eyes.service

if [ $INSTALL_HALT -ne 0 ]; then
    cat > /etc/systemd/system/gpio-halt.service << EOF
[Unit]
Description=GPIO halt button
After=multi-user.target

[Service]
Type=simple
ExecStart=/usr/local/bin/gpio-halt ${HALT_PIN}
Restart=on-failure

[Install]
WantedBy=multi-user.target
EOF
    systemctl enable gpio-halt.service
fi

systemctl daemon-reload

# ---- DONE -------------------------------------------------------------------

echo
echo "============================================================"
echo "Installation complete."
echo
echo "Boot config: ${CONFIG_TXT}"
echo "Eye code:    /opt/Pi_Eyes/"
echo "Python venv: /opt/pi-eyes-venv/"
echo
echo "Settings take effect on next boot."
echo
echo -n "REBOOT NOW? [y/N] "
read
if [[ "$REPLY" =~ ^(yes|y|Y)$ ]]; then
    echo "Rebooting..."
    reboot
fi
exit 0
