echo [INFO ]   $0 Detacing Loop Device If Busy: /dev/loop1
[ -b /dev/loop1 ] && losetup -d /dev/loop1 &>> rbf.log 
sleep 2
echo [INFO ]    $0 Creating odroidc1-image-local.img
fallocate -l 3072M odroidc1-image-local.img &>> rbf.log 
if [ $? != 0 ]; then exit 201; fi

echo [INFO ]   $0 Creating Parititons
parted odroidc1-image-local.img  --align optimal -s mklabel msdos mkpart primary fat32 2048s 1026047s mkpart primary ext4 1026048s 5220351s  &>> rbf.log 
if [ $? != 0 ]; then echo [INFO ]  PARTED_ERROR: Could Not Partition Image;  read -p "Press Enter To Continue"; fi

losetup /dev/loop1 odroidc1-image-local.img &>> rbf.log
if [ $? != 0 ]; then exit 220; fi

partprobe /dev/loop1 &>> rbf.log
if [ $? != 0 ]; then exit 221; fi

[ -b /dev/loop1p1 ] && echo [INFO ]   $0 Creating Filesystem vfat on partition 1 || exit 204
mkfs.vfat -n 59B4781A /dev/loop1p1 &>> rbf.log 
[ -b /dev/loop1p2 ] && echo [INFO ]   $0 Creating Filesystem ext4 on partition 2 || exit 204
mkfs.ext4 -U 3c53006d-449e-4d59-bdf2-6c13964b9db5 /dev/loop1p2 &>> rbf.log 
mkdir -p /tmp/temp
if [ $? != 0 ]; then exit 222; fi

echo [INFO ]   $0 Mouting Parititon 2 on /
mount /dev/loop1p2 /tmp/temp/
if [ $? != 0 ]; then exit 205; fi

mkdir -p /tmp/temp//boot
echo [INFO ]   $0 Mouting Parititon 1 on /boot
mount /dev/loop1p1 /tmp/temp/boot
if [ $? != 0 ]; then exit 205; fi

mkdir /tmp/temp/proc /tmp/temp/sys
mount -t proc proc /tmp/temp/proc
rm -rf /tmp/temp/etc/yum.repos.d
mkdir -p /tmp/temp/etc/yum.repos.d
cat > /tmp/temp/etc/yum.repos.d/c7buildroot.repo << EOF
[c7buildroot]
name=c7buildroot
baseurl=ftp://192.168.1.3/c7buildroot/
gpgcheck=0
enabled=1
EOF
if [ $? != 0 ]; then exit 206; fi

cat > /tmp/temp/etc/yum.repos.d/c7pass1.repo << EOF
[c7pass1]
name=c7pass1
baseurl=ftp://192.168.1.3/c7pass1/
gpgcheck=0
enabled=1
EOF
if [ $? != 0 ]; then exit 206; fi

cat > /tmp/temp/etc/yum.repos.d/comps.repo << EOF
[comps]
name=comps
baseurl=ftp://192.168.1.3/comps/
gpgcheck=0
enabled=1
EOF
if [ $? != 0 ]; then exit 206; fi

echo [INFO ]  $0 Copying Custom Kernel
cp -rv files/odroidc1/uImage /tmp/temp/boot &>> rbf.log 
if [ $? != 0 ]; then exit 207; fi

cp -rv files/odroidc1/uInitrd /tmp/temp/boot &>> rbf.log 
if [ $? != 0 ]; then exit 207; fi

cp -rv files/odroidc1/meson8b_odroidc.dtb /tmp/temp/boot &>> rbf.log 
if [ $? != 0 ]; then exit 207; fi

echo [INFO ]  $0 Copying Custom Kernel Modules
mkdir -p /tmp/temp/lib/modules &>> rbf.log 
if [ $? != 0 ]; then exit 207; fi

cp -rv files/odroidc1/3.10.66-49 /tmp/temp/lib/modules/ &>> rbf.log 
if [ $? != 0 ]; then exit 207; fi

rpm --root /tmp/temp --initdb
if [ $? != 0 ]; then exit 209; fi

echo [INFO ]  $0 Installing Package Groups. Please Wait
yum --disablerepo=* --enablerepo=c7buildroot,c7pass1,comps --installroot=/tmp/temp groupinstall @core 2>> rbf.log
if [ $? != 0 ]; then echo [INFO ]  GROUP_INSTALL_ERROR: Error Installing Some Package Groups;  read -p "Press Enter To Continue"; fi

cp -rpv ./etc /tmp/temp &>> rbf.log 
if [ $? != 0 ]; then exit 212; fi

sed -i 's/root:x:/root::/' /tmp/temp/etc/passwd  &>> rbf.log 
if [ $? != 0 ]; then echo [INFO ]  ROOT_PASS_ERROR: Could Not Set Empty Root Pass;  read -p "Press Enter To Continue"; fi

sed -i 's/SELINUX=enforcing/SELINUX=disabled/' /tmp/temp/etc/selinux/config  &>> rbf.log 
if [ $? != 0 ]; then echo [INFO ]  SELINUX_ERROR: Could Not Set SELINUX Status;  read -p "Press Enter To Continue"; fi

echo [INFO ]  $0 Running Board Script: ./boards.d/odroidc1.sh odroidc1-image-local.img files/odroid/bl1.bin.hardkernel files/odroidc1/u-boot.bin /tmp/temp files/odroidc1/boot.ini 2 3c53006d-449e-4d59-bdf2-6c13964b9db5
./boards.d/odroidc1.sh odroidc1-image-local.img files/odroid/bl1.bin.hardkernel files/odroidc1/u-boot.bin /tmp/temp files/odroidc1/boot.ini 2 3c53006d-449e-4d59-bdf2-6c13964b9db5
if [ $? != 0 ]; then echo [INFO ]  BOARD_SCRIPT_ERROR: Error In Board Script;  read -p "Press Enter To Continue"; fi

echo [INFO ]  $0 Running Finalize Script: ./boards.d/finalize.sh
./boards.d/finalize.sh
if [ $? != 0 ]; then echo [INFO ]  FINALIZE_SCRIPT_ERROR: Error In Finalize Script;  read -p "Press Enter To Continue"; fi

exit 0
