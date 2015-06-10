#!/usr/bin/bash
FILE=$1
PARTITION=$2
MOUNTPOINT=$3
OFFSET=`fdisk -b512 -l $FILE|grep $FILE$PARTITION|awk '{print $2}'`
mount -o loop,offset=$(($OFFSET*512)) $FILE $MOUNTPOINT

