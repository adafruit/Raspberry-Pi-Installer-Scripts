/*
 * DRM driver for ST7789V panels with flexible config
 *
 * Copyright 2019 Limor Fried
 * Copyright 2016 Noralf Trønnes
 *
 * This program is free software; you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation; either version 2 of the License, or
 * (at your option) any later version.
 */

#include <linux/backlight.h>
#include <linux/delay.h>
#include <linux/gpio/consumer.h>
#include <linux/module.h>
#include <linux/property.h>
#include <linux/regulator/consumer.h>
#include <linux/spi/spi.h>

#include <drm/drm_fb_helper.h>
#include <drm/drm_modeset_helper.h>
#include <drm/drm_gem_framebuffer_helper.h>
#include <drm/tinydrm/mipi-dbi.h>
#include <drm/tinydrm/tinydrm-helpers.h>
#include <video/mipi_display.h>

#define ST77XX_MADCTL_MY  0x80
#define ST77XX_MADCTL_MX  0x40
#define ST77XX_MADCTL_MV  0x20
#define ST77XX_MADCTL_ML  0x10
#define ST77XX_MADCTL_BGR 0x08
#define ST77XX_MADCTL_RGB 0x00

static u32 col_offset = 0;
static u32 row_offset = 0;
static u8 col_hack_fix_offset = 0;
static short x_offset = 0;
static short y_offset = 0;

static void st7789vada_enable(struct drm_simple_display_pipe *pipe,
			    struct drm_crtc_state *crtc_state,
			    struct drm_plane_state *plane_state)
{
	struct tinydrm_device *tdev = pipe_to_tinydrm(pipe);
	struct mipi_dbi *mipi = mipi_dbi_from_tinydrm(tdev);
	u8 addr_mode;
	int ret;

	DRM_DEBUG_KMS("\n");

	ret = mipi_dbi_poweron_conditional_reset(mipi);
	if (ret < 0)
		return;
	if (ret == 1)
		goto out_enable;

	mipi_dbi_command(mipi, MIPI_DCS_SET_DISPLAY_OFF);

	mipi_dbi_command(mipi, MIPI_DCS_SOFT_RESET);
	msleep(150);
	mipi_dbi_command(mipi, MIPI_DCS_EXIT_SLEEP_MODE);
	msleep(10);
	mipi_dbi_command(mipi, MIPI_DCS_SET_PIXEL_FORMAT, 0x55); // 16 bit color
	msleep(10);
	mipi_dbi_command(mipi, MIPI_DCS_SET_ADDRESS_MODE, 0);
	mipi_dbi_command(mipi, MIPI_DCS_SET_COLUMN_ADDRESS, 0, 0, 0, 240);
	mipi_dbi_command(mipi, MIPI_DCS_SET_PAGE_ADDRESS, 0, 0, 320>>8, 320&0xFF);
	mipi_dbi_command(mipi, MIPI_DCS_ENTER_INVERT_MODE); // odd hack, displays are inverted
	mipi_dbi_command(mipi, MIPI_DCS_ENTER_NORMAL_MODE);
	msleep(10);
	mipi_dbi_command(mipi, MIPI_DCS_SET_DISPLAY_ON);
	msleep(10);

out_enable:
	/* The PiTFT (ili9340) has a hardware reset circuit that
	 * resets only on power-on and not on each reboot through
	 * a gpio like the rpi-display does.
	 * As a result, we need to always apply the rotation value
	 * regardless of the display "on/off" state.
	 */
	switch (mipi->rotation) {
	default:
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
		x_offset = col_offset+col_hack_fix_offset; 
		// hack tweak to account for extra pixel width to make even
		y_offset = row_offset; 
		break;
	case 270:
		addr_mode = ST77XX_MADCTL_MV | ST77XX_MADCTL_MY;
		x_offset = row_offset;
		y_offset = col_offset;
		break;
	}
	mipi_dbi_command(mipi, MIPI_DCS_SET_ADDRESS_MODE, addr_mode);

	mipi_dbi_command(mipi, MIPI_DCS_SET_DISPLAY_ON);

	mipi_dbi_enable_flush(mipi, crtc_state, plane_state);

	backlight_enable(mipi->backlight);
}

static const struct drm_simple_display_pipe_funcs st7789vada_pipe_funcs = {
	.enable = st7789vada_enable,
	.disable = mipi_dbi_pipe_disable,
	.update = tinydrm_display_pipe_update,
	.prepare_fb = drm_gem_fb_simple_display_pipe_prepare_fb,
};

static struct drm_display_mode st7789vada_mode = {
  TINYDRM_MODE(240, 320, 25, 15), // width, height, mm_w, mm_h
};

DEFINE_DRM_GEM_CMA_FOPS(st7789vada_fops);

static struct drm_driver st7789vada_driver = {
	.driver_features	= DRIVER_GEM | DRIVER_MODESET | DRIVER_PRIME |
				  DRIVER_ATOMIC,
	.fops			= &st7789vada_fops,
	TINYDRM_GEM_DRIVER_OPS,
	.debugfs_init		= mipi_dbi_debugfs_init,
	.name			= "st7789vada",
	.desc			= "ST7789V Adafruit",
	.date			= "20190914",
	.major			= 1,
	.minor			= 0,
};

