MOD_NAME	:= snd-i2smic-rpi

ifneq ($(KERNELRELEASE),)

# call from kernel build system

all:
	@echo "Building from the kernel build system"
	@echo "Module build: $(CONFIG_SND_I2S_RPI)"
	@echo "Name: $(MOD_NAME)"

obj-$(CONFIG_SND_I2S_RPI) := $(MOD_NAME).o

else
# external module build

EXTRA_FLAGS += -I$(PWD)

#
# KDIR is a path to a directory containing kernel source.
# It can be specified on the command line passed to make to enable the module to
# be built and installed for a kernel other than the one currently running.
# By default it is the path to the symbolic link created when
# the current kernel's modules were installed, but
# any valid path to the directory in which the target kernel's source is located
# can be provided on the command line.
#
KDIR	?= /lib/modules/$(shell uname -r)/build
MDIR	?= /lib/modules/$(shell uname -r)
PWD	:= $(shell pwd)

export CONFIG_SND_I2S_RPI := m

all:
	$(MAKE) -C $(KDIR) M=$(PWD) modules

clean:
	$(MAKE) -C $(KDIR) M=$(PWD) clean

help:
	$(MAKE) -C $(KDIR) M=$(PWD) help

install: snd-i2smic-rpi.ko
	rm -f ${MDIR}/kernel/sound/drivers/$(MOD_NAME).ko
	install -m644 -b -D $(MOD_NAME).ko ${MDIR}/kernel/sound/drivers/$(MOD_NAME).ko
	depmod -a

uninstall:
	rm -rf ${MDIR}/kernel/sound/drivers/$(MOD_NAME).ko
	depmod -a

endif

.PHONY : all clean install uninstall
