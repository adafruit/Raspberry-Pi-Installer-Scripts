"""
THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES
OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT
HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY,
WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR
OTHER DEALINGS IN THE SOFTWARE.

This script is licensed under the terms of the MIT license.
Unless otherwise noted, code reproduced herein
was written for this script.

- The Pimoroni Crew - (modified by Adafruit!)
"""

from adafruit_shell import Shell

# script control variables
productname = "i2s amplifier" # the name of the product to install
spacereq = 1 # minimum size required on root partition in MB
debugmode = False # whether the script should use debug routines
debuguser = "none" # optional test git user to use in debug mode
debugpoint = "none" # optional git repo branch or tag to checkout
forcesudo = False # whether the script requires to be ran with root privileges
promptreboot = False # whether the script should always prompt user to reboot
mininstall = False # whether the script enforces minimum install routine
customcmd = True # whether to execute commands specified before exit
armhfonly = True # whether the script is allowed to run on other arch
armv6 = True # whether armv6 processors are supported
armv7 = True # whether armv7 processors are supported
armv8 = True # whether armv8 processors are supported
raspbianonly = False # whether the script is allowed to run on other OSes
osreleases = ("Raspbian", ) # list os-releases supported
oswarning = ("Debian", "Kano", "Mate", "PiTop", "Ubuntu") # list experimental os-releases
osdeny = ("Darwin", "Kali") # list os-releases specifically disallowed

ASK_TO_REBOOT = False
CURRENT_SETTING = False
UPDATE_DB = False

BOOTCMD = "/boot/cmdline.txt"
CONFIG = "/boot/config.txt"
APTSRC = "/etc/apt/sources.list"
INITABCONF = "/etc/inittab"
BLACKLIST = "/etc/modprobe.d/raspi-blacklist.conf"
LOADMOD = "/etc/modules"
DTBODIR = "/boot/overlays"


# function definitons
success() {
    echo -e "$(tput setaf 2)$1$(tput sgr0)"
}

inform() {
    echo -e "$(tput setaf 6)$1$(tput sgr0)"
}

warning() {
    echo -e "$(tput setaf 1)$1$(tput sgr0)"
}

newline() {
    echo ""
}

progress() {
    count=0
    until [ $count -eq $1 ]; do
        echo -n "..." && sleep 1
        ((count++))
    done
    echo
}

def sysclean():
    shell.run_command("sudo apt-get clean && sudo apt-get autoclean")
    shell.run_command("sudo apt-get -y autoremove &> /dev/null")

def sysupdate():
    # TO DO: Finish pythonizing
    if not UPDATE_DB:
        echo "Updating apt indexes..." && progress 3 &
        sudo apt-get update 1> /dev/null || { warning "Apt failed to update indexes!" && exit 1; }
        echo "Reading package lists..."
        progress 3 && UPDATE_DB = True

sysupgrade() {
    sudo apt-get upgrade
    sudo apt-get clean && sudo apt-get autoclean
    sudo apt-get -y autoremove &> /dev/null
}

sysreboot() {
    warning "Some changes made to your system require"
    warning "your computer to reboot to take effect."
    newline
    if prompt "Would you like to reboot now?"; then
        sync && sudo reboot
    fi
}

def arch_check():
    IS_ARMv6 = shell.is_armhf() and shell.get_arch() == "armv6l"

def os_check():
    os = shell.get_os()
    if os == "Raspbian":
        IS_RASPBIAN = True
    if os in os_releases:
        IS_SUPPORTED = True
    elif os in oswarning:
        IS_EXPERIMENTAL = True
    elif os in osdeny:
        IS_SUPPORTED = False
    if os == "Darwin":
        IS_MACOSX = True

def raspbian_check():
    release = shell.get_raspbian_version()
    
    if release in ("unstable", "buster", "stretch"):
        return (False, True)
    if release in ("jessie", "wheezy"):
        return (True, False)
    return (False, False)

