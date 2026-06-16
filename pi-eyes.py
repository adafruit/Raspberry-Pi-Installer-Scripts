# SPDX-FileCopyrightText: 2016 Phillip Burgess for Adafruit Industries
#
# SPDX-License-Identifier: MIT

# Adafruit Snake Eyes Bonnet installer for Raspberry Pi OS Trixie (Debian 13).
# Supports Pi 3B, Pi 4, and Pi 5.
#
# Notes:
#   - Targets Trixie; boot config at /boot/firmware (resolved via
#     shell.get_boot_config()).
#   - Does not touch the vc4-kms-v3d overlay (fkms was removed in Bookworm).
#   - Forces HDMI mode via video= kernel cmdline (works headless).
#   - pip installs into a dedicated venv at /opt/pi-eyes-venv (PEP 668).
#   - Code installed to /opt/Pi_Eyes.
#   - fbx2 uses X11 MIT-SHM capture and the Linux GPIO character device
#     (replaces dispmanx, removed in Bookworm; works on Pi 3B/4/5).
#   - Uses rpi-lgpio on Pi 5 (RP1 GPIO controller; RPi.GPIO not supported).
#   - Autostart via systemd units (rc.local is deprecated on Trixie).

import os

try:
    from adafruit_shell import Shell
except ImportError:
    raise RuntimeError(
        "The library 'adafruit_shell' was not found. To install, try typing: "
        "sudo pip3 install adafruit-python-shell"
    )

shell = Shell()
shell.group = "PI-EYES"

VENV = "/opt/pi-eyes-venv"
PI_EYES_DIR = "/opt/Pi_Eyes"

SCREEN_NAMES = (
    "OLED 128x128 (SSD1351)",
    "TFT 128x128 (ST7735)",
    "IPS 240x240 (ST7789)",
    "HDMI only (no SPI screens)",
)
SCREEN_OPTS = ("-o", "-t", "-i", "")
RADIUS_VALUES = (128, 128, 240, 240)


def append_to_line(path, pattern, addition):
    """Replace an existing `pattern` token on the (single-line) cmdline file,
    or append `addition` to the end of the first line if not present."""
    if shell.pattern_search(path, pattern):
        shell.pattern_replace(path, pattern, addition)
    else:
        contents = shell.read_text_file(path).rstrip("\n")
        shell.write_text_file(path, f"{contents} {addition}\n", append=False)


