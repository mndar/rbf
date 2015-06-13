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

dd if=$STAGE1LOADER of=$DISKIMAGE bs=1 count=442
dd if=$STAGE1LOADER of=$DISKIMAGE bs=512 skip=1 seek=1
dd if=$UBOOT of=$DISKIMAGE bs=512 seek=64
cp $ROOTFILES $ROOTPATH/boot/
sed -i 's/UUID/UUID='$ROOTUUID'/' $ROOTPATH/boot/boot.ini
exit 0
