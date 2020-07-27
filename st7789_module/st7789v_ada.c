// SPDX-License-Identifier: GPL-2.0-or-later
/*
 * DRM driver for Multi-Inno MI0283QT panels
 *
 * Copyright 2016 Noralf Trønnes
 */

#include <linux/backlight.h>
#include <linux/delay.h>
#include <linux/gpio/consumer.h>
#include <linux/module.h>
#include <linux/property.h>
#include <linux/regulator/consumer.h>
#include <linux/spi/spi.h>

#include <drm/drm_atomic_helper.h>
#include <drm/drm_damage_helper.h>
#include <drm/drm_drv.h>
#include <drm/drm_fb_cma_helper.h>
#include <drm/drm_fb_helper.h>
#include <drm/drm_fourcc.h>
#include <drm/drm_gem_cma_helper.h>
#include <drm/drm_gem_framebuffer_helper.h>
#include <drm/drm_mipi_dbi.h>
#include <drm/drm_rect.h>
#include <drm/drm_vblank.h>
#include <drm/drm_modeset_helper.h>
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


static void mi0283qt_fb_dirty(struct drm_framebuffer *fb, struct drm_rect *rect)
{
	struct drm_gem_cma_object *cma_obj = drm_fb_cma_get_gem_obj(fb, 0);
	struct mipi_dbi_dev *dbidev = drm_to_mipi_dbi_dev(fb->dev);
	unsigned int height = rect->y2 - rect->y1;
	unsigned int width = rect->x2 - rect->x1;
	struct mipi_dbi *dbi = &dbidev->dbi;
	bool swap = dbi->swap_bytes;
	u16 x1, x2, y1, y2;
	int idx, ret = 0;
	bool full;
	void *tr;

	if (!dbidev->enabled)
		return;

	if (!drm_dev_enter(fb->dev, &idx))
		return;

	full = width == fb->width && height == fb->height;

	DRM_DEBUG_KMS("Flushing [FB:%d] " DRM_RECT_FMT "\n", fb->base.id, DRM_RECT_ARG(rect));

	if (!dbi->dc || !full || swap ||
	    fb->format->format == DRM_FORMAT_XRGB8888) {
		tr = dbidev->tx_buf;
		ret = mipi_dbi_buf_copy(dbidev->tx_buf, fb, rect, swap);
		if (ret)
			goto err_msg;
	} else {
		tr = cma_obj->vaddr;
	}

	x1 = rect->x1 + x_offset;
	x2 = rect->x2 - 1 + x_offset;
	y1 = rect->y1 + y_offset;
	y2 = rect->y2 - 1 + y_offset;

	printk(KERN_INFO "setaddrwin (%d, %d) -> (%d, %d) offsets: %d & %d \n", x1, y1, x2, y2, x_offset, y_offset);

	mipi_dbi_command(dbi, MIPI_DCS_SET_COLUMN_ADDRESS,
			 (x1 >> 8) & 0xFF, x1 & 0xFF,
			 (x2 >> 8) & 0xFF, x2 & 0xFF);
	mipi_dbi_command(dbi, MIPI_DCS_SET_PAGE_ADDRESS,
			 (y1 >> 8) & 0xFF, y1 & 0xFF,
			 (y2 >> 8) & 0xFF, y2 & 0xFF);

	ret = mipi_dbi_command_buf(dbi, MIPI_DCS_WRITE_MEMORY_START, tr,
				width*height * 2);
err_msg:
	if (ret)
		dev_err_once(fb->dev->dev, "Failed to update display %d\n", ret);

	drm_dev_exit(idx);
}



static void mi0283qt_pipe_update(struct drm_simple_display_pipe *pipe,
				struct drm_plane_state *old_state)
{
	struct drm_plane_state *state = pipe->plane.state;
	struct drm_crtc *crtc = &pipe->crtc;
	struct drm_rect rect;

	if (drm_atomic_helper_damage_merged(old_state, state, &rect))
		mi0283qt_fb_dirty(state->fb, &rect);

	if (crtc->state->event) {
		spin_lock_irq(&crtc->dev->event_lock);
		drm_crtc_send_vblank_event(crtc, crtc->state->event);
		spin_unlock_irq(&crtc->dev->event_lock);
		crtc->state->event = NULL;
	}
}


static struct drm_display_mode mi0283qt_mode = {
	DRM_SIMPLE_MODE(240, 320, 58, 43),
};

DEFINE_DRM_GEM_CMA_FOPS(mi0283qt_fops);

static struct drm_driver mi0283qt_driver = {
	.driver_features	= DRIVER_GEM | DRIVER_MODESET | DRIVER_ATOMIC,
	.fops			= &mi0283qt_fops,
	.release		= mipi_dbi_release,
	DRM_GEM_CMA_VMAP_DRIVER_OPS,
	.debugfs_init		= mipi_dbi_debugfs_init,
	.name			= "mi0283qt",
	.desc			= "Multi-Inno MI0283QT",
	.date			= "20160614",
	.major			= 1,
	.minor			= 0,
};

