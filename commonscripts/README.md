RootFS Build Factory
====================
Common Scripts Usage
----------------------------------------------
**changeuuid.py**

- Changes UUID and LABEL of ext* and vfat partitions respectively. Also updates relevant boot config files (/etc/fstab, /extlinux/extlinux.conf and /boot.ini (Odroid C1))
- You need to execute the script as 'root'
- Uses 'blkid' to obtain information about UUID/LABEL and filesystem type
- Make sure you have unmounted all partitions on the device before executing this script.
- Has two operations 'pretend' and 'change'. 'pretend' just shows you what is going to be changed. (UUID, LABEL and boot config files). 'change' performs the actual changes.
- It doesn't depend on any other files in the RootFS Build Factory repo. You can just download this script and use it.
- Usage 

        ./changeuuid.py <change|pretend> <device> <mountpoint>
- 'change' or 'pretend' are actions
- 'device' is the device on which you wrote your image eg. /dev/sdb or /dev/mmcblk0 etc.
- 'mountpoint' is any empty directory
- Examples

        ./changeuuid.py pretend /dev/sdb /tmp/temp/
        ./changeuuid.py change /dev/sdb /tmp/temp/
        
- If you want to perform the changes on the raw *.img file, set it up on a loopback device and run partprobe on it before using changeuuid.py

        losetup /dev/loop0 CentOS-Userland-7-armv7hl-Minimal-1511-CubieTruck.img
        partprobe /dev/loop0
        ./changeuuid.py change /dev/loop0 /tmp/temp/
        losetup -d /dev/loop0
        
- Tested with CentOS 7 ARM and Fedora 23 ARM Minimal images on CentOS 7 x86\_64, Fedora 23 x86\_64, CentOS 7 ARM and Fedora 23 ARM.
- You need to install python2 with "**dnf install python2**" on Fedora 23 ARM. More testing/changes are in my TODO list.
- The output on stdout has a lot of debug information. Post it if something goes wrong and you need help.
