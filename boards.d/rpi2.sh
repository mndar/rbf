#!/usr/bin/bash
DISKIMAGE=$1
UBOOT=$2
ROOTPATH=$3
ROOTFILES=$4

#Enter Custom Commands Below
echo "Extracting Boot Files"
tar xvf $ROOTFILES -C $ROOTPATH

exit 0
