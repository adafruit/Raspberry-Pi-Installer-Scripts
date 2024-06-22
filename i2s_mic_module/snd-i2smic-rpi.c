/*
 * =====================================================================================
 *
 *       Filename:  snd-i2smic-rpi
 *
 *    Description:  I2S microphone kernel module
 *
 *        Version:  0.1.0
 *        Created:  2020-04-14
 *       Revision:  none
 *       Compiler:  gcc
 *
 *       Pi4 Mods:  Carter Nelson
 *    Orig Author:  Huan Truong (htruong@tnhh.net), originally written by Paul Creaser
 *
 * =====================================================================================
 */
#include <linux/module.h>
#include <linux/moduleparam.h>
#include <linux/kernel.h>
#include <linux/kmod.h>
#include <linux/platform_device.h>
#include <sound/soc.h>
#include <linux/delay.h>
#include "snd-i2smic-rpi.h"

/*
 * modified for linux 4.1.5
 * inspired by https://github.com/msperl/spi-config
 * with thanks for https://github.com/notro/rpi-source/wiki
 * as well as Florian Meier for the rpi i2s and dma drivers
 *
 * to use a differant (simple-card compatible) codec
 * change the codec name string in two places and the
 * codec_dai name string. (see codec's source file)
 *
 *
 * N.B. playback vs capture is determined by the codec choice
 * */

static struct snd_soc_card snd_rpi_i2s_card;
static struct platform_device *pdev;

/*
 * Setup command line parameter
 */
static short rpi_platform_generation;
module_param(rpi_platform_generation, short, 0);
MODULE_PARM_DESC(rpi_platform_generation, "Raspberry Pi generation: 0=Pi0, 1=Pi2/3, 2=Pi4");

/*
 * Dummy callback for release
 */
void device_release_callback(struct device *dev) { /*  do nothing */ };

static struct snd_soc_dai_link_component cpu_component = {
  .name = "not-set.i2s",
};

static struct snd_soc_dai_link_component codec_component = {
  .name = "snd-soc-dummy-dai",
};

static struct snd_soc_dai_link_component platform_component = {
  .name = "not-set.i2s",
};

static struct snd_soc_dai_link dai_link = {
  .name = "simple-card_codec_link",
  .stream_name = "simple-card_codec_link",
  .cpus = &cpu_component,
  .num_cpus = 1,
  .codecs = &codec_component,
  .num_codecs = 1,
  .platforms = &platform_component,
  .num_platforms = 1,
  .dai_fmt = SND_SOC_DAIFMT_I2S | SND_SOC_DAIFMT_NB_NF | SND_SOC_DAIFMT_CBS_CFS,
};

static struct snd_soc_card snd_rpi_i2s_card = {
  .name = "snd_rpi_i2s_card",
  .dai_link = &dai_link,
  .num_links = 1,
};

/*
 * Callback for module initialization
 */
int i2s_mic_rpi_init(void)
{
  const char *dmaengine = "bcm2708-dmaengine"; //module name
  static char *card_platform;
  int ret;

  printk(KERN_INFO "snd-i2smic-rpi: Version %s\n", SND_I2SMIC_RPI_VERSION);

  // Set platform
  switch (rpi_platform_generation) {
    case 0:
      // Pi Zero
      card_platform = "20203000.i2s";
      break;
    case 1:
      // Pi 2 and 3
      card_platform = "3f203000.i2s";
      break;
    case 2:
    default:
      // Pi 4
      card_platform = "fe203000.i2s";
      break;
  }

  printk(KERN_INFO "snd-i2smic-rpi: Setting platform to %s\n", card_platform);

  // request DMA engine module
  ret = request_module(dmaengine);
  pr_alert("request module load '%s': %d\n", dmaengine, ret);

  // update info
  cpu_component.name = card_platform;
  platform_component.name = card_platform;

  // register the card device
  pdev = platform_device_alloc("asoc-simple-card", -1);
  if (!pdev) {
    pr_err("snd-i2smic-rpi: platform_device_alloc failed\n");
    return -ENOMEM;
  }

  pdev->dev.release = device_release_callback;
  pdev->dev.platform_data = &snd_rpi_i2s_card;

  ret = platform_device_add(pdev);
  if (ret) {
    pr_err("snd-i2smic-rpi: platform_device_add failed: %d\n", ret);
    platform_device_put(pdev);
    return ret;
  }

  pr_alert("register platform device '%s': %d\n", pdev->name, ret);

  return 0;
}

/*
 * Callback for module exit
 */
void i2s_mic_rpi_exit(void)
{
  platform_device_unregister(pdev);
  pr_alert("i2s mic module unloaded\n");
}

// Plumb it up
module_init(i2s_mic_rpi_init);
module_exit(i2s_mic_rpi_exit);
MODULE_DESCRIPTION("ASoC simple-card I2S Microphone");
MODULE_AUTHOR("Carter Nelson");
MODULE_LICENSE("GPL v2");
