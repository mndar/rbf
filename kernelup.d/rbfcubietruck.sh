#!/usr/bin/bash
DISTRO=$1
KERNELVER=$2
ROOT=$3

#Enter Custom Commands Below
cat >> /boot/extlinux/extlinux.conf << EOF

label $DISTRO $KERNELVER
        kernel /vmlinuz-$KERNELVER
        append enforcing=0 root=$ROOT
        fdtdir /dtb-$KERNELVER
        initrd /initramfs-$KERNELVER.img

EOF
exit 0

