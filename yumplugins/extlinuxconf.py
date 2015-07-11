"""@package extlinuxconf plugin
Configure /boot/extlinux/extlinux.conf on kernel updates
"""
import os
import re
from yum.plugins import TYPE_CORE

requires_api_version = '2.5'
plugin_type = TYPE_CORE


def getPartitionPathFromFstab(mountPoint):
    """Get Partition From fstab"""
    fstab = open("/etc/fstab", "r")
    fstabContents = fstab.readlines()
    fstab.close()
    r = re.compile('[ \t]+')
    for fstabLine in fstabContents:
        fstabLine = fstabLine.strip()
        if not fstabLine.startswith("#"):
            lineContents = r.split(fstabLine)
            if len(lineContents) < 6:
                continue
            if lineContents[1] == mountPoint:
                return lineContents[0]
    return None

def posttrans_hook(conduit):
    """Post Transaction Hook"""
    rootPath = getPartitionPathFromFstab("/")
    if rootPath == None:
        conduit.error(2, "Could not find path to / in fstab." \
                      + "Please fix boot configuration manually")
        return
    try:
        redhatReleaseFile = open("/etc/redhat-release", "r")
        redhatRelease = redhatReleaseFile.readlines()[0].strip()
        redhatReleaseFile.close()
    except IOError:
        conduit.info(2, "Could not determine Distribution. Using Linux As Name")
        redhatRelease = "Linux"

    tsInfo = conduit.getTsInfo()
    for txmbr in tsInfo:
        packageName = txmbr.po.name
        packageState = txmbr.ts_state
        conduit.info(2, packageName + " " + packageState)
        if (packageState == "i" or packageState == "u") and \
            packageName.startswith("kernel-core"):
            conduit.info(2, "Appending /boot/extlinux/extlinux.conf")
            installedKernels = os.listdir("/lib/modules")
            if not os.path.exists("/boot/extlinux"):
                os.makedirs("/boot/extlinux")
            extlinuxConfFile = open("/boot/extlinux/extlinux.conf", "a")
            for kernelVer in installedKernels:
                extlinuxContents = "\nlabel " + redhatRelease + " " + \
                kernelVer + "\n\t" + "kernel /vmlinuz-" + kernelVer + \
                "\n\tappend enforcing=0 root=" + rootPath + \
                "\n\tfdtdir /dtb-" + kernelVer + "\n\tinitrd /initramfs-" + \
                kernelVer + ".img\n\n"
                extlinuxConfFile.write(extlinuxContents)
            extlinuxConfFile.close()

