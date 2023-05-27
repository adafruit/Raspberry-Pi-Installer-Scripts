#!/bin/bash

# Unload
sudo dtoverlay -r drm-minipitft114
sudo modprobe -r fb_st7789v
sudo modprobe -r fbtft

# Compile
sudo make

# Load again
sudo modprobe fbtft
sudo insmod ./fb_st7789v.ko
sudo dtoverlay drm-minipitft114