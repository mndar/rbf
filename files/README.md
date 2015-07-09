U-Boot and Kernel Files
--------------
- Contents of this directory have been compiled from various sources. 
- F21 X86_64 was used as the development box
- Cross Compiler Used: gcc-linaro-4.9-2014.11-x86_64_arm-linux-gnueabihf.tar.xz https://releases.linaro.org/14.11/components/toolchain/binaries/arm-linux-gnueabihf
        
- U-Boot Binaries in {cubietruck,bananapi,cubieboard,cubieboard2,beaglebone,pandaboard} have been cross compiled from the u-boot git repo git://git.denx.de/u-boot.git

        cp configs/Bananapi_defconfig .config
        make ARCH=arm CROSS_COMPILE=/opt/gcc-linaro-4.9-2014.11-x86_64_arm-linux-gnueabihf/bin/arm-linux-gnueabihf- menuconfig
        make ARCH=arm CROSS_COMPILE=/opt/gcc-linaro-4.9-2014.11-x86_64_arm-linux-gnueabihf/bin/arm-linux-gnueabihf- -j4
        
- The files in the directory files/rpi2 have been taken from https://github.com/raspberrypi/firmware.git. config.txt and cmdlinux.txt from F21

- The kernel files/odroidc1 have been taken from *Ubuntu 14.04* downloaded from http://odroid.com/dokuwiki/doku.php?id=en:c1_ubuntu_minimal. The u-boot files have been compiled from sources at https://github.com/hardkernel/u-boot.git. Instructions to compile: http://odroid.com/dokuwiki/doku.php?id=en:c1_building_u-boot

- files/wandboard* have been taken from http://wiki.wandboard.org/index.php/Sdcard-images
