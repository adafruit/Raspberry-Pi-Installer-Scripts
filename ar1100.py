#!/usr/bin/python
import usb.core
import usb.util
import time
import os
import pygame
from pygame.locals import *

def mapnum(x, in_min, in_max, out_min, out_max):
        return (x - in_min) * (out_max - out_min) / (in_max - in_min) + out_min;


CALIBRATED_5IN_800x480 = [
0x00, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff,
0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff,
0x55, 0x80, 0x05, 0x05, 0x40, 0x03, 0x00, 0x20, 0x00, 0x50, 0x00, 0x80, 0x00, 0xb0, 0x00, 0xe0,
0x00, 0x20, 0x00, 0x50, 0x00, 0x80, 0x00, 0xb0, 0x00, 0xe0, 0x4d, 0x2a, 0x3a, 0x2b, 0xcb, 0x56,
0xb5, 0x29, 0x18, 0x82, 0xe9, 0x29, 0x41, 0xad, 0x06, 0x2b, 0x16, 0xd9, 0x42, 0x2a, 0x45, 0x29,
0x82, 0x53, 0x10, 0x56, 0xda, 0x54, 0x99, 0x81, 0xcf, 0x55, 0x5e, 0xac, 0xec, 0x55, 0x83, 0xd8,
0xcf, 0x55, 0xf1, 0x29, 0x3d, 0x82, 0xa0, 0x55, 0x11, 0x82, 0x22, 0x81, 0x4b, 0x81, 0x47, 0xad,
0xc2, 0x82, 0x06, 0xd9, 0xc8, 0x82, 0x65, 0x2a, 0xda, 0xac, 0xc1, 0x55, 0xa3, 0xac, 0xeb, 0x80,
0x26, 0xae, 0x27, 0xac, 0xd9, 0xad, 0x8e, 0xd8, 0xd9, 0xae, 0x8b, 0x28, 0xb9, 0xda, 0x9a, 0x54,
0x59, 0xdb, 0x1e, 0x7f, 0x78, 0xdc, 0x0f, 0xad, 0xdd, 0xdc, 0x88, 0xd8, 0xde, 0xdb, 0x00, 0x00,
]

CALIBRATED_7IN_800x480 = [
0x00, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff,
0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff,
0x55, 0x80, 0x03, 0x03, 0x40, 0x02, 0x00, 0x20, 0x00, 0x80, 0x00, 0xe0, 0x00, 0xb0, 0x00, 0xe0,
0x00, 0x20, 0x00, 0x80, 0x00, 0xe0, 0x00, 0xb0, 0x00, 0xe0, 0x7f, 0x22, 0x5c, 0x2d, 0xbf, 0x7d,
0xdd, 0x2a, 0xaf, 0xdc, 0xf3, 0x2b, 0x21, 0x23, 0xb2, 0x82, 0xb4, 0x80, 0x4c, 0x82, 0x40, 0xde,
0xe7, 0x85, 0x42, 0x23, 0xcc, 0xd6, 0xda, 0x7e, 0x7d, 0xd7, 0xd9, 0xdc, 0x8b, 0xd8, 0x83, 0xd8,
0xcf, 0x55, 0xf1, 0x29, 0x3d, 0x82, 0xa0, 0x55, 0x11, 0x82, 0x22, 0x81, 0x4b, 0x81, 0x47, 0xad,
0xc2, 0x82, 0x06, 0xd9, 0xc8, 0x82, 0x65, 0x2a, 0xda, 0xac, 0xc1, 0x55, 0xa3, 0xac, 0xeb, 0x80,
0x26, 0xae, 0x27, 0xac, 0xd9, 0xad, 0x8e, 0xd8, 0xd9, 0xae, 0x8b, 0x28, 0xb9, 0xda, 0x9a, 0x54,
0x59, 0xdb, 0x1e, 0x7f, 0x78, 0xdc, 0x0f, 0xad, 0xdd, 0xdc, 0x88, 0xd8, 0xde, 0xdb, 0x00, 0x00,
]

writeeeprom = CALIBRATED_5IN_800x480;

USB_MODE_GENERIC = [0x55, 0x01, 0x70]
USB_MODE_MOUSE = [0x55, 0x01, 0x71]

MCP_VID = 0x04D8
MOUSE_PID = 0x0C02
GENERIC_PID = 0x0C01

# Try to locate it as a mouse:
dev = usb.core.find(idVendor=MCP_VID, idProduct=MOUSE_PID)
if dev:
        # first endpoint
        interface = 0
        endpoint = dev[0][(0,0)][0]

        # if the OS kernel already claimed the device, which is most likely true
        # thanks to http://stackoverflow.com/questions/8218683/pyusb-cannot-set-configuration

        if dev.is_kernel_driver_active(interface) is True:
          # tell the kernel to detach
          dev.detach_kernel_driver(interface)
          # claim the device
          usb.util.claim_interface(dev, interface)

        # try to send it command to swap to generic HID
        try:
          # turn into HID
          #                             bReq, wVal,   wIndex, data
          ret = dev.ctrl_transfer(0x21, 0x09, 0x0003, 0x0000, [0x55, 0x01, 0x70])
          if (ret == 3):
                print("Turned into HID!")
        except:
          # failed to get data for this request
          print("Failed to turn into HID")
          exit(-1)

