#!/usr/bin/bash
DISKIMAGE=$1
STAGE1LOADER=$2
UBOOT=$3
ROOTPATH=$4
ROOTFILES=$5
ROOTPARTINDEX=$6
ROOTUUID=$7

#Enter Custom Commands Below
echo "Extracting Boot Files"
tar Jxvomf $ROOTFILES -C $ROOTPATH
sed -i 's/mmcblk0p3/mmcblk0p'$ROOTPARTINDEX'/' $ROOTPATH/boot/cmdline.txt
sed -i 's/IPv6_rpfilter=yes/IPv6_rpfilter=no/' $ROOTPATH/etc/firewalld/firewalld.conf
exit 0
