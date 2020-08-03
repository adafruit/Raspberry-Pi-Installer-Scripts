// SPDX-License-Identifier: GPL-2.0+
/*
 * FB driver for the ST7789V LCD Controller
 *
 * Copyright (C) 2015 Dennis Menschel
 */

#include <linux/bitops.h>
#include <linux/delay.h>
#include <linux/init.h>
#include <linux/kernel.h>
#include <linux/module.h>
#include <video/mipi_display.h>

#include "fbtft.h"

#define DRVNAME "fb_st7789v"

static unsigned int width;
module_param(width, uint, 0000);
MODULE_PARM_DESC(width, "Display width");

static unsigned int height;
module_param(height, uint, 0000);
MODULE_PARM_DESC(height, "Display height");

static u32 col_offset = 0;
static u32 row_offset = 0;
static u8 col_hack_fix_offset = 0;
static short x_offset = 0;
static short y_offset = 0;

#define ST77XX_MADCTL_MY  0x80
#define ST77XX_MADCTL_MX  0x40
#define ST77XX_MADCTL_MV  0x20
#define ST77XX_MADCTL_ML  0x10
#define ST77XX_MADCTL_BGR 0x08
#define ST77XX_MADCTL_RGB 0x00

#define DEFAULT_GAMMA \
	"70 2C 2E 15 10 09 48 33 53 0B 19 18 20 25\n" \
	"70 2C 2E 15 10 09 48 33 53 0B 19 18 20 25"

/**
 * enum st7789v_command - ST7789V display controller commands
 *
 * @PORCTRL: porch setting
 * @GCTRL: gate control
 * @VCOMS: VCOM setting
 * @VDVVRHEN: VDV and VRH command enable
 * @VRHS: VRH set
 * @VDVS: VDV set
 * @VCMOFSET: VCOM offset set
 * @PWCTRL1: power control 1
 * @PVGAMCTRL: positive voltage gamma control
 * @NVGAMCTRL: negative voltage gamma control
 *
 * The command names are the same as those found in the datasheet to ease
 * looking up their semantics and usage.
 *
 * Note that the ST7789V display controller offers quite a few more commands
 * which have been omitted from this list as they are not used at the moment.
 * Furthermore, commands that are compliant with the MIPI DCS have been left
 * out as well to avoid duplicate entries.
 */
enum st7789v_command {
	PORCTRL = 0xB2,
	GCTRL = 0xB7,
	VCOMS = 0xBB,
	VDVVRHEN = 0xC2,
	VRHS = 0xC3,
	VDVS = 0xC4,
	VCMOFSET = 0xC5,
	PWCTRL1 = 0xD0,
	PVGAMCTRL = 0xE0,
	NVGAMCTRL = 0xE1,
};

/**
 * init_display() - initialize the display controller
 *
 * @par: FBTFT parameter object
 *
 * Most of the commands in this init function set their parameters to the
 * same default values which are already in place after the display has been
 * powered up. (The main exception to this rule is the pixel format which
 * would default to 18 instead of 16 bit per pixel.)
 * Nonetheless, this sequence can be used as a template for concrete
 * displays which usually need some adjustments.
 *
 * Return: 0 on success, < 0 if error occurred.
 */
static int init_display(struct fbtft_par *par)
{
    printk(KERN_INFO "ST7789 adafruit fbtft driver\n");

    width = par->info->var.xres;
    height = par->info->var.yres;

    if ((width == 0) || (width > 240)) {
      width = 240;
    }
    if ((height == 0) || (height > 320)) {
      height = 320;
    }
    printk(KERN_INFO "Size: (%d, %d)\n", width, height);
  
    // Go to sleep
    write_reg(par, MIPI_DCS_SET_DISPLAY_OFF);
    // Soft reset
	write_reg(par, MIPI_DCS_SOFT_RESET);
	mdelay(150);

	/* turn off sleep mode */
	write_reg(par, MIPI_DCS_EXIT_SLEEP_MODE);
	mdelay(10);

	/* set pixel format to RGB-565 */
	write_reg(par, MIPI_DCS_SET_PIXEL_FORMAT, MIPI_DCS_PIXEL_FMT_16BIT);

	write_reg(par, MIPI_DCS_SET_ADDRESS_MODE, 0);
	write_reg(par, MIPI_DCS_SET_COLUMN_ADDRESS, 0, 0, 0, 240);
	write_reg(par, MIPI_DCS_SET_PAGE_ADDRESS, 0, 0, 320>>8, 320&0xFF);
	write_reg(par, MIPI_DCS_ENTER_INVERT_MODE); // odd hack, displays are inverted
	write_reg(par, MIPI_DCS_ENTER_NORMAL_MODE);
	mdelay(10);


	write_reg(par, MIPI_DCS_SET_DISPLAY_ON);
	return 0;
}

/**
 * set_var() - apply LCD properties like rotation and BGR mode
 *
 * @par: FBTFT parameter object
 *
 * Return: 0 on success, < 0 if error occurred.
 */
static int set_var(struct fbtft_par *par)
{
	u8 addr_mode = 0;

	switch (par->info->var.rotate) {
	case 0:
		addr_mode = 0;
		x_offset = col_offset;
		y_offset = row_offset;        
		break;
	case 90:
		addr_mode = ST77XX_MADCTL_MV | ST77XX_MADCTL_MX;
		x_offset = row_offset;
		y_offset = col_offset;
        break;
	case 180:
		addr_mode = ST77XX_MADCTL_MX | ST77XX_MADCTL_MY;
        x_offset = (240 - width) - col_offset + col_hack_fix_offset;
        // hack tweak to account for extra pixel width to make even
        y_offset = (320 - height) - row_offset;
		break;
	case 270:
		addr_mode = ST77XX_MADCTL_MV | ST77XX_MADCTL_MY;
		x_offset = (320 - height) - row_offset;
		y_offset = (240 - width) - col_offset;
		break;
	default:
		return -EINVAL;
	}
    printk(KERN_INFO "Rotation %d offsets %d %d\n", par->info->var.rotate, x_offset, y_offset);

	write_reg(par, MIPI_DCS_SET_ADDRESS_MODE, addr_mode);
	return 0;
}

/**
 * blank() - blank the display
 *
 * @par: FBTFT parameter object
 * @on: whether to enable or disable blanking the display
 *
 * Return: 0 on success, < 0 if error occurred.
 */
static int blank(struct fbtft_par *par, bool on)
{
	if (on)
		write_reg(par, MIPI_DCS_SET_DISPLAY_OFF);
	else
		write_reg(par, MIPI_DCS_SET_DISPLAY_ON);
	return 0;
}

static struct fbtft_display display = {
	.regwidth = 8,
	.width = 240,
	.height = 320,
	.gamma_num = 2,
	.gamma_len = 14,
	.gamma = DEFAULT_GAMMA,
	.fbtftops = {
		.init_display = init_display,
		.set_var = set_var,
		.blank = blank,
	},
};

FBTFT_REGISTER_DRIVER(DRVNAME, "sitronix,st7789v", &display);

MODULE_ALIAS("spi:" DRVNAME);
MODULE_ALIAS("platform:" DRVNAME);
MODULE_ALIAS("spi:st7789v");
MODULE_ALIAS("platform:st7789v");

MODULE_DESCRIPTION("FB driver for the ST7789V LCD Controller");
MODULE_AUTHOR("Dennis Menschel");
MODULE_LICENSE("GPL");
