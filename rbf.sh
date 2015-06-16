echo [INFO ]   $0 Detacing Loop Device If Busy: /dev/loop0
[ -b /dev/loop0 ] && losetup -d /dev/loop0 &>> rbf.log 
sleep 2
echo [INFO ]    $0 Creating qemu-centos-image-local.img
fallocate -l 4096M qemu-centos-image-local.img &>> rbf.log 
if [ $? != 0 ]; then exit 201; fi

losetup /dev/loop0 qemu-centos-image-local.img &>> rbf.log
if [ $? != 0 ]; then exit 220; fi

echo [INFO ]   $0 Creating Parititons
parted /dev/loop0 --align optimal -s mklabel msdos mkpart primary ext3 2048s 1026047s mkpart primary linux-swap 1026048s 3123199s mkpart primary ext4 3123200s 7317503s  &>> rbf.log 
if [ $? != 0 ]; then exit 202; fi

partprobe /dev/loop0 &>> rbf.log
if [ $? != 0 ]; then exit 221; fi

[ -b /dev/loop0p1 ] && echo [INFO ]   $0 Creating Filesystem ext3 on partition 1 || exit 204
mkfs.ext3 -U adf16082-8a76-4420-84c2-c04a5668c686 /dev/loop0p1 &>> rbf.log 
[ -b /dev/loop0p2 ] && echo [INFO ]   $0 Creating Filesystem swap on partition 2 || exit 204
mkswap -U 88dc06ad-5db6-4bd3-af59-7cd32f59f2f6 /dev/loop0p2 &>> rbf.log 
[ -b /dev/loop0p3 ] && echo [INFO ]   $0 Creating Filesystem ext4 on partition 3 || exit 204
mkfs.ext4 -U 1034c496-82cf-4c8f-9f71-ac8519121cdc /dev/loop0p3 &>> rbf.log 
mkdir -p /tmp/temp
if [ $? != 0 ]; then exit 222; fi

echo [INFO ]   $0 Mouting Parititon 3 on /
mount /dev/loop0p3 /tmp/temp/
if [ $? != 0 ]; then exit 205; fi

mkdir -p /tmp/temp//boot
echo [INFO ]   $0 Mouting Parititon 1 on /boot
mount /dev/loop0p1 /tmp/temp/boot
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

rpm --root /tmp/temp --initdb
if [ $? != 0 ]; then exit 209; fi

echo [INFO ]  $0 Installing Package Groups. Please Wait
yum --disablerepo=* --enablerepo=c7buildroot,c7pass1,comps --installroot=/tmp/temp groupinstall @core 2>> rbf.log
if [ $? != 0 ]; then echo [INFO ]  GROUP_INSTALL_ERROR: Error Installing Some Package Groups;  read -p "Press Enter To Continue"; fi

echo [INFO ]  $0 Installing Packages. Please Wait
yum --disablerepo=* --enablerepo=c7buildroot,c7pass1,comps --installroot=/tmp/temp install net-tools dracut-config-generic kernel 2>> rbf.log
if [ $? != 0 ]; then echo [INFO ]  PACKAGE_INSTALL_ERROR: Error Installing Some Packages;  read -p "Press Enter To Continue"; fi

cp -rpv ./etc /tmp/temp &>> rbf.log 
if [ $? != 0 ]; then exit 212; fi

sed -i 's/root:x:/root::/' /tmp/temp/etc/passwd  &>> rbf.log 
if [ $? != 0 ]; then echo [INFO ]  ROOT_PASS_ERROR: Could Not Set Empty Root Pass;  read -p "Press Enter To Continue"; fi

sed -i 's/SELINUX=enforcing/SELINUX=disabled/' /tmp/temp/etc/selinux/config  &>> rbf.log 
if [ $? != 0 ]; then echo [INFO ]  SELINUX_ERROR: Could Not Set SELINUX Status;  read -p "Press Enter To Continue"; fi

echo [INFO ]  $0 Running Board Script: ./boards.d/qemu.sh /dev/loop0 none none /tmp/temp none 3 1034c496-82cf-4c8f-9f71-ac8519121cdc
./boards.d/qemu.sh /dev/loop0 none none /tmp/temp none 3 1034c496-82cf-4c8f-9f71-ac8519121cdc
if [ $? != 0 ]; then echo [INFO ]  BOARD_SCRIPT_ERROR: Error In Board Script;  read -p "Press Enter To Continue"; fi

echo [INFO ]  $0 Running Finalize Script: ./boards.d/finalize.sh
./boards.d/finalize.sh
if [ $? != 0 ]; then echo [INFO ]  FINALIZE_SCRIPT_ERROR: Error In Finalize Script;  read -p "Press Enter To Continue"; fi

exit 0
