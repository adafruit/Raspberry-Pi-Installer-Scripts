# Raspberry-Pi-Installer-Scripts

Some scripts for helping install Adafruit HATs, bonnets, add-on's, & friends!

Many scripts are based heavily on get.pimoroni.com scripts!

  * Install i2s amplifier with: curl -sS https://raw.githubusercontent.com/adafruit/Raspberry-Pi-Installer-Scripts/master/i2samp.sh | bash

## Python Scripts

We are in the process of converting our Shell Scripts to Python. Instructions for running specific scripts are available in the [Adafruit Learning System](https://learn.adafruit.com/). Here are the general setup instructions.

### Dependencies

- Python 3
- [Adafruit_Python_Shell](https://github.com/adafruit/Adafruit_Python_Shell)
- [Click](https://pypi.org/project/click/)

### Prepare your system

To install the dependencies for the python scripts, run the following commands:

```bash
sudo apt-get install python3-pip
sudo pip3 install --upgrade click
sudo pip3 install --upgrade setuptools
sudo pip3 install --upgrade adafruit-python-shell
```
Then to run the python script, type the following replacing "scriptname.py" with the actual script name:

```bash
sudo python3 scriptname.py
```

## Old Shell Scripts

If you were directed here from an external site and the script you were looking for appears to be missing, you can either use the newer python script or check the [converted_shell_scripts](https://github.com/adafruit/Raspberry-Pi-Installer-Scripts/tree/main/converted_shell_scripts) folder to use the old shell scripts.
