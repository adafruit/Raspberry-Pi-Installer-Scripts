try:
    from clint.textui import prompt
except ImportError:
    raise RuntimeError("The library 'clint' was not found. To install, try typing: sudo pip3 install clint")
import sys
import os
import subprocess

def selectN(message, selections):
    """
    Display a list of selections for the user to enter
    """
    options = []
    
    for index, selection in enumerate(selections):
        options.append({
            'selector': str(index + 1),
            'prompt': selection,
            'return': index + 1,
        })
    return prompt.options(message, options)

def run_command(cmd, suppress_message = False):
    """
    Run a shell command and show the output as it runs
    """
    proc = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE)
    while True:
        output = proc.stdout.readline()
        if len(output) == 0 and proc.poll() is not None:
            break
        if output and not suppress_message:
            print(output.decode("utf-8").strip())
    r = proc.poll()
    if r == 0:
        return True
    else:
        err = proc.stderr.read()
        if not suppress_message:
            print(err.decode("utf-8"))
        return False

####################################################### MAIN
def main():
    os.system('clear')
    print("""This script downloads and installs
I2S microphone support.
""")
    pimodel_select = selectN("Select Pi Model:", ["Pi 0 or 0W", "Pi 2 or 3", "Pi 4"]) - 1

    auto_load = prompt.yn("Auto load module at boot?")

    print("""
Installing...""")

    # Get needed packages
    run_command("apt-get -y install git raspberrypi-kernel-headers")

    # Clone the repo
    run_command("git clone https://github.com/adafruit/Raspberry-Pi-Installer-Scripts.git")

    # Build and install the module
    os.chdir(os.getcwd() + "/Raspberry-Pi-Installer-Scripts/i2s_mic_module")
    run_command("make clean")
    run_command("make")
    run_command("make install")

    # Setup auto load at boot if selected
    if auto_load:
        file = open("/etc/modules-load.d/snd-i2smic-rpi.conf", "wt+")
        file.write("""
snd-i2smic-rpi
""")
        file = open("/etc/modprobe.d/snd-i2smic-rpi.conf", "wt+")
        file.write("""
options snd-i2smic-rpi rpi_platform_generation={}
""".format(pimodel_select))

    # Enable I2S overlay
    run_command("sed -i -e 's/#dtparam=i2s/dtparam=i2s/g' /boot/config.txt")

    # Done
    print("""DONE.

Settings take effect on next boot.
""")
    if prompt.yn("REBOOT NOW?", "n"):
        print("Exiting without reboot.")
        sys.exit(0)
    print("Reboot started...")
    os.system('reboot')
    sys.exit(0)

# Main function
if __name__ == "__main__":
    if os.geteuid() != 0:
        print("Installer must be run as root.")
        print("Try 'sudo python3 {}'".format(sys.argv[0]))
        sys.exit(1)
    main()
