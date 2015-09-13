dd if="/disks/sdb1/newcentos/qemu-centos-image.img" of=/dev/sde bs=1M
boards.d/cubietruck.sh /dev/sde none files/cubietruck/u-boot-sunxi-with-spl.bin
sync
