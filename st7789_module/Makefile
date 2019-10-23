obj-m+=st7789v_ada.o

KDIR ?= /lib/modules/`uname -r`/build

default:
	$(MAKE) -C $(KDIR) M=$(pwd) modules

install:
	$(MAKE) -C $(KDIR) M=$(PWD) modules_install
	$(DEPMOD)

clean:
	$(MAKE) -C $(KDIR) M=$(PWD) clean