def main():
    """
    Perform all global variables declarations as well as function definition
    above this section for clarity, thanks!
    """

    # checks and init
    IS_RASPBIAN = False
    IS_MACOSX = False
    IS_SUPPORTED = False
    IS_EXPERIMENTAL = False

    arch_check
    os_check

    if debugmode:
        print("""USER_HOME is {}

IS_RASPBIAN is {}
IS_MACOSX is {}
IS_SUPPORTED is {}
IS_EXPERIMENTAL is {}

""".format(shell.home_dir(), IS_RASPBIAN, IS_MACOSX, IS_SUPPORTED, IS_EXPERIMENTAL))

    if not shell.is_armhf():
        shell.bail("""This hardware is not supported, sorry!
Config files have been left untouched
""")

    if shell.is_armv8() and armv8 == False:
        shell.bail("Sorry, your CPU is not supported by this installer")
    if shell.is_armv7() and armv7 == False:
        shell.bail("Sorry, your CPU is not supported by this installer")
    if shell.is_armv6() and armv6 == False:
        shell.bail("Sorry, your CPU is not supported by this installer")

    if raspbianonly and not IS_RASPBIAN:
        shell.bail("This script is intended for Raspbian on a Raspberry Pi!")

    if IS_RASPBIAN:
        (supported, experimental) = raspbian_check()
        if not supported and not experimental:
            newline && warning "--- Warning ---" && newline
            echo "The $productname installer"
            echo "does not work on this version of Raspbian."
            echo "Check https://github.com/$gitusername/$gitreponame"
            echo "for additional information and support"
            newline && exit 1

    if not IS_SUPPORTED && not IS_EXPERIMENTAL:
            shell.bail("Your operating system is not supported, sorry!")

    if IS_EXPERIMENTAL:
        warning "Support for your operating system is experimental. Please visit"
        warning "forums.adafruit.com if you experience issues with this product."
        newline

    if forcesudo:
        shell.require_root()

    print("""

This script will install everything needed to use
{}

warning "--- Warning ---"

Always be careful when running scripts and commands
copied from the internet. Ensure they are from a
trusted source.

If you want to see what this script does before
running it, you should run:
    \curl -sS github.com/adafruit/Raspberry-Pi-Installer-Scripts/{}

""".format(productname, shell.script()))

    if shell.prompt("Do you wish to continue?", force_arg="y"):
        print("\nChecking hardware requirements...")

        if shell.exists(CONFIG) and shell.grep("^device_tree=$", CONFIG):
            print("\nAdding Device Tree Entry to {}".format($CONFIG))

            if shell.exists(CONFIG) and shell.grep("^dtoverlay=hifiberry-dac$", CONFIG):
                print("dtoverlay already active")
            else:
                shell.write_text_file(CONFIG, "dtoverlay=hifiberry-dac")
                ASK_TO_REBOOT = True

            if shell.exists(CONFIG) &&  and shell.grep("^dtoverlay=i2s-mmap$", CONFIG):
                print("i2s mmap dtoverlay already active")
            else:
                shell.write_text_file(CONFIG, "dtoverlay=i2s-mmap")
                ASK_TO_REBOOT = True

            if shell.exists(BLACKLIST):
                print("\nCommenting out Blacklist entry in {}".format(BLACKLIST))
                sudo sed -i -e "s|^blacklist[[:space:]]*i2c-bcm2708.*|#blacklist i2c-bcm2708|" \
                            -e "s|^blacklist[[:space:]]*snd-soc-pcm512x.*|#blacklist snd-soc-pcm512x|" \
                            -e "s|^blacklist[[:space:]]*snd-soc-wm8804.*|#blacklist snd-soc-wm8804|" $BLACKLIST &> /dev/null
        else:
            shell.bail("\nNo Device Tree Detected, not supported\n")

        if [ -e $CONFIG ] && grep -q -E "^dtparam=audio=on$" $CONFIG; then
            bcm2835off="no"
            newline
            echo "Disabling default sound driver"
            sudo sed -i "s|^dtparam=audio=on$|#dtparam=audio=on|" $CONFIG &> /dev/null
            if [ -e $LOADMOD ] && grep -q "^snd-bcm2835" $LOADMOD; then
                sudo sed -i "s|^snd-bcm2835|#snd-bcm2835|" $LOADMOD &> /dev/null
            fi
            ASK_TO_REBOOT=true
        elif [ -e $LOADMOD ] && grep -q "^snd-bcm2835" $LOADMOD; then
            bcm2835off="no"
            newline
            echo "Disabling default sound module"
            sudo sed -i "s|^snd-bcm2835|#snd-bcm2835|" $LOADMOD &> /dev/null
            ASK_TO_REBOOT=true
        else
            newline
            echo "Default sound driver currently not loaded"
            bcm2835off="yes"
        fi

        echo "Configuring sound output"
        if [ -e /etc/asound.conf ]; then
            shell.remove("/etc/asound.conf.old")
            shell.run_command("sudo mv /etc/asound.conf /etc/asound.conf.old")
        fi
        shell.write_text_file("~/asound.conf", """
pcm.speakerbonnet {
   type hw card 0
}

pcm.dmixer {
   type dmix
   ipc_key 1024
   ipc_perm 0666
   slave {
     pcm "speakerbonnet"
     period_time 0
     period_size 1024
     buffer_size 8192
     rate 44100
     channels 2
   }
}

ctl.dmixer {
    type hw card 0
}

pcm.softvol {
    type softvol
    slave.pcm "dmixer"
    control.name "PCM"
    control.card 0
}

ctl.softvol {
    type hw card 0
}

pcm.!default {
    type             plug
    slave.pcm       "softvol"
}
 """)

        shell.move("~/asound.conf", "/etc/asound.conf")

        print("\nInstalling aplay systemd unit")
        sudo sh -c 'cat > /etc/systemd/system/aplay.service' << 'EOL'
    [Unit]
    Description=Invoke aplay from /dev/zero at system start.

    [Service]
    ExecStart=/usr/bin/aplay -D default -t raw -r 44100 -c 2 -f S16_LE /dev/zero

    [Install]
    WantedBy=multi-user.target
    EOL

        sudo systemctl daemon-reload
        sudo systemctl disable aplay
        newline
        echo "You can optionally activate '/dev/zero' playback in"
        echo "the background at boot. This will remove all"
        echo "popping/clicking but does use some processor time."
        newline
        if confirm "Activate '/dev/zero' playback in background? [RECOMMENDED]"; then
        newline
        sudo systemctl enable aplay
        ASK_TO_REBOOT=true
        fi

        if [ $bcm2835off == "yes" ]; then
            newline
            echo "We can now test your $productname"
            warning "Set your speakers at a low volume if possible!"
            if confirm "Do you wish to test your system now?"; then
                echo "Testing..."
                speaker-test -l5 -c2 -t wav
            fi
        fi
        newline
        success "All done!"
        newline
        echo "Enjoy your new $productname!"
        newline

        if [ $promptreboot == "yes" ] || $ASK_TO_REBOOT; then
            sysreboot
        fi
    else
        newline
        echo "Aborting..."
        newline
    fi

    exit 0

# Main function
if __name__ == "__main__":
    if forcesudo:
        shell.require_root()
    main()
