#!/usr/bin/bash
DISKIMAGE=$1
UBOOT=$2
ROOTPATH=$3
ROOTFILES=$4

#Enter Custom Commands Below
echo "Writing U-Boot Image"
dd if=$UBOOT of=$DISKIMAGE bs=1024 seek=8 conv=fsync,notrunc

exit 0
