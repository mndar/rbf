#!/usr/bin/bash
FILE=$1
LOOPDEVICE=$2
losetup $LOOPDEVICE $FILE
partprobe $LOOPDEVICE
echo To Detach, Run \"losetup -d $LOOPDEVICE\"
