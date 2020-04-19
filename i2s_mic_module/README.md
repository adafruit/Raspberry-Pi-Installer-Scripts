**Driver for the Adafruit I2S MEMS Microphone**

[Product learn page on Adafruit](https://learn.adafruit.com/adafruit-i2s-mems-microphone-breakout/overview).

Known problems with this driver: Low vol level. While you can use the alsa magic socery to make an alsa softvol input, that approach won't work out of the box with anything that uses Pulseaudio. If you have any idea how to make this work with Pulse, please drop me a line.

Installing the I2S microphone driver the easy way
====================================

If you use Raspbian or any Debian-derived distribution, [go to the releases tab](https://github.com/htruong/snd-i2s_rpi/releases) and download the newest deb version.

Then do the following

```bash

# Installing raspberrypi-kernel-headers works only if you haven't messed with
# the rpi-update thing.
# If you did, then you would have to do the rpi-source method
# to get the kernel headers. See: 
# https://learn.adafruit.com/adafruit-i2s-mems-microphone-breakout/raspberry-pi-wiring-and-test#kernel-compiling

$ sudo apt install dkms raspberrypi-kernel-headers

$ sudo dpkg -i snd-i2s-rpi-dkms_0.0.2_all.deb

# For this to work, remember to modify these first:
# /boot/config.txt -> dtparam=i2s=on
# and 
# /etc/modules -> snd-bcm2835
# remember to reboot

$ sudo modprobe snd-i2s_rpi rpi_platform_generation=0

# rpi_platform_generation=0 for Raspberry Pi 1 B/A/A+, 0
# do not add anything for everything else (2/3).

# see if it works

$ dmesg | grep i2s

# it should say blah.i2s mapping OK

# [    3.519017] snd_i2s_rpi: loading out-of-tree module taints kernel.
# [    3.519881] snd-i2s_rpi: Version 0.0.2
# [    3.519889] snd-i2s_rpi: Setting platform to 20203000.i2s
# [    7.624559] asoc-simple-card asoc-simple-card.0: ASoC: CPU DAI 20203000.i2s not registered - will retry
#  ... snip ...
# [    9.507142] asoc-simple-card asoc-simple-card.0: snd-soc-dummy-dai <-> 20203000.i2s mapping ok

$ arecord -l

# it should list your mic
# note that the default vol level is very low, you need
# to follow the ladyada's guide to make it hearable


# If you want it to load automatically at startup

# 1. Add to /etc/modules
# snd-i2s_rpi

# 2. If you have a Pi old-gen, you need to do this:
# create file called /etc/modprobe.d/snd-i2s_rpi.conf
# add this line
# options snd-i2s_rpi rpi_platform_generation=0

```


Installing as a stand-alone module
====================================

    make
    sudo make install

To load the driver manually, run this as root:

    modprobe snd-i2s_rpi

You may also specify custom toolchains by using the `CROSS_COMPILE` flag:

    CROSS_COMPILE=/usr/local/bin/arm-eabi-


Installing as a part of the kernel
======================================

Instructions to come later. Who would ever want to do that?




Installing as a DKMS module
=================================

You can have even more fun with snd-i2s\_rpi by installing it as a DKMS module has the main advantage of being auto-compiled (and thus, possibly surviving) between kernel upgrades.

First, get dkms. On Raspbian this should be:

	sudo apt install dkms

Then copy the root of this repository to `/usr/share`:

	sudo cp -R . /usr/src/snd-i2s_rpi-0.0.2 (or whatever version number declared on dkms.conf is)
	sudo dkms add -m snd-i2s_rpi -v 0.0.2

Build and load the module:

	sudo dkms build -m snd-i2s_rpi -v 0.0.2
	sudo dkms install -m snd-i2s_rpi -v 0.0.2

Now you have a proper dkms module that will work for a long time... hopefully.


