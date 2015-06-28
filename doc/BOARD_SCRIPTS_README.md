Board Scripts README
====================
Explanation
-----------
- Board Scripts are simple bash scripts that are called after installation of all package groups, packages, the kernel, setting of root password, authorized ssh key and setting of SELinux Status.

- They take the following arguments 

        DISKIMAGE=$1
        STAGE1LOADER=$2
        UBOOT=$3
        ROOTPATH=$4
        ROOTFILES=$5
        ROOTPARTINDEX=$6
        ROOTUUID=$7
        
- ***$DISKIMAGE*** is the block device on which the rootfs is being created. 
  Use this variable to write your bootloader to the block device (Disk Image).
  
- ***$STAGE1LOADER*** contains path to the stage1loader specified in the XML Template.
  Use this to write Stage1 Loader to the block device (Disk Image).
  
- ***$UBOOT*** contains path to U-Boot specified in the XML Template.
  Use this to write the bootloader U-Boot to the block device (Disk Image).

- ***$ROOTPATH*** is where the the new install root is mounted.
  Use this to access and edit any files or directories in the new filesystem.
  
- ***$ROOTFILES*** contains path to rootfiles specified in the XML Template.
  Use this to copy special files (eg. files for /boot) from a tar.
  Note: It can contain path to a directory, tarball or a single file.
  The value from tag rootfiles is directly available in the board script.
  
- ***$ROOTPARTINDEX*** is the index of the root partition from the partition table.
   Use this to setup your boot configuration's *root=/dev/{mmcblk0p,sda}$ROOTPARTINDEX*
   This will be useful if you setup does not include an initramfs.
   
- ***$ROOTUUID*** is the UUID of the root partition from the partition table.
   Use this to setup you boot configuration's *root=UUID=$UUID*
   This will be useful if your setup includes an initramfs and you want to pass the *root=*
   parameter using an *UUID*.

- Use ***exit 0*** to tell RBF that the board script executed successfully. Any other exit code will prompt the user with a message *"BOARD_SCRIPT_ERROR: Error In Board Script. Press Enter To Continue"*

Examples
---------
- ***boards.d/cubietruck.sh*** : Simplest possible board script. Just writes U-Boot to rootfs image.

- ***boards.d/rpi2.sh*** : Extracts *$ROOTFILES* to *$ROOTPATH* and sets up the *root=* parameter in *cmdline.txt* using $ROOTPARTINDEX

- ***boards.d/odroidc1.sh*** : Write U-Boot, then copies a single boot file from *$ROOTFILES* to *$ROOTPATH/boot* and then sets up the root= parameter using *$ROOTUUID*
