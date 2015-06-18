echo [INFO ]   $0 Detacing Loop Device If Busy: /dev/loop0
[ -b /dev/loop0 ] && losetup -d /dev/loop0 &>> rbf.log 
sleep 2
echo [INFO ]    $0 Creating cubietruck-centos-image.img
fallocate -l 4096M cubietruck-centos-image.img &>> rbf.log 
if [ $? != 0 ]; then exit 201; fi

losetup /dev/loop0 cubietruck-centos-image.img &>> rbf.log
if [ $? != 0 ]; then exit 220; fi

echo [INFO ]   $0 Creating Parititons
parted /dev/loop0 --align optimal -s mklabel msdos mkpart primary ext3 2048s 1026047s mkpart primary linux-swap 1026048s 3123199s mkpart primary ext4 3123200s 7317503s  &>> rbf.log 
if [ $? != 0 ]; then exit 202; fi

partprobe /dev/loop0 &>> rbf.log
if [ $? != 0 ]; then exit 221; fi

[ -b /dev/loop0p1 ] && echo [INFO ]   $0 Creating Filesystem ext3 on partition 1 || exit 204
mkfs.ext3 -U 42892d65-37d6-4ba1-8b65-81bbbc73a371 /dev/loop0p1 &>> rbf.log 
[ -b /dev/loop0p2 ] && echo [INFO ]   $0 Creating Filesystem swap on partition 2 || exit 204
mkswap -U cf69ac77-8a9e-49cb-9bb4-cc890f51abbf /dev/loop0p2 &>> rbf.log 
[ -b /dev/loop0p3 ] && echo [INFO ]   $0 Creating Filesystem ext4 on partition 3 || exit 204
mkfs.ext4 -U 47667d48-a4e0-4d98-9c40-c99b56657d0b /dev/loop0p3 &>> rbf.log 
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
yum --disablerepo=* --enablerepo=c7buildroot,c7pass1,comps --installroot=/tmp/temp install net-tools dracut-config-generic kernel 2>> rbf.log
if [ $? != 0 ]; then echo [INFO ]  PACKAGE_INSTALL_ERROR: Error Installing Some Packages;  read -p "Press Enter To Continue"; fi

