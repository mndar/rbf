#!/usr/bin/bash

IMAGE=$1
DEVICE=$2

if ! [ -b $DEVICE ]
then
    echo "$DEVICE is not a block device"
    exit 1
fi

if [ -f $IMAGE ]
then
    echo "Image $IMAGE Found"
    
    DEVICE_NAME=${DEVICE//\/dev\//}
    DEVICE_MODEL=`cat /sys/class/block/$DEVICE_NAME/device/model|tr -d '[[:space:]]'`
    DEVICE_VENDOR=`cat /sys/class/block/$DEVICE_NAME/device/vendor|tr -d '[[:space:]]'`


    read -p "Are you sure you want to write $IMAGE to $DEVICE [$DEVICE_VENDOR $DEVICE_MODEL]?(yes/no): " RESPONSE

    if [ $RESPONSE == "yes" ]
    then
        echo "Writing Image"
        dd if=$IMAGE of=$DEVICE
        echo "Done!!"
    else
        echo "Not Writing Image. Exiting"
    fi
else
    echo "Image $IMAGE not Found"
    exit 2
fi
