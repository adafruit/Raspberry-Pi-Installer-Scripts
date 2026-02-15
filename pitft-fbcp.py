import os

try:
    from adafruit_shell import Shell
except ImportError:
    raise RuntimeError("The library 'adafruit_shell' was not found. To install, try typing: pip3 install adafruit-python-shell")

shell = Shell()

# Check if adafruit-pitft.py is available, if not, we can't continue
if not shell.exists("adafruit-pitft.py"):
    raise RuntimeError("The script 'adafruit-pitft.py' was not found. Please ensure it is downloaded and in your current directory.")

__version__ = "1.0.0"

# Framebuffer (HDMI out) rotation:
HDMI_ROTATE_OPTIONS = [
    {"label": "Normal (landscape)", "value": 0},
    {"label": "90° clockwise (portrait)", "value": 1},
    {"label": "180° (landscape)", "value": 2},
    {"label": "90° counterclockwise (portrait)", "value": 3},
]

# PiTFT (MADCTL) rotation:
TFT_ROTATE_OPTIONS = [
    {"label": "0°", "value": "0"},
    {"label": "90°", "value": "90"},
    {"label": "180°", "value": "180"},
    {"label": "270°", "value": "270"},
]

# Display options with IDs corresponding to adafruit-pitft.py
config = [
    {
        "type": "pitft22",
        "pitft_id": "22",
        "label": "PiTFT 2.2\" HAT",
    },
    {
        "type": "pitft28-resistive",
        "pitft_id": "28r",
        "label": "PiTFT / PiTFT Plus resistive 2.4-3.2\"",
    },
    {
        "type": "pitft28-capacitive",
        "pitft_id": "28c",
        "label": "PiTFT / PiTFT Plus 2.8\" capacitive",
    },
    {
        "type": "pitft35-resistive",
        "pitft_id": "35r",
        "label": "PiTFT / PiTFT Plus 3.5\"",
    },
]

# Preconfigured Projects
projects = [
    {
        "label": "PiGRRL 2",
        "pitft_config": "pitft28-resistive",
        "fbrotate": 0,
        "tftrotate": "270",
    },
    {
        "label": "Pocket PiGRRL",
        "pitft_config": "pitft22",
        "fbrotate": 0,
        "tftrotate": "270",
    },
    {
        "label": "PiGRRL Zero",
        "pitft_config": "pitft22",
        "fbrotate": 0,
        "tftrotate": "270",
    },
    {
        "label": "Cupcade (horizontal screen)",
        "pitft_config": "pitft28-resistive",
        "fbrotate": 0,
        "tftrotate": "180",
    },
    {
        "label": "Cupcade (vertical screen)",
        "pitft_config": "pitft28-resistive",
        "fbrotate": 1,
        "tftrotate": "180",
    },
]

selected_config = None
selected_fbrotate = None
selected_tftrotate = None
boot_config = shell.get_boot_config()

def get_config_by_id(config_id):
    return next(item for item in config if item["type"] == config_id)

def get_hdmi_rotate_by_value(value):
    return next(item for item in HDMI_ROTATE_OPTIONS if item["value"] == value)

def get_tft_rotate_by_value(value):
    return next(item for item in TFT_ROTATE_OPTIONS if item["value"] == value)

def select_project(project_config):
    global selected_config, selected_fbrotate, selected_tftrotate
    selected_config = get_config_by_id(project_config["pitft_config"])
    selected_fbrotate = get_hdmi_rotate_by_value(project_config["fbrotate"])
    selected_tftrotate = get_tft_rotate_by_value(project_config["tftrotate"])

def main():
    global selected_config, selected_tftrotate, selected_fbrotate

    shell.clear()
    print("""This script enables basic PiTFT display
support for portable gaming, etc.  Does
not cover X11, touchscreen or buttons
(see adafruit-pitft-helper for those).
HDMI output is set to PiTFT resolution,
not all monitors support this, PiTFT
may be only display after reboot.
Run time ~5 minutes. Reboot required.
""")

    if not shell.prompt("CONTINUE?", default='n'):
        print("Canceled.")
        shell.exit()
    print("Continuing...")


    # FEATURE PROMPTS ----------------------------------------------------------
    # Installation doesn't begin until after all user input is taken.

    # Build menu from config
    selections = []
    for item in projects:
        selections.append(item['label'])
    selections.append("Configure options manually")
    selections.append("Quit without installing")

    project_selection = shell.select_n("Select project:", selections)
    if project_selection == len(projects) + 2:
        shell.exit(1)
    if project_selection <= len(projects):
        select_project(projects[project_selection - 1])
    else:
        # Manual configuration
        display_options = []
        for item in config:
            display_options.append(item['label'])
        selected_config = get_config_by_id(config[shell.select_n("Select display type:", display_options)]["type"])

        rotation_options = ["{}".format(x) for x in HDMI_ROTATE_OPTIONS]
        selected_fbrotate = HDMI_ROTATE_OPTIONS[shell.select_n("HDMI framebuffer rotation:", rotation_options)]

        tft_rotation_options = ["{}°".format(x) for x in TFT_ROTATE_OPTIONS]
        selected_tftrotate = TFT_ROTATE_OPTIONS[shell.select_n("TFT (MADCTL) rotation:", tft_rotation_options)]


    # START INSTALL ------------------------------------------------------------
    print(f"""
Device: {selected_config['label']}
HDMI framebuffer rotate: {selected_fbrotate['label']}
TFT MADCTL rotate: {selected_tftrotate['label']}

    """)
    if not shell.prompt("Continue?", default="n"):
        print("Canceled.")
        shell.exit()

    # All selections are validated at this point...
    # *_SELECT variables will have numeric index of 1+

    print("""
    Start installation...
    """)

    # Get the original username
    username = os.environ["SUDO_USER"]

    # We'll just call adafruit-pitft.py with the command options for future compatibility and run with sudo, but as the user
    shell.run_command(f"sudo -E env PATH=$PATH python3 adafruit-pitft.py --display {selected_config['pitft_id']} --rotation {selected_tftrotate['value']} --install-type mirror --reboot no", run_as_user=username)

    # PITFT SETUP ------------------------------------
    # Apply anything that is specific for the PiTFT

    print("Configuring PiTFT...")

    # Enable SPI using raspi-config
    shell.run_command("raspi-config nonint do_spi 0")

    # Set up HDMI rotation
    shell.reconfig(f"{boot_config}", "^.*display_rotate.*$", f"display_rotate={selected_fbrotate['value']}")

    # Use smaller console font (Terminus 6x12):
    shell.reconfig("/etc/default/console-setup", "^.*FONTFACE.*$", "FONTFACE=\"Terminus\"")
    shell.reconfig("/etc/default/console-setup", "^.*FONTSIZE.*$", "FONTSIZE=\"6x12\"")

    # Enable Retropie video smoothing
    if shell.exists("/opt/retropie/configs/all/retroarch.cfg"):
        shell.reconfig("/opt/retropie/configs/all/retroarch.cfg", "^.*video_smooth.*$", "video_smooth = \"true\"")
    else:
        shell.warn("RetroArch config not found, skipping video smoothing setup.")

    # PROMPT FOR REBOOT --------------------------------------------------------
    shell.prompt_reboot()

# Main function
if __name__ == "__main__":
    shell.require_root()
    main()