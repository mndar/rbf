#!/usr/bin/bash
DISKIMAGE=$1
STAGE1LOADER=$2
UBOOT=$3
ROOTPATH=$4
ROOTFILES=$5
ROOTPARTINDEX=$6
ROOTUUID=$7

#Enter Custom Commands Below
echo "Writing U-Boot Image"
dd if=$UBOOT of=$DISKIMAGE bs=512 seek=2

exit 0