static const struct of_device_id mi0283qt_of_match[] = {
	{ .compatible = "multi-inno,mi0283qt" },
	{},
};
MODULE_DEVICE_TABLE(of, mi0283qt_of_match);

static const struct spi_device_id mi0283qt_id[] = {
	{ "mi0283qt", 0 },
	{ },
};
MODULE_DEVICE_TABLE(spi, mi0283qt_id);



static void mi0283qt_enable(struct drm_simple_display_pipe *pipe,
			    struct drm_crtc_state *crtc_state,
			    struct drm_plane_state *plane_state)
{
	struct mipi_dbi_dev *dbidev = drm_to_mipi_dbi_dev(pipe->crtc.dev);
	struct mipi_dbi *dbi = &dbidev->dbi;
	u8 addr_mode;
	u16 width = mi0283qt_mode.htotal;
    u16 height = mi0283qt_mode.vtotal;
	int ret, idx;

    printk(KERN_INFO "w/h %d %d\n", width, height);
    

	if (!drm_dev_enter(pipe->crtc.dev, &idx))
		return;

	DRM_DEBUG_KMS("\n");

	ret = mipi_dbi_poweron_conditional_reset(dbidev);
	if (ret < 0)
		goto out_exit;
	if (ret == 1)
		goto out_enable;

	mipi_dbi_command(dbi, MIPI_DCS_SET_DISPLAY_OFF);

	mipi_dbi_command(dbi, MIPI_DCS_SOFT_RESET);
	msleep(150);
	mipi_dbi_command(dbi, MIPI_DCS_EXIT_SLEEP_MODE);
	msleep(10);
	mipi_dbi_command(dbi, MIPI_DCS_SET_PIXEL_FORMAT, 0x55); // 16 bit color
	msleep(10);
	mipi_dbi_command(dbi, MIPI_DCS_SET_ADDRESS_MODE, 0);
	mipi_dbi_command(dbi, MIPI_DCS_SET_COLUMN_ADDRESS, 0, 0, 0, 240);
	mipi_dbi_command(dbi, MIPI_DCS_SET_PAGE_ADDRESS, 0, 0, 320>>8, 320&0xFF);
	mipi_dbi_command(dbi, MIPI_DCS_ENTER_INVERT_MODE); // odd hack, displays are inverted
	mipi_dbi_command(dbi, MIPI_DCS_ENTER_NORMAL_MODE);
	msleep(10);
	mipi_dbi_command(dbi, MIPI_DCS_SET_DISPLAY_ON);
	msleep(10);

out_enable:
	/* The PiTFT has a hardware reset circuit that
	 * resets only on power-on and not on each reboot through
	 * a gpio like the rpi-display does.
	 * As a result, we need to always apply the rotation value
	 * regardless of the display "on/off" state.
	 */


	switch (dbidev->rotation) {
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
        x_offset = (240 - width) + col_offset+col_hack_fix_offset; 
        // hack tweak to account for extra pixel width to make even
        y_offset = (320 - height) + row_offset;
        break;
	case 270:
		addr_mode = ST77XX_MADCTL_MV | ST77XX_MADCTL_MY;
		x_offset = (320 - height) + row_offset;
		y_offset = (240 - width) + col_offset;
		break;
	}
    printk(KERN_INFO "Rotation offsets %d %d\n", x_offset, y_offset);
    
	mipi_dbi_command(dbi, MIPI_DCS_SET_ADDRESS_MODE, addr_mode);

	mipi_dbi_command(dbi, MIPI_DCS_SET_DISPLAY_ON);

	mipi_dbi_enable_flush(dbidev, crtc_state, plane_state);
out_exit:
	drm_dev_exit(idx);
}



static const struct drm_simple_display_pipe_funcs mi0283qt_pipe_funcs = {
	.enable = mi0283qt_enable,
	.disable = mipi_dbi_pipe_disable,
	.update = mi0283qt_pipe_update,
	.prepare_fb = drm_gem_fb_simple_display_pipe_prepare_fb,
};



