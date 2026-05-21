#!/bin/bash

# Map the Linux console (tty1) to the SPI TFT framebuffer.
#
# Background: when vc4-kms-v3d (HDMI) and the SPI TFT DRM driver
# (ili9341 / hx8357 / mipi-dbi-spi) both load at boot, they race for
# DRM minor / framebuffer numbers. The SPI display can land on either
# /dev/fb0 or /dev/fb1 depending on probe order. Greping dmesg for a
# fixed fb number is brittle (issue #365), so we discover the SPI TFT
# framebuffer by walking /sys/class/graphics/fb*.
#
# After remapping, we force a console refresh so whatever was last
# drawn on the old framebuffer gets re-rendered on the SPI display.

set -u

DISPLAY_TYPE="{display_type}"
TIMEOUT_DECISECONDS=300   # 30 seconds (loop sleeps 0.1s)

echo "Waiting for SPI TFT framebuffer (display_type=${DISPLAY_TYPE})..."

# Return 0 (and echo the fb number) if /sys/class/graphics/$1 looks
# like the SPI TFT we installed for.
is_spi_tft_fb() {
    local fbpath="$1"
    local fbname
    local devpath

    # Read the framebuffer driver name, e.g. "ili9341drmfb", "hx8357drmfb",
    # "mipi_dbi", "vc4drmfb", "simple-framebuffer".
    fbname="$(cat "${fbpath}/name" 2>/dev/null || true)"

    # Resolve the underlying device path (DRM card → parent device).
    devpath="$(readlink -f "${fbpath}/device" 2>/dev/null || true)"

    # 1) Name-based match. Works for ili9341, hx8357d, st7789, etc. The
    #    fbdev name varies by driver: DRM tinydrm uses "<name>drmfb"
    #    (e.g. "ili9341drmfb"); the older fbtft staging driver uses
    #    "fb_<name>" (e.g. "fb_ili9341"). Accept either.
    if [ -n "${fbname}" ]; then
        if [[ "${fbname}" == *"${DISPLAY_TYPE}"* ]]; then
            return 0
        fi
    fi

    # 2) Device-path match. For panel-mipi-dbi-spi the fbdev name is
    #    "panel-mipi-dbid" / "mipi_dbi" which does not contain the
    #    configured display_type, but the device path under sysfs lives
    #    below the SPI controller (e.g. .../soc/.../spi@.../spi0.0
    #    or .../soc/.../spi@.../spi0.0/...). Match any SPI slave on
    #    spi0.0, which is where the installer wires SPI TFT panels.
    #    Accept both the bare leaf path (.../spi0.0) and any child path
    #    (.../spi0.0/...); earlier versions required a trailing slash
    #    and missed the leaf case used by panel-mipi-dbi-spi.
    if [ -n "${devpath}" ] && \
       { [[ "${devpath}" == *"/spi0.0" ]] || [[ "${devpath}" == *"/spi0.0/"* ]]; }; then
        # Belt-and-braces: exclude framebuffers that are obviously not
        # the SPI TFT (e.g. vc4drmfb, simple-framebuffer). Those should
        # not have spi0.0 in their devpath, but guard anyway.
        if [[ "${fbname}" != "vc4drmfb" && "${fbname}" != "simple-framebuffer" ]]; then
            return 0
        fi
    fi

    return 1
}

found_fb=""

for ((i = 1; i <= TIMEOUT_DECISECONDS; i++)); do
    for fbpath in /sys/class/graphics/fb*; do
        [ -e "${fbpath}" ] || continue
        fbnum="${fbpath##*/fb}"
        # Only accept numeric fb entries (skip e.g. /sys/class/graphics/fbcon).
        case "${fbnum}" in
            ''|*[!0-9]*) continue ;;
        esac
        [ -e "/dev/fb${fbnum}" ] || continue

        if is_spi_tft_fb "${fbpath}"; then
            found_fb="${fbnum}"
            break 2
        fi
    done
    sleep 0.1
done

if [ -z "${found_fb}" ]; then
    echo "Timeout waiting for SPI TFT framebuffer (display_type=${DISPLAY_TYPE})"
    echo "Available framebuffers:"
    for fbpath in /sys/class/graphics/fb*; do
        [ -e "${fbpath}/name" ] || continue
        fbname="$(cat "${fbpath}/name" 2>/dev/null || true)"
        devpath="$(readlink -f "${fbpath}/device" 2>/dev/null || true)"
        echo "  ${fbpath}: name='${fbname}' device='${devpath}'"
    done
    exit 1
fi

echo "SPI TFT framebuffer ready on /dev/fb${found_fb}, mapping console..."
con2fbmap 1 "${found_fb}"
echo "Console mapped to framebuffer ${found_fb}"

# Force a redraw of tty1. con2fbmap only updates the routing table;
# without this, getty's earlier output stays on the old framebuffer and
# the SPI display keeps showing whatever was on it at power-on. ESC c
# resets the terminal which prompts fbcon to repaint the active console.
if [ -w /dev/tty1 ]; then
    printf '\033c' > /dev/tty1 2>/dev/null || true
fi

# Re-apply the configured console font, now that fbcon is attached to
# the SPI TFT framebuffer. Background (issue #341): when fbcon first
# attaches to the SPI panel it sizes its character grid against the
# kernel built-in 8x8 boot font (e.g. 30 columns on a 240px panel). The
# normal console-setup.service runs setfont *before* the SPI panel
# probes here (it targets the dummy/vc4 console), so when the SPI panel
# eventually takes over the console its grid never gets resized for the
# narrower 6px-wide Terminus 6x12 font - the kernel keeps painting a
# 30-cell grid using 6px glyphs in 8px slots, leaving the right ~25%
# of the panel unpainted at the shell prompt.
#
# Re-running setupcon here, *after* con2fbmap, lands a second setfont
# on the SPI fbcon while it is idle, which triggers the grid recompute
# (30 cols * 8 px slot -> 40 cols * 6 px = full 240 px width).
if command -v setupcon >/dev/null 2>&1; then
    echo "Re-applying console font to refresh fbcon character grid..."
    setupcon --force --save-only >/dev/null 2>&1 || true
    setupcon --force </dev/tty1 >/dev/tty1 2>&1 || true
fi

exit 0
