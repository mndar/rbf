RootFS Build Factory
====================
Being developed for Google Summer Of Code 2015
----------------------------------------------
*Organization: CentOS*

*Written By: Mandar Joshi [emailmandar at gmail.com]*

*Mentor: Ian McLeod [imcleod at redhat.com]*


This project is still in the development stage.
I've tested it with Fedora 21 ARM and CentOS 7 ARM repositories

**Tested Emulators**
- Qemu

**Tested Boards**
- Cubietruck
- Odroid C1
- Raspberry Pi 2
- Banana Pi (Tested By Nicolas [nicolas at shivaserv.fr])

**Untested Boards**
- Cubieboard
- Cubieboard 2
- Wandboard{solo,dual,quad}
- Pandaboard
- CompuLab TrimSlice
- Beaglebone


If you have any of the untested boards, please test the RootFS Build Factory and let us know the results. You can email me [emailmandar at gmail.com]

**Usage of rbf.py:**

Note: One of the initial checks rbf.py makes is if you have the required programs to generate images. My test setup is Fedora 21 ARM on Cubietruck

- Edit template/cubietruck.xml and set image path in the image tag

- Set repository information as per your distro. templates/cubietruck.xml and templates/rpi2.xml are bare minimum ones.
  You can even specify a local repository if you have one. The provided info is used as baseurl.

- To just parse the XML Template
  ./rbf.py parse templates/cubietruck.xml

- To Also build image. You need to be root
  ./rbf.py build templates/cubietruck.xml

- Follow the output of the script. 
  Presently it prompts you to press Enter after every step.
  The script uses the yum command to installpackages. The yum command asks you whether to continue with y/d/N after resolving dependencies.

- Once the image is generated write it your microsd card using dd or dcfldd
  Eg. dcfldd if=cubietruck-centos-image.img of=/dev/sdb 

- Just login as root. No password is required. 
  The default config of u-boot is set as console=ttyS0,115200
  If you want to see the boot messages you will need a USB to TTL Cable.
  The provided u-boot for cubietruck supports HDMI console. However USB Keyboard is not supported.
    
- With the Cubietruck, once booted you will get the login prompt on tty0.

- You can experiment with different templates. You can use custom built kernels too. See templates/cubietruck_centos.xml
  
- The group and package tags in the packages element take comma separated package names as well.

**Known Issues:**

- While installing @core in CentOS, sometimes yum gives following messages for these two packages. However the image generated is bootable.
    Note: rbf.py just uses yum --installroot to install packages.
    
    Installing :filesystem-3.2-18.el7.armv7hl
    error: unpacking of archive failed on file /lib: cpio: rename
    error: filesystem-3.2-18.el7.armv7hl: install failed
    
    Installing : glibc-common-2.17-78.el7.armv7hl
    error: unpacking of archive failed on file /usr/share/locale/be/LC_MESSAGES/libc.mo;00000e3c: cpio: open
    error: glibc-common-2.17-78.el7.armv7hl: install failed
    
- This happens with the Cubietruck at times. It has happened to me twice after plugging in the HDMI cable.
    It boots from NAND flash instead of the microsd card. Just rebooting by pressing the button on the side fixes the problem for me.
    
- DBus, NetworkManager don't start on the Raspberry Pi 2 and ODroid C1. Have to run dhclient manually.
  To fix this you need to copy dbus.service and dbus.socket from /lib/systemd/system/ to /usr/lib/systemd/system and create a symlink for dbus.socket in dbus.target.wants
  
        cd /usr/lib/systemd/system
        cp /lib/systemd/system/dbus.s* .
        cd dbus.target.wants/
        ln -s ../dbus.socket .
        reboot

**Usage of scripts in commonscripts:**

- expandimage.sh $FILE $EXPANDBY
    Expands $FILE by $EXPAND. Uses fallocate to expand the provided file
    
        commonscripts/expandimage.sh disk.img 4096M

- loopdevcreate.sh $FILE $LOOPDEVICE
    Creates a loop back device for provide partition. Can be use to create /dev/loop* for partition from raw disk image.
    
        commonscripts/loopdevcreate.sh disk.img /dev/loop0
    To Detach, use losetup -d
    
        losetup -d /dev/loop0
    
- mountpart.sh $FILE $PARTITION $MOUNTPOINT
    Mounts specified partition from disk image to mount point.
    
        commonscripts/mountpart.sh disk.img 1 /media/pendrive/
    
- writeimage.sh $FILE $DEVICE
    Informs user which device will be written to (displays vendor and model) before executing the dd command
    
        commonscripts/writeimage.sh centos.img /dev/sdd

**Usage of yumplugins/extlinuxconf.py:**

This plugin appends entries to /boot/extlinux/extlinux.conf everytime kernel-core is installed or updated.
Thus making your new kernel bootable.

- Copy yumplugins/extlinuxconf.py to /usr/lib/yum-plugins/
  and  yumplugins/extlinuxconf.conf to /etc/yum/pluginconf.d/
  
        cp yumplugins/extlinuxconf.py /usr/lib/yum-plugins/
        cp yumplugins/extlinuxconf.conf /etc/yum/pluginconf.d/
    

**Note:**
- The files in the directory files/rpi2 have been taken from https://github.com/raspberrypi/firmware.git. config.txt and cmdlinux.txt from F21
- files/cubietruck/u-boot-sunxi-with-spl.bin has been cross compiled from the u-boot git repo git://git.denx.de/u-boot.git
- The kernel files/odroidc1 have been taken from Ubuntu 14.04. The u-boot files have been compiled from sources at https://github.com/hardkernel/u-boot.git
- The rpms directory has RPMs generated from sources available here http://pythondialog.sourceforge.net/
- files/{bananapi,cubieboard,cubieboard2,beaglebone,pandaboard} have been cross compiled from the u-boot git repo git://git.denx.de/u-boot.git
- files/wandboard* have been taken from http://wiki.wandboard.org/index.php/Sdcard-images
