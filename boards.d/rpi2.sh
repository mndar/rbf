#!/usr/bin/bash
DISKIMAGE=$1
UBOOT=$2
ROOTPATH=$3
ROOTFILES=$4
ROOTPARTINDEX=$5

#Enter Custom Commands Below
echo "Extracting Boot Files"
tar Jxvf $ROOTFILES -C $ROOTPATH
sed -i 's/mmcblk0p3/mmcblk0p'$ROOTPARTINDEX'/' $ROOTPATH/boot/cmdline.txt
exit 0
