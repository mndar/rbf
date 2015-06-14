echo [INFO ]   $0 Detacing Loop Device If Busy: /dev/loop0
[ -b /dev/loop0 ] && losetup -d /dev/loop0 &>> rbf.log 
sleep 2
echo [INFO ]    $0 Creating rpi2-image.img
fallocate -l 4096M rpi2-image.img &>> rbf.log 
if [ $? != 0 ]; then exit 201; fi

losetup /dev/loop0 rpi2-image.img &>> rbf.log
if [ $? != 0 ]; then exit 220; fi

echo [INFO ]   $0 Creating Parititons
parted /dev/loop0 --align optimal -s mklabel msdos mkpart primary fat32 2048s 1026047s mkpart extended  1026048s 5122047s mkpart logical ext4 1028096s 3076095s mkpart logical ext4 3078144s 5122047s mkpart primary ext4 5122048s 7170047s mkpart primary ext4 7170048s 8388607s  &>> rbf.log 
if [ $? != 0 ]; then echo [INFO ]  PARTED_ERROR: Could Not Partition Image;  read -p "Press Enter To Continue"; fi

partprobe /dev/loop0 &>> rbf.log
if [ $? != 0 ]; then exit 221; fi

[ -b /dev/loop0p1 ] && echo [INFO ]   $0 Creating Filesystem vfat on partition 1 || exit 204
mkfs.vfat -n B1909B3F /dev/loop0p1 &>> rbf.log 
[ -b /dev/loop0p5 ] && echo [INFO ]   $0 Creating Filesystem ext4 on partition 5 || exit 204
mkfs.ext4 -U 0399bec4-6ded-4dfd-91a8-9cf9987a223b /dev/loop0p5 &>> rbf.log 
[ -b /dev/loop0p6 ] && echo [INFO ]   $0 Creating Filesystem ext4 on partition 6 || exit 204
mkfs.ext4 -U 3f6df543-0c69-4de2-b880-b4aa6cb85657 /dev/loop0p6 &>> rbf.log 
[ -b /dev/loop0p3 ] && echo [INFO ]   $0 Creating Filesystem ext4 on partition 3 || exit 204
mkfs.ext4 -U ce25c52f-fce9-49a8-857d-41159da5f013 /dev/loop0p3 &>> rbf.log 
[ -b /dev/loop0p4 ] && echo [INFO ]   $0 Creating Filesystem ext4 on partition 4 || exit 204
mkfs.ext4 -U 9f68fa73-d067-440d-8a02-d425bdd0de9f /dev/loop0p4 &>> rbf.log 
mkdir -p /tmp/temp
if [ $? != 0 ]; then exit 222; fi

echo [INFO ]   $0 Mouting Parititon 5 on /
mount /dev/loop0p5 /tmp/temp/
if [ $? != 0 ]; then exit 205; fi

mkdir -p /tmp/temp//boot
mkdir -p /tmp/temp/
mkdir -p /tmp/temp//mnt
mkdir -p /tmp/temp//home
mkdir -p /tmp/temp//var
echo [INFO ]   $0 Mouting Parititon 1 on /boot
mount /dev/loop0p1 /tmp/temp/boot
if [ $? != 0 ]; then exit 205; fi

echo [INFO ]   $0 Mouting Parititon 6 on /mnt
mount /dev/loop0p6 /tmp/temp/mnt
if [ $? != 0 ]; then exit 205; fi

echo [INFO ]   $0 Mouting Parititon 3 on /home
mount /dev/loop0p3 /tmp/temp/home
if [ $? != 0 ]; then exit 205; fi

echo [INFO ]   $0 Mouting Parititon 4 on /var
mount /dev/loop0p4 /tmp/temp/var
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
cp -rv files/rpi2/kernel7.img /tmp/temp/boot &>> rbf.log 
if [ $? != 0 ]; then exit 207; fi

echo [INFO ]  $0 Copying Custom Kernel Modules
mkdir -p /tmp/temp/lib/modules &>> rbf.log 
if [ $? != 0 ]; then exit 207; fi

cp -rv files/rpi2/3.18.14-v7+ /tmp/temp/lib/modules/ &>> rbf.log 
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

echo [INFO ]  $0 Running Board Script: ./boards.d/rpi2.sh /dev/loop0 none none /tmp/temp files/rpi2/boot_rpi2.tar.xz 5 0399bec4-6ded-4dfd-91a8-9cf9987a223b
./boards.d/rpi2.sh /dev/loop0 none none /tmp/temp files/rpi2/boot_rpi2.tar.xz 5 0399bec4-6ded-4dfd-91a8-9cf9987a223b
if [ $? != 0 ]; then echo [INFO ]  BOARD_SCRIPT_ERROR: Error In Board Script;  read -p "Press Enter To Continue"; fi

echo [INFO ]  $0 Running Finalize Script: ./boards.d/finalize.sh
./boards.d/finalize.sh
if [ $? != 0 ]; then echo [INFO ]  FINALIZE_SCRIPT_ERROR: Error In Finalize Script;  read -p "Press Enter To Continue"; fi

exit 0
