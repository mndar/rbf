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

dd if=$STAGE1LOADER of=$DISKIMAGE count=1 seek=1 conv=notrunc bs=128k
dd if=$UBOOT of=$DISKIMAGE count=2 seek=1 conv=notrunc bs=384k
exit 0
