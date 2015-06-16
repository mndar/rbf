mkdir /tmp/temp/boot/extlinux
if [ $? != 0 ]; then exit 217; fi

cat > /tmp/temp/boot/extlinux/extlinux.conf << EOF
#Created by RootFS Build Factory
ui menu.c32
menu autoboot centos
menu title centos Options
#menu hidden
timeout 60
totaltimeout 600
EOF
if [ $? != 0 ]; then exit 217; fi

