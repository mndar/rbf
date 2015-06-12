umount /tmp/temp/boot
umount /tmp/temp/mnt
umount /tmp/temp/opt
umount /tmp/temp/proc
umount /tmp/temp
[ -b /dev/loop1 ] && losetup -d /dev/loop1 &>> rbf.log 
sleep 2
exit 0
