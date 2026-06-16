# Raspberry-Pi-Installer-Scripts

Some scripts for helping install Adafruit HATs, bonnets, add-on's, & friends!

Many scripts are based heavily on get.pimoroni.com scripts!

  * Install i2s amplifier: see the [Adafruit MAX98357 I2S Amp guide](https://learn.adafruit.com/adafruit-max98357-i2s-class-d-mono-amp/raspberry-pi-usage), or follow the [Python script setup](#python-scripts) below and run `sudo python3 i2samp.py`.

## Python Scripts

Our installer scripts are written in Python. Instructions for running specific scripts are available in the [Adafruit Learning System](https://learn.adafruit.com/). Here are the general setup instructions.

### Dependencies

- Python 3
- [Adafruit_Python_Shell](https://github.com/adafruit/Adafruit_Python_Shell)
- [Click](https://pypi.org/project/click/)

### Prepare your system

To install the dependencies for the Python scripts, run the following commands:

```bash
sudo apt-get install python3-pip python3-venv
python -m venv env --system-site-packages
source env/bin/activate
pip3 install adafruit-python-shell click
```
Then to run the Python script, type the following replacing "scriptname.py" with the actual script name:

```bash
sudo -E env PATH=$PATH python3 scriptname.py
```

## Old Shell Scripts

If you were directed here from an external site and the script you were looking for appears to be missing, you can either use the newer python script or check the [converted_shell_scripts](https://github.com/adafruit/Raspberry-Pi-Installer-Scripts/tree/main/converted_shell_scripts) folder to use the old shell scripts.
