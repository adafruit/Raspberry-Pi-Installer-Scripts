#!/bin/bash

# Wait for TFT framebuffer to be ready
echo "Waiting for SPI TFT framebuffer..."

# Wait up to 30 seconds for /dev/fb0 or /dev/fb1 to appear
for i in {1..300}; do
    for fbdev in 0 1; do
        if [ -e /dev/fb$fbdev ]; then
            echo "Found /dev/fb$fbdev, checking if it's ili9341..."

            # Check if it's actually the ili9341 device
            if dmesg | grep -q "ili9341.*fb$fbdev"; then
                echo "ili9341 framebuffer ready, mapping console..."
                con2fbmap 1 $fbdev
                echo "Console mapped to framebuffer $fbdev"
                exit 0
            fi
        fi
    done
    sleep 0.1
done

echo "Timeout waiting for SPI TFT framebuffer"
exit 1
