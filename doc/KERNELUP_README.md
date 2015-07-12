Kernel Upgrade Scripts README
====================
Explanation
-----------
- Every board has a different kernel requirements. If the distribution kernel supports the given board (either directly or via some conversion from the distribution kernel), this feature of RBF makes it possible to alter the kernel related stuff via a simple bash script. The script is named rbf(boardname).sh and is present in the kernelup.d directory. It is copied to /usr/sbin in the installroot during image generation.

- The dnf/yum plugin rbfkernelup.py reads the board name from /etc/rbf/board.xml and looks for *rbf(boardname).sh*. The script is executed when the kernel-core package is installed or upgraded.

- The script is called with the following arguments

        DISTRO=$1
        KERNELVER=$2
        ROOT=$3
        
- ***$DISTRO*** is the name of the distribution determined from /etc/redhat-release. If this file is missing the distro name in /etc/rbf/board.xml is used. Use this to name your boot entry.

- ***$KERNELVER*** is the kernel version installed by dnf/yum. The plugin looks for package kernel-core and uses its suffix as $KERNELVER. Use this to determine filename of the kernel files eg. *vmlinuz-$KERNELVER*, *initramfs-$KERNELVER*, *dtb-$KERNELVER*

- ***$ROOT*** is the path to your root device (can be UUID too) determined by reading /proc/cmdline. Use this to setup your root parameter in the boot config.

Examples
---------
- ***kernelup.d/rbfcubietruck.sh***: Adds a kernel entry to */boot/extlinux/extlinux.conf*. This script is not required if you have the *extlinux-bootloader* package installed. You can use this as an example for writing board scripts for other boards.