static const struct of_device_id st7789vada_of_match[] = {
	{ .compatible = "multi-inno,mi0283qt" },
	{},
};
MODULE_DEVICE_TABLE(of, st7789vada_of_match);

static const struct spi_device_id st7789vada_id[] = {
	{ "st7789vada", 0 },
	{ },
};
MODULE_DEVICE_TABLE(spi, st7789vada_id);


static const struct drm_framebuffer_funcs st7789vada_fb_funcs = {
	.destroy	= drm_gem_fb_destroy,
	.create_handle	= drm_gem_fb_create_handle,
	.dirty		= tinydrm_fb_dirty,
};

static const uint32_t st7789vada_formats[] = {
	DRM_FORMAT_RGB565,
	DRM_FORMAT_XRGB8888,
};

static int st7789vada_fb_dirty(struct drm_framebuffer *fb,
			     struct drm_file *file_priv,
			     unsigned int flags, unsigned int color,
			     struct drm_clip_rect *clips,
			     unsigned int num_clips)
{
	struct drm_gem_cma_object *cma_obj = drm_fb_cma_get_gem_obj(fb, 0);
	struct tinydrm_device *tdev = fb->dev->dev_private;
	struct mipi_dbi *mipi = mipi_dbi_from_tinydrm(tdev);
	bool swap = mipi->swap_bytes;
	struct drm_clip_rect clip;
	int ret = 0;
	bool full;
	void *tr;
	u16 x1, x2, y1, y2;

	if (!mipi->enabled)
		return 0;

	full = tinydrm_merge_clips(&clip, clips, num_clips, flags,
				   fb->width, fb->height);

	DRM_DEBUG("Flushing [FB:%d] x1=%u, x2=%u, y1=%u, y2=%u\n", fb->base.id,
		  clip.x1, clip.x2, clip.y1, clip.y2);

	if (!mipi->dc || !full || swap ||
	    fb->format->format == DRM_FORMAT_XRGB8888) {
		tr = mipi->tx_buf;
		ret = mipi_dbi_buf_copy(mipi->tx_buf, fb, &clip, swap);
		if (ret)
			return ret;
	} else {
		tr = cma_obj->vaddr;
	}

	x1 = clip.x1 + x_offset;
	x2 = clip.x2 - 1 + x_offset;
	y1 = clip.y1 + y_offset;
	y2 = clip.y2 - 1 + y_offset;

	//printk(KERN_INFO "setaddrwin %d %d %d %d\n", x1, y1, x2, y2);

	mipi_dbi_command(mipi, MIPI_DCS_SET_COLUMN_ADDRESS,
			 (x1 >> 8) & 0xFF, x1 & 0xFF,
			 (x2 >> 8) & 0xFF, x2 & 0xFF);
	mipi_dbi_command(mipi, MIPI_DCS_SET_PAGE_ADDRESS,
			 (y1 >> 8) & 0xFF, y1 & 0xFF,
			 (y2 >> 8) & 0xFF, y2 & 0xFF);

	ret = mipi_dbi_command_buf(mipi, MIPI_DCS_WRITE_MEMORY_START, tr,
				(clip.x2 - clip.x1) * (clip.y2 - clip.y1) * 2);

	return ret;
}

/**
 * st7789vada - MIPI DBI initialization
 * @dev: Parent device
 * @mipi: &mipi_dbi structure to initialize
 * @pipe_funcs: Display pipe functions
 * @driver: DRM driver
 * @mode: Display mode
 * @rotation: Initial rotation in degrees Counter Clock Wise
 *
 * This function initializes a &mipi_dbi structure and it's underlying
 * @tinydrm_device. It also sets up the display pipeline.
 *
 * Supported formats: Native RGB565 and emulated XRGB8888.
 *
 * Objects created by this function will be automatically freed on driver
 * detach (devres).
 *
 * Returns:
 * Zero on success, negative error code on failure.
 */
int st7789vada_init(struct device *dev, struct mipi_dbi *mipi,
		  const struct drm_simple_display_pipe_funcs *pipe_funcs,
		  struct drm_driver *driver,
		  const struct drm_display_mode *mode, unsigned int rotation)
{
	size_t bufsize = mode->vdisplay * mode->hdisplay * sizeof(u16);
	struct tinydrm_device *tdev = &mipi->tinydrm;
	int ret;

	if (!mipi->command)
		return -EINVAL;

	mutex_init(&mipi->cmdlock);

	mipi->tx_buf = devm_kmalloc(dev, bufsize, GFP_KERNEL);
	if (!mipi->tx_buf)
		return -ENOMEM;

	ret = devm_tinydrm_init(dev, tdev, &st7789vada_fb_funcs, driver);
	if (ret)
		return ret;

	tdev->fb_dirty = st7789vada_fb_dirty;

	/* TODO: Maybe add DRM_MODE_CONNECTOR_SPI */
	ret = tinydrm_display_pipe_init(tdev, pipe_funcs,
					DRM_MODE_CONNECTOR_VIRTUAL,
					st7789vada_formats,
					ARRAY_SIZE(st7789vada_formats), mode,
					rotation);
	if (ret)
		return ret;

	tdev->drm->mode_config.preferred_depth = 16;
	mipi->rotation = rotation;

	drm_mode_config_reset(tdev->drm);

	DRM_DEBUG_KMS("preferred_depth=%u, rotation = %u\n",
		      tdev->drm->mode_config.preferred_depth, rotation);

	return 0;
}

