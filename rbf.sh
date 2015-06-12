echo [INFO ]   $0 Detacing Loop Device If Busy: /dev/loop1
[ -b /dev/loop1 ] && losetup -d /dev/loop1 &>> rbf.log 
sleep 2
echo [INFO ]    $0 Creating rpi2-image.img
fallocate -l 4096M rpi2-image.img &>> rbf.log 
if [ $? != 0 ]; then exit 201; fi

