echo [INFO ]   $0 Detacing Loop Device If Busy: /dev/loop1
[ -b /dev/loop1 ] && losetup -d /dev/loop1 &>> rbf.log 
sleep 2
echo [INFO ]    $0 Creating cubietruck-centos-image.img
fallocate -l 4096M cubietruck-centos-image.img &>> rbf.log 
if [ $? != 0 ]; then exit 201; fi

echo [INFO ]   $0 Creating Parititons
parted cubietruck-centos-image.img -s mklabel msdos mkpart primary ext3 1 501 mkpart primary linux-swap 501 1525 mkpart primary ext4 1525 3573  &>> rbf.log 
if [ $? != 0 ]; then exit 202; fi

losetup /dev/loop1 cubietruck-centos-image.img
partprobe /dev/loop1
sleep 2
[ -b /dev/loop1p1 ] && echo [INFO ]   $0 Creating Filesystem ext3 on partition 1 || exit 204
mkfs.ext3 -U 5ca9de03-9f5c-4272-a170-75e6369bef13 /dev/loop1p1 &>> rbf.log 
[ -b /dev/loop1p2 ] && echo [INFO ]   $0 Creating Filesystem swap on partition 2 || exit 204
mkswap -U 94fbdbeb-13a8-4ddc-8d48-3980e144b8df /dev/loop1p2 &>> rbf.log 
[ -b /dev/loop1p3 ] && echo [INFO ]   $0 Creating Filesystem ext4 on partition 3 || exit 204
mkfs.ext4 -U d40fb7bf-1345-4e50-be13-a4881a60acc7 /dev/loop1p3 &>> rbf.log 
mkdir -p /tmp/temp
echo [INFO ]   $0 Mouting Parititon 3 on /
mount /dev/loop1p3 /tmp/temp/
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
baseurl=http://armv7.dev.centos.org/repodir/c7-buildroot/
gpgcheck=0
enabled=1
EOF
if [ $? != 0 ]; then exit 206; fi

cat > /tmp/temp/etc/yum.repos.d/c7pass1.repo << EOF
[c7pass1]
name=c7pass1
baseurl=http://armv7.dev.centos.org/repodir/c7-pass-1/
gpgcheck=0
enabled=1
EOF
if [ $? != 0 ]; then exit 206; fi

cat > /tmp/temp/etc/yum.repos.d/comps.repo << EOF
[comps]
name=comps
baseurl=http://armv7.dev.centos.org/repodir/comps/
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
yum --disablerepo=* --enablerepo=c7buildroot,c7pass1,comps --installroot=/tmp/temp install net-tools kernel 2>> rbf.log
if [ $? != 0 ]; then echo [INFO ]  PACKAGE_INSTALL_ERROR: Error Installing Some Packages;  read -p "Press Enter To Continue"; fi

cp -rpv ./etc /tmp/temp &>> rbf.log 
if [ $? != 0 ]; then exit 212; fi

sed -i 's/root:x:/root::/' /tmp/temp/etc/passwd  &>> rbf.log 
if [ $? != 0 ]; then echo [INFO ]  ROOT_PASS_ERROR: Could Not Set Empty Root Pass;  read -p "Press Enter To Continue"; fi

sed -i 's/SELINUX=enforcing/SELINUX=disabled/' /tmp/temp/etc/selinux/config  &>> rbf.log 
if [ $? != 0 ]; then echo [INFO ]  SELINUX_ERROR: Could Not Set SELINUX Status;  read -p "Press Enter To Continue"; fi

echo [INFO ]  $0 Running Board Script: boards.d/cubietruck.sh
./boards.d/cubietruck.sh cubietruck-centos-image.img files/u-boot-sunxi-with-spl.bin /tmp/temp none
if [ $? != 0 ]; then exit 215; fi

echo [INFO ]  $0 Running Finalize Script: ./boards.d/finalize.sh
./boards.d/finalize.sh
if [ $? != 0 ]; then exit 216; fi

exit 0