def main():
    shell.clear()

    pi_model = ""
    if os.path.exists("/proc/device-tree/model"):
        pi_model = shell.read_text_file("/proc/device-tree/model").replace("\x00", "")
    is_pi5 = "Raspberry Pi 5" in pi_model

    print("Adafruit Snake Eyes Bonnet installer")
    print("Raspberry Pi OS Trixie - Pi 3B / Pi 4 / Pi 5")
    print("")
    print(f"Running on: {pi_model}")
    print("")

    # FEATURE PROMPTS ------------------------------------------------------

    print("Select screen type:")
    screen_select = shell.select_n("Screen type:", SCREEN_NAMES) - 1
    screen_opt = SCREEN_OPTS[screen_select]
    radius = RADIUS_VALUES[screen_select]
    hdmi_only = screen_select == 3
    video_res = "1280x720" if screen_select == 2 else "640x480"

    install_halt = shell.prompt("Install GPIO-halt utility?", default="n")
    halt_pin = 21
    if install_halt:
        while True:
            halt_pin_input = input("GPIO pin for halt (BCM number): ").strip()
            if halt_pin_input.isdigit() and 0 <= int(halt_pin_input) <= 27:
                halt_pin = int(halt_pin_input)
                break
            print("Please enter a valid BCM GPIO number (0-27).")

    install_adc = shell.prompt("Install Bonnet ADC support?", default="n")
    install_gadget = shell.prompt(
        "Install USB Ethernet gadget support? (Pi Zero)", default="n"
    )

    print("")
    print("Summary:")
    print(f"  Screen:       {SCREEN_NAMES[screen_select]}")
    print(f"  Resolution:   {video_res}")
    print(f"  GPIO halt:    {f'YES, GPIO{halt_pin}' if install_halt else 'NO'}")
    print(f"  ADC support:  {'YES' if install_adc else 'NO'}")
    print(f"  USB gadget:   {'YES' if install_gadget else 'NO'}")
    print("")
    print("THIS IS A ONE-WAY OPERATION - NO UNINSTALL PROVIDED.")
    print("Run time ~10-15 minutes. Reboot required.")
    print("")
    if not shell.prompt("Proceed?", default="n"):
        print("Canceled.")
        shell.exit()

    boot_config = shell.get_boot_config()
    if boot_config is None:
        shell.bail("Could not find Raspberry Pi boot config (config.txt)")
    boot_dir = os.path.dirname(boot_config)
    cmdline = f"{boot_dir}/cmdline.txt"

    # PACKAGES -------------------------------------------------------------

    print("")
    print("Updating package index...")
    shell.run_command("apt-get update")

    print("Installing system packages...")
    shell.run_command(
        "apt-get install -y build-essential python3-venv python3-dev "
        "python3-full libx11-dev libxext-dev git curl unzip"
    )

    # Pi 5 uses the RP1 controller; RPi.GPIO does not support it. rpi-lgpio is
    # a drop-in replacement via lgpio.
    if is_pi5:
        print("Pi 5: installing rpi-lgpio (RP1 GPIO controller)...")
        shell.run_command(
            "apt-get install -y python3-lgpio python3-rpi-lgpio python3-smbus i2c-tools"
        )
    else:
        shell.run_command("apt-get install -y python3-rpi.gpio python3-smbus i2c-tools")

    # PYTHON VENV ----------------------------------------------------------

    print(f"Creating Python venv at {VENV}...")
    # --system-site-packages lets the venv see system gpio/smbus.
    shell.run_command(f"python3 -m venv --system-site-packages {VENV}")
    pip = f"{VENV}/bin/pip"
    shell.run_command(f"{pip} install --upgrade pip")

    print("Installing Python libraries...")
    shell.run_command(
        f"{pip} install numpy pi3d svg.path adafruit-blinka "
        "adafruit-circuitpython-ads1x15"
    )

    # PI_EYES CODE ---------------------------------------------------------

    print("Downloading Pi_Eyes...")
    shell.chdir("/tmp")
    shell.remove("master.zip")
    shell.remove("Pi_Eyes-master")
    shell.run_command(
        "curl -sLO https://github.com/adafruit/Pi_Eyes/archive/master.zip"
    )
    shell.run_command("unzip -q master.zip")
    shell.run_command(f"mkdir -p {PI_EYES_DIR}")
    shell.run_command(f"cp -r Pi_Eyes-master/. {PI_EYES_DIR}/")
    shell.remove("master.zip")
    shell.remove("Pi_Eyes-master")

    # Use a local fbx2.c (Trixie-compatible) if it sits next to this script.
    script_dir = os.path.dirname(os.path.abspath(__file__))
    local_fbx2 = os.path.join(script_dir, "fbx2.c")
    if os.path.exists(local_fbx2):
        print(f"Using local fbx2.c from {script_dir}...")
        shell.copy(local_fbx2, f"{PI_EYES_DIR}/fbx2.c")

    print("Compiling fbx2...")
    shell.chdir(PI_EYES_DIR)
    shell.run_command("gcc -O2 -o fbx2 fbx2.c -lpthread -lm -lX11 -lXext")
    shell.run_command("chmod +x fbx2")

    # GPIO HALT ------------------------------------------------------------

    if install_halt:
        print("Installing gpio-halt...")
        shell.chdir("/tmp")
        shell.remove("master.zip")
        shell.remove("Adafruit-GPIO-Halt-master")
        shell.run_command(
            "curl -sLO https://github.com/adafruit/Adafruit-GPIO-Halt/"
            "archive/master.zip"
        )
        shell.run_command("unzip -q master.zip")
        shell.chdir("Adafruit-GPIO-Halt-master")
        shell.run_command("make")
        shell.move("gpio-halt", "/usr/local/bin/")
        shell.chdir("/tmp")
        shell.remove("Adafruit-GPIO-Halt-master")
        shell.remove("master.zip")

    # BOOT CONFIGURATION ---------------------------------------------------

    print("Configuring system...")

    # Boot to console - eyes.py launches its own X via xinit.
    shell.run_command("systemctl set-default multi-user.target")
    shell.run_command(
        "ln -fs /lib/systemd/system/getty@.service "
        "/etc/systemd/system/getty.target.wants/getty@tty1.service"
    )
    shell.remove("/etc/systemd/system/getty@tty1.service.d/autologin.conf")

    # Disable X screen blanking.
    shell.run_command("mkdir -p /etc/X11")
    if video_res == "1280x720":
        modeline = (
            '    Modeline "1280x720" 74.25 1280 1390 1430 1650 '
            "720 725 730 750 +hsync +vsync"
        )
    else:
        modeline = (
            '    Modeline "640x480"  25.18  640  656  752  800 '
            "480 490 492 525 -hsync -vsync"
        )
    shell.write_text_file(
        "/etc/X11/xorg.conf",
        f"""Section "ServerFlags"
    Option "BlankTime"    "0"
    Option "StandbyTime"  "0"
    Option "SuspendTime"  "0"
    Option "OffTime"      "0"
    Option "dpms"         "false"
EndSection

Section "Monitor"
    Identifier "HDMI-1"
{modeline}
EndSection

Section "Screen"
    Identifier  "Screen0"
    Monitor     "HDMI-1"
    DefaultDepth 24
    SubSection "Display"
        Depth 24
        Modes "{video_res}"
    EndSubSection
EndSection
""",
        append=False,
    )

    # GPU memory (raspi-config do_memory_split was removed in Trixie).
    shell.reconfig(boot_config, "^.*gpu_mem.*$", "gpu_mem=128")

    # HDMI: force hotplug and a custom resolution. video= in cmdline forces
    # the mode at the KMS level and enables the connector even with no
    # physical display attached (the 'e' flag).
    shell.reconfig(boot_config, "^.*hdmi_force_hotplug.*$", "hdmi_force_hotplug=1")
    shell.reconfig(boot_config, "^.*hdmi_group.*$", "hdmi_group=2")
    shell.reconfig(boot_config, "^.*hdmi_mode.*$", "hdmi_mode=87")

    if video_res == "1280x720":
        shell.reconfig(boot_config, "^.*hdmi_cvt.*$", "hdmi_cvt=1280 720 60 1 0 0 0")
        append_to_line(cmdline, "video=HDMI-A-1:[^ ]*", "video=HDMI-A-1:1280x720@60e")
    else:
        shell.reconfig(boot_config, "^.*hdmi_cvt.*$", "hdmi_cvt=640 480 60 1 0 0 0")
        append_to_line(cmdline, "video=HDMI-A-1:[^ ]*", "video=HDMI-A-1:640x480@60e")

    # I2C for ADC.
    if install_adc:
        shell.run_raspi_config("do_i2c 0")

    # SPI for screen.
    if not hdmi_only:
        shell.run_raspi_config("do_spi 0")
        shell.reconfig(boot_config, "^.*dtparam=spi1.*$", "dtparam=spi1=on")
        shell.reconfig(boot_config, "^.*dtoverlay=spi1.*$", "dtoverlay=spi1-3cs")
        append_to_line(cmdline, "spidev\\.bufsiz=[^ ]*", "spidev.bufsiz=8192")

    # USB Ethernet gadget (Pi Zero).
    if install_gadget:
        shell.reconfig(boot_config, "^.*dtoverlay=dwc2.*$", "dtoverlay=dwc2")
        if not shell.pattern_search(cmdline, "modules-load=dwc2,g_ether"):
            shell.pattern_replace(
                cmdline, "rootwait", "rootwait modules-load=dwc2,g_ether"
            )

    # SYSTEMD SERVICES -----------------------------------------------------

    print("Creating systemd service units...")

    shell.run_command("mkdir -p /etc/pi-eyes")
    shell.write_text_file(
        "/etc/pi-eyes/env",
        f"PYTHON={VENV}/bin/python3\nPI_EYES_DIR={PI_EYES_DIR}\nRADIUS={radius}\n",
        append=False,
    )

    if not hdmi_only:
        # fbx2 copies the X display to the SPI screens. DISPLAY=:0 lets it
        # connect to the X server started by the pi-eyes service; After=
        # ensures eyes.py is up first.
        shell.write_text_file(
            "/etc/systemd/system/pi-eyes-fbx2.service",
            f"""[Unit]
Description=Pi Eyes SPI framebuffer copy (fbx2)
After=pi-eyes.service
Requires=pi-eyes.service
StartLimitIntervalSec=0

[Service]
Type=simple
Environment=DISPLAY=:0
EnvironmentFile=/etc/pi-eyes/env
ExecStartPre=/bin/sleep 5
ExecStart={PI_EYES_DIR}/fbx2 {screen_opt}
Restart=on-failure
RestartSec=3

[Install]
WantedBy=multi-user.target
""",
            append=False,
        )
        shell.run_command("systemctl enable pi-eyes-fbx2.service")

    # pi-eyes launches eyes.py (or cyclops.py) under its own X via xinit.
    eyes_cmd = "cyclops.py" if hdmi_only else "eyes.py --radius ${RADIUS}"
    shell.write_text_file(
        "/etc/systemd/system/pi-eyes.service",
        f"""[Unit]
Description=Pi Eyes animation
After=multi-user.target

[Service]
Type=simple
EnvironmentFile=/etc/pi-eyes/env
ExecStart=/bin/bash -c 'cd ${{PI_EYES_DIR}}; xinit ${{PYTHON}} {eyes_cmd} :0'
Restart=on-failure
RestartSec=3

[Install]
WantedBy=multi-user.target
""",
        append=False,
    )
    shell.run_command("systemctl enable pi-eyes.service")

    if install_halt:
        shell.write_text_file(
            "/etc/systemd/system/gpio-halt.service",
            f"""[Unit]
Description=GPIO halt button
After=multi-user.target

[Service]
Type=simple
ExecStart=/usr/local/bin/gpio-halt {halt_pin}
Restart=on-failure

[Install]
WantedBy=multi-user.target
""",
            append=False,
        )
        shell.run_command("systemctl enable gpio-halt.service")

    shell.run_command("systemctl daemon-reload")

    # DONE -----------------------------------------------------------------

    print("")
    print("============================================================")
    print("Installation complete.")
    print("")
    print(f"Boot config: {boot_config}")
    print(f"Eye code:    {PI_EYES_DIR}/")
    print(f"Python venv: {VENV}/")
    print("")
    print("Settings take effect on next boot.")
    print("")
    shell.prompt_reboot()


if __name__ == "__main__":
    shell.require_root()
    main()