static int mi0283qt_probe(struct spi_device *spi)
{
	struct device *dev = &spi->dev;
	struct mipi_dbi_dev *dbidev;
	struct drm_device *drm;
	struct mipi_dbi *dbi;
	struct gpio_desc *dc;
	u32 rotation = 0;
	u32 width = 240;
	u32 height = 320;
	int ret;

	dbidev = kzalloc(sizeof(*dbidev), GFP_KERNEL);
	if (!dbidev)
		return -ENOMEM;

    printk(KERN_INFO "ST7789 fake driver\n");

	dbi = &dbidev->dbi;
	drm = &dbidev->drm;
	ret = devm_drm_dev_init(dev, drm, &mi0283qt_driver);
	if (ret) {
		kfree(dbidev);
		return ret;
	}

	drm_mode_config_init(drm);

	dbi->reset = devm_gpiod_get_optional(dev, "reset", GPIOD_OUT_HIGH);
	if (IS_ERR(dbi->reset)) {
		DRM_DEV_ERROR(dev, "Failed to get gpio 'reset'\n");
		return PTR_ERR(dbi->reset);
	}

	dc = devm_gpiod_get_optional(dev, "dc", GPIOD_OUT_LOW);
	if (IS_ERR(dc)) {
		DRM_DEV_ERROR(dev, "Failed to get gpio 'dc'\n");
		return PTR_ERR(dc);
	}

	dbidev->regulator = devm_regulator_get(dev, "power");
	if (IS_ERR(dbidev->regulator))
		return PTR_ERR(dbidev->regulator);

	dbidev->backlight = devm_of_find_backlight(dev);
	if (IS_ERR(dbidev->backlight))
		return PTR_ERR(dbidev->backlight);

	device_property_read_u32(dev, "rotation", &rotation);
    printk(KERN_INFO "Rotation %d\n", rotation);

	device_property_read_u32(dev, "width", &width);
	if (width % 2) {
	  width +=1;	  // odd width will cause a kernel panic
	  col_hack_fix_offset = 1;
	} else {
	  col_hack_fix_offset = 0;
	}
	printk(KERN_INFO "Width %d\n", width);
	if ((width == 0) || (width > 240)) {
	  width = 240; // default to full framebuff;
	}
	device_property_read_u32(dev, "height", &height);
	printk(KERN_INFO "Height %d\n", height);
	if ((height == 0) || (height > 320)) {
	  height = 320; // default to full framebuff;
	}

	mi0283qt_mode.hdisplay = mi0283qt_mode.hsync_start = 
	  mi0283qt_mode.hsync_end = mi0283qt_mode.htotal = width;
	mi0283qt_mode.vdisplay = mi0283qt_mode.vsync_start = 
	  mi0283qt_mode.vsync_end = mi0283qt_mode.vtotal = height;


	device_property_read_u32(dev, "col_offset", &col_offset);
	printk(KERN_INFO "Column offset %d\n", col_offset);

	device_property_read_u32(dev, "row_offset", &row_offset);
	printk(KERN_INFO "Row offset %d\n", row_offset);


	ret = mipi_dbi_spi_init(spi, dbi, dc);
	if (ret)
		return ret;

	/* Cannot read from this controller via SPI */
    dbi->read_commands = NULL;

	ret = mipi_dbi_dev_init(dbidev, &mi0283qt_pipe_funcs, &mi0283qt_mode, rotation);
	if (ret)
		return ret;

	drm_mode_config_reset(drm);

	ret = drm_dev_register(drm, 0);
	if (ret)
		return ret;

	spi_set_drvdata(spi, drm);

	drm_fbdev_generic_setup(drm, 0);

	return 0;
}

static int mi0283qt_remove(struct spi_device *spi)
{
	struct drm_device *drm = spi_get_drvdata(spi);

	drm_dev_unplug(drm);
	drm_atomic_helper_shutdown(drm);

	return 0;
}

static void mi0283qt_shutdown(struct spi_device *spi)
{
	drm_atomic_helper_shutdown(spi_get_drvdata(spi));
}

static int __maybe_unused mi0283qt_pm_suspend(struct device *dev)
{
	return drm_mode_config_helper_suspend(dev_get_drvdata(dev));
}

static int __maybe_unused mi0283qt_pm_resume(struct device *dev)
{
	drm_mode_config_helper_resume(dev_get_drvdata(dev));

	return 0;
}

static const struct dev_pm_ops mi0283qt_pm_ops = {
	SET_SYSTEM_SLEEP_PM_OPS(mi0283qt_pm_suspend, mi0283qt_pm_resume)
};

static struct spi_driver mi0283qt_spi_driver = {
	.driver = {
		.name = "mi0283qt",
		.owner = THIS_MODULE,
		.of_match_table = mi0283qt_of_match,
		.pm = &mi0283qt_pm_ops,
	},
	.id_table = mi0283qt_id,
	.probe = mi0283qt_probe,
	.remove = mi0283qt_remove,
	.shutdown = mi0283qt_shutdown,
};
module_spi_driver(mi0283qt_spi_driver);

MODULE_DESCRIPTION("Sitronix ST7789V Flexible DRM driver");
MODULE_AUTHOR("Noralf Trønnes + Limor Fried");
MODULE_LICENSE("GPL");
