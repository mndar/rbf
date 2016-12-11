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
dd if=$UBOOT of=$DISKIMAGE bs=512 seek=97
cp $ROOTFILES $ROOTPATH/boot/
sed -i 's/UUID/UUID='$ROOTUUID'/' $ROOTPATH/boot/boot.ini

echo "armv5tel-redhat-linux-gnu" > $ROOTPATH/etc/rpm/platform

echo "remove rbf repos"
rm $ROOTPATH/etc/yum.repos.d/*_rbf.repo

echo "remove yum cache"
rm -rf $ROOTPATH/var/cache/yum/*

echo "zero the disks freespace"
dd if=/dev/zero of=$ROOTPATH/zero
dd if=/dev/zero of=$ROOTPATH/boot/zero
sync
rm -f $ROOTPATH/zero $ROOTPATH/boot/zero

exit 0