# Try to locate it as a mouse:
dev = usb.core.find(idVendor=MCP_VID, idProduct=GENERIC_PID)

if (not dev):
        print("Couldn't find generic either :/")
        exit(-1)

print("Found Generic!")
interface = 0
endpoint = dev[0][(0,0)][1]

while True:
        #try:

                if dev.is_kernel_driver_active(interface) is True:
                  # tell the kernel to detach
                  dev.detach_kernel_driver(interface)
                  # claim the device
                  usb.util.claim_interface(dev, interface)

                time.sleep(1)
                dev.set_configuration()
                break
        #except:
        #        print("retrying set config...")


print("Writing EEPROM...")
for addr in range (0x60, 0xFF, 8):
        msg = [0x55, 0x04 + 8, 0x29, 0x00, addr, 8]
        msg.extend(writeeeprom[addr-0x60:addr-0x60+8])

        #print(msg)
        #print(', '.join([hex(i) for i in msg]))
        ret = dev.write(1, msg)
        #print("Wrote : ", ret)

        ret = dev.read(0x81, 64)
        #print("Read : ", readeeprom.extend(ret[4:20]))
        #print(', '.join([hex(i) for i in ret[0:4]]))
        if ret[2] != 0:
                print("Failed to write")
                exit(-1)


print("Reading EEPROM...")
readeeprom = []
for addr in range (0x60, 0xF8 , 16):
        msg = [0x55, 0x04, 0x28, 0x00, addr, 16]
        ret = dev.write(1, msg)
        #print("Wrote :", ret)

        ret = dev.read(0x81, 64)
        #print("Read :",ret)
        readeeprom.extend(ret[4:20])
        #print(', '.join([hex(i) for i in ret[4:20]]))

for i in range(len(readeeprom)):
        print(("0x%02x," % readeeprom[i]), end='')
        if (i % 16 == 15):
                print("")
#print(", 0x%2X".join([hex (i) for i in readeeprom]))

# compare eeproms
if (writeeeprom != readeeprom):
        print("Failed to write eeprom correctly (verification fail)")
        exit(-1)

print("EEPROM verified OK!")


# try to send it command to swap to generic HID
try:
        # turn into Mouse
        #                             bReq, wVal,   wIndex, data
        ret = dev.ctrl_transfer(0x21, 0x09, 0x0003, 0x0000, [0x55, 0x01, 0x71])
        if (ret == 3):
                print("Turned into Mouse!")
except:
        # failed to get data for this request
        print("Failed to turn into Mouse")
        exit(-1)
try:
        # release the device
        usb.util.release_interface(dev, interface)
        # reattach the device to the OS kernel
        dev.attach_kernel_driver(interface)
except:
        pass

time.sleep(3)

# Try to locate it as a mouse:
dev = usb.core.find(idVendor=MCP_VID, idProduct=MOUSE_PID)
if not dev:
        print("No mouse :(")
        exit(-1)

# first endpoint
interface = 0
endpoint = dev[0][(0,0)][0]

# if the OS kernel already claimed the device, which is most likely true
# thanks to http://stackoverflow.com/questions/8218683/pyusb-cannot-set-configuration

if dev.is_kernel_driver_active(interface) is True:
          # tell the kernel to detach
          dev.detach_kernel_driver(interface)
          # claim the device
          usb.util.claim_interface(dev, interface)

# set up pygame

white = (255, 255, 255)
w = 800
h = 480

# Output to the LCD instead of the console
os.putenv("DISPLAY", ":0")

pygame.init()


screen = pygame.display.set_mode((w, h))
running = 1

img = pygame.image.load('gradient800x480.jpg')

screen.fill((white))
screen.blit(img,(0,0))
pygame.display.flip()
while running:
    for event in pygame.event.get():
           print(event)
           if event.type == QUIT:
               exit(0)
           elif event.type == KEYDOWN:
               if event.key == K_ESCAPE:
                   pygame.quit()
                   exit(0)

    try:
        data = dev.read(endpoint.bEndpointAddress,endpoint.wMaxPacketSize)
        #print(data)
        x = data[1] + (data[2] << 8)
        y = data[3] + (data[4] << 8)
        #print(x, y)
        x = mapnum(x, 0, 4096, 0, w)
        y = mapnum(y, 0, 4096, 0, h)
        print(x, y)
        pygame.draw.circle(screen, white, (x,y), 10)
        pygame.display.flip()

    except usb.core.USBError as e:
        data = None
        if e.args == ('Operation timed out',):
            continue

# release the device
usb.util.release_interface(dev, interface)
# reattach the device to the OS kernel
dev.attach_kernel_driver(interface)
