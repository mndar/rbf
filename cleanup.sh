umount /tmp/temp/boot
umount /tmp/temp/mnt
umount /tmp/temp/home
umount /tmp/temp/var
umount /tmp/temp/proc
umount /tmp/temp
[ -b /dev/loop0 ] && losetup -d /dev/loop0 &>> rbf.log 
sleep 2
exit 0