static int st7789vada_probe(struct spi_device *spi)
{
	struct device *dev = &spi->dev;
	struct mipi_dbi *mipi;
	struct gpio_desc *dc;
	u32 rotation = 0;
	u32 width = 240;
	u32 height = 320;
	int ret;

	mipi = devm_kzalloc(dev, sizeof(*mipi), GFP_KERNEL);
	if (!mipi)
		return -ENOMEM;

	mipi->reset = devm_gpiod_get_optional(dev, "reset", GPIOD_OUT_HIGH);
	if (IS_ERR(mipi->reset)) {
		DRM_DEV_ERROR(dev, "Failed to get gpio 'reset'\n");
		return PTR_ERR(mipi->reset);
	}

	dc = devm_gpiod_get_optional(dev, "dc", GPIOD_OUT_LOW);
	if (IS_ERR(dc)) {
		DRM_DEV_ERROR(dev, "Failed to get gpio 'dc'\n");
		return PTR_ERR(dc);
	}

	mipi->regulator = devm_regulator_get(dev, "power");
	if (IS_ERR(mipi->regulator))
		return PTR_ERR(mipi->regulator);

	mipi->backlight = devm_of_find_backlight(dev);
	if (IS_ERR(mipi->backlight))
		return PTR_ERR(mipi->backlight);

	device_property_read_u32(dev, "rotation", &rotation);
	//printk(KERN_INFO "Rotation %d\n", rotation);

	device_property_read_u32(dev, "width", &width);
	if (width % 2) {
	  width +=1;	  // odd width will cause a kernel panic
	  col_hack_fix_offset = 1;
	} else {
	  col_hack_fix_offset = 0;
	}
	//printk(KERN_INFO "Width %d\n", width);
	if ((width == 0) || (width > 240)) {
	  width = 240; // default to full framebuff;
	}
	device_property_read_u32(dev, "height", &height);
	//printk(KERN_INFO "Height %d\n", height);
	if ((height == 0) || (height > 320)) {
	  height = 320; // default to full framebuff;
	}

	st7789vada_mode.hdisplay = st7789vada_mode.hsync_start = 
	  st7789vada_mode.hsync_end = st7789vada_mode.htotal = width;
	st7789vada_mode.vdisplay = st7789vada_mode.vsync_start = 
	  st7789vada_mode.vsync_end = st7789vada_mode.vtotal = height;

	device_property_read_u32(dev, "col_offset", &col_offset);
	//printk(KERN_INFO "Column offset %d\n", col_offset);

	device_property_read_u32(dev, "row_offset", &row_offset);
	//printk(KERN_INFO "Row offset %d\n", row_offset);

	ret = mipi_dbi_spi_init(spi, mipi, dc);
	if (ret)
		return ret;

	/* Cannot read from this controller via SPI */
	mipi->read_commands = NULL;

	ret = st7789vada_init(&spi->dev, mipi, &st7789vada_pipe_funcs,
			      &st7789vada_driver, &st7789vada_mode, rotation);
	if (ret)
		return ret;

	spi_set_drvdata(spi, mipi);

	return devm_tinydrm_register(&mipi->tinydrm);
}

static void st7789vada_shutdown(struct spi_device *spi)
{
	struct mipi_dbi *mipi = spi_get_drvdata(spi);

	tinydrm_shutdown(&mipi->tinydrm);
}

static int __maybe_unused st7789vada_pm_suspend(struct device *dev)
{
	struct mipi_dbi *mipi = dev_get_drvdata(dev);

	return drm_mode_config_helper_suspend(mipi->tinydrm.drm);
}

static int __maybe_unused st7789vada_pm_resume(struct device *dev)
{
	struct mipi_dbi *mipi = dev_get_drvdata(dev);

	drm_mode_config_helper_resume(mipi->tinydrm.drm);

	return 0;
}

static const struct dev_pm_ops st7789vada_pm_ops = {
	SET_SYSTEM_SLEEP_PM_OPS(st7789vada_pm_suspend, st7789vada_pm_resume)
};

static struct spi_driver st7789vada_spi_driver = {
	.driver = {
		.name = "st7789vada",
		.owner = THIS_MODULE,
		.of_match_table = st7789vada_of_match,
		.pm = &st7789vada_pm_ops,
	},
	.id_table = st7789vada_id,
	.probe = st7789vada_probe,
	.shutdown = st7789vada_shutdown,
};
module_spi_driver(st7789vada_spi_driver);

MODULE_DESCRIPTION("Sitronix ST7789V Flexible DRM driver");
MODULE_AUTHOR("Limor Fried");
MODULE_LICENSE("GPL");
