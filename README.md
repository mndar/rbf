RootFS Build Factory
Being developed for Google Summer Of Code 2015
Organization: CentOS
Written By: Mandar Joshi [emailmandar at gmail.com]
Mentor: Ian McLeod [imcleod at redhat.com]

This project is still in the development stage.
I've tested it with Fedora 21 ARM and CentOS 7 ARM repositories


Usage of rbf.py:
Note: One of the initial checks rbf.py makes is if you have the required programs to generate images. My test setup is Fedora 21 ARM on Cubietruck

1.  Edit template/cubietruck.xml and set image path in the image tag

2.  Set repository information as per your distro. templates/cubietruck.xml and templates/rpi2.xml are bare minimum ones.
    You can even specify a local repository if you have one. The provided info is used as baseurl.

3.  To just parse the XML Template
    ./rbf.py parse templates/cubietruck.xml

4.  To Also build image. You need to be root
    ./rbf.py build templates/cubietruck.xml

5.  Follow the output of the script. 
    Presently it prompts you to press Enter after every step.
    The script uses the yum command to installpackages. The yum command asks you whether to continue with y/d/N after resolving dependencies.

6.  Once the image is generated write it your microsd card using dd or dcfldd
    Eg. dcfldd if=cubietruck-centos-image.img of=/dev/sdb 

7.  Just login as root. No password is required. 
    The default config of u-boot is set as console=ttyS0,115200
    If you want to see the boot messages you will need a USB to TTL Cable.
    The provided u-boot for cubietruck supports HDMI console. However USB Keyboard is not supported.
    
8.  With the Cubietruck, once booted you will get the login prompt on tty0.

9.  Default network config is left alone.

10. You can experiment with different templates. You can use custom built kernels too. See templates/cubietruck_centos.xml
    The group and package tags in the packages element take comma separated package names as well.

Known Issues:

1.  While installing @core in CentOS, sometimes yum gives following messages for these two packages. However the image generated is bootable.
    Note: rbf.py just uses yum --installroot to install packages.
    
    Installing :filesystem-3.2-18.el7.armv7hl
    error: unpacking of archive failed on file /lib: cpio: rename
    error: filesystem-3.2-18.el7.armv7hl: install failed
    
    Installing : glibc-common-2.17-78.el7.armv7hl
    error: unpacking of archive failed on file /usr/share/locale/be/LC_MESSAGES/libc.mo;00000e3c: cpio: open
    error: glibc-common-2.17-78.el7.armv7hl: install failed
    
2.  This happens with the Cubietruck at times. It has happened to me twice after plugging in the HDMI cable.
    It boots from NAND flash instead of the microsd card. Just rebooting by pressing the button on the side fixes the problem for me.
    
    
Usage of scripts in commonscripts:

1.  expandimage.sh $FILE $EXPANDBY
    Expands $FILE by $EXPAND. Uses fallocate to expand the provided file
    Eg. commonscripts/expandimage.sh disk.img 4096M

2.  loopdevcreate.sh $FILE $LOOPDEVICE
    Creates a loop back device for provide partition. Can be use to create /dev/loop* for partition from raw disk image.
    Eg. commonscripts/loopdevcreate.sh disk.img /dev/loop0
    To Detach, use losetup -d
    Eg. losetup -d /dev/loop0
    
3.  mountpart.sh $FILE $PARTITION $MOUNTPOINT
    Mounts specified partition from disk image to mount point.
    Eg. commonscripts/mountpart.sh disk.img 1 /media/pendrive/
    

Usage of yumplugins/extlinuxconf.py:

This is part of Target 6
This plugin appends entries to /boot/extlinux/extlinux.conf everytime kernel-core is installed or updated.
Thus making your new kernel bootable.

1.  Copy yumplugins/extlinuxconf.py to /usr/lib/yum-plugins/
    and  yumplugins/extlinuxconf.conf to /etc/yum/pluginconf.d/
    cp yumplugins/extlinuxconf.py /usr/lib/yum-plugins/
    cp yumplugins/extlinuxconf.conf /etc/yum/pluginconf.d/
    

Note: The files in the directory files/* have been taken from Fedora 21
