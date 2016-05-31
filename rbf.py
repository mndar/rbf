#!/usr/bin/python
# pylint: disable=

"""@package parser
Parser for Board XML Template

Parses provided XML Template
"""

import os
import subprocess
import sys
import platform
import logging
import uuid
from xml.dom.minidom import parse, Document
from xml.parsers.expat import ExpatError
from rbfutils import RbfUtils


def printUsage():
    """Prints Usage"""
    logging.info("./rbf.py <parse|build> <xmlTemplate.xml>")


def initLogging():
    """Initialize Logging"""
    logFormatter = logging.Formatter("[%(levelname)-5.5s]  %(message)s")
    rootLogger = logging.getLogger()
    rootLogger.setLevel(logging.INFO)
    if os.path.exists("rbf.log"):
        os.remove("rbf.log")
    fileHandler = logging.FileHandler("rbf.log")
    fileHandler.setFormatter(logFormatter)
    rootLogger.addHandler(fileHandler)

    consoleHandler = logging.StreamHandler()
    consoleHandler.setFormatter(logFormatter)
    rootLogger.addHandler(consoleHandler)


def checkCommandExistsAccess(commandList):
    """Checks if commands in the command list are present in the system & are
    executable"""
    osPathList = os.environ["PATH"].split(":")
    notFoundList = []
    notExecList = []
    for command in commandList:
        commandExists = False
        for path in osPathList:
            fullPath = path + "/" + command
            if os.path.exists(fullPath):
                commandExists = True
                break
        if commandExists:
            if os.access(fullPath, os.X_OK):
                continue
            else:
                notExecList.append(command)
        else:
            notFoundList.append(command)

    if len(notFoundList) != 0:
        notFoundString = ""
        for command in notFoundList:
            notFoundString = notFoundString + command + ", "

        notFoundString = notFoundString[0:-2]
        logging.error("Commands Not Found: " + notFoundString)

    if len(notExecList) != 0:
        notExecString = ""
        for command in notExecList:
            notExecString = notExecString + command + ", "

        notExecString = notExecString[0:-2]
        logging.error("Commands Not Executable: " + notExecString)

    if len(notFoundList) == 0 and len(notExecList) == 0:
        return True
    else:
        return False


class BoardTemplateParser(object):
    """BoardTemplateParser Class.

    Parses XML Template and performs required actions on image file
    """
    INDEX, SIZE, BEGIN, PTYPE, FS, MOUNTPOINT, UUID = range(0, 7)

    INCORRECT_ARGUMENTS, ERROR_PARSING_XML, ERROR_PARSING_XML_TAGS,\
    ERROR_IMAGE_SIZE, ERROR_IMAGE_FILE, INVALID_PARTITION_DATA, NO_PACKAGES,\
    NO_KERNEL_TYPE, INCORRECT_REPOSITORY, IMAGE_EXISTS,\
    LOGICAL_PART_ERROR, PRIMARY_PART_ERROR, NO_PARTITIONS_FOUND,\
    PRIMARY_PARTITION_SIZES_ERROR, LOGICAL_PARTITION_SIZES_ERROR, FSTAB_ERROR,\
    CLEANUP_ERROR, NOT_ROOT, COMMANDS_NOT_FOUND, SYS_MKFS_COMMANDS_NOT_FOUND,\
    NO_FIRMWARE_FOUND, TEMPLATE_NOT_FOUND, TOTAL_PARTITIONS_ERROR,\
    NO_ROOT_FOUND, SSH_KEY_NOT_FOUND, NO_NETWORK, NO_REPOSITORY, NO_INSTALLER\
     = range(100, 128)

    DD_ERROR, PARTED_ERROR,\
    LOOP_DEVICE_CREATE_ERROR, PARTITION_DOES_NOT_EXIST, MOUNTING_ERROR,\
    WRITE_REPO_ERROR, COPY_KERNEL_ERROR, COPY_FIRMWARE_ERROR, RPMDB_INIT_ERROR,\
    GROUP_INSTALL_ERROR, PACKAGE_INSTALL_ERROR, ETC_OVERLAY_ERROR,\
    ROOT_PASS_ERROR, ROOT_SSH_KEY_ERROR, SELINUX_ERROR, BOARD_SCRIPT_ERROR,\
    FINALIZE_SCRIPT_ERROR, EXTLINUXCONF_ERROR, NO_ETC_OVERLAY,\
    LOOP_DEVICE_DELETE_ERROR, LOSETUP_ERROR, PARTPROBE_ERROR,\
    COULD_NOT_CREATE_WORKDIR, KERNEL_PACKAGE_INSTALL_ERROR, KERNELUP_ERROR\
     = range(200, 225)

    RbfScriptErrors = {
        DD_ERROR: "DD_ERROR: Error While Creating Image File",
        PARTED_ERROR: "PARTED_ERROR: Could Not Partition Image",
        LOOP_DEVICE_CREATE_ERROR: "LOOP_DEVICE_CREATE_ERROR: Could Not Create"\
         + " Loop Device. Device Might Be Busy. Check \"losetup -l\"",
        PARTITION_DOES_NOT_EXIST: "PARTITION_DOES_NOT_EXIST: Could Not Find "\
         + "Specified Partition",
        MOUNTING_ERROR: "MOUNTING_ERROR: Could Not Mount Partitions",
        WRITE_REPO_ERROR: "WRITE_REPO_ERROR: Could Not Write Repo Files",
        COPY_KERNEL_ERROR: "COPY_KERNEL_ERROR: Could Not Copy Kernel",
        COPY_FIRMWARE_ERROR: "COPY_FIRMWARE_ERROR: Could Not Copy Firmware",
        RPMDB_INIT_ERROR: "RPMDB_INIT_ERROR: Could Not Init RPM DB",
        GROUP_INSTALL_ERROR: "GROUP_INSTALL_ERROR: Error Installing Some "\
         + "Package Groups",
        PACKAGE_INSTALL_ERROR: "PACKAGE_INSTALL_ERROR: Error Installing Some "\
         + "Packages",
        ETC_OVERLAY_ERROR: "ETC_OVERLAY_ERROR: Could Not Copy /etc Overlay",
        ROOT_PASS_ERROR: "ROOT_PASS_ERROR: Could Not Set Root Pass",
        ROOT_SSH_KEY_ERROR: "ROOT_SSH_KEY_ERROR: Could Not Setup root ssh key",
        SELINUX_ERROR: "SELINUX_ERROR: Could Not Set SELINUX Status",
        BOARD_SCRIPT_ERROR: "BOARD_SCRIPT_ERROR: Error In Board Script",
        FINALIZE_SCRIPT_ERROR: "FINALIZE_SCRIPT_ERROR: Error In Finalize "\
         + "Script",
        EXTLINUXCONF_ERROR: "EXTLINUXCONF_ERROR: Error Creating "\
         + "/boot/extlinux/extlinux.conf",
        NO_ETC_OVERLAY: "NO_ETC_OVERLAY: No Etc Overlay Found",
        LOOP_DEVICE_DELETE_ERROR: "LOOP_DEVICE_DELETE_ERROR: Could Not Delete "\
        + "Loop Device. Device Might Be Busy. Check \"losetup -l\"",
        LOSETUP_ERROR: "LOSETUP_ERROR: Something went wrong while setting up "\
         + "the loopback device",
        PARTPROBE_ERROR: "PARTPROBE_ERROR: Probing Parititons Failed",
        COULD_NOT_CREATE_WORKDIR: "COULD_NOT_CREATE_WORKDIR: Could not create "\
        + "work directory",
        KERNEL_PACKAGE_INSTALL_ERROR: "KERNEL_PACKAGE_INSTALL_ERROR: Error "\
         + "installing Kernel Packages",
        KERNELUP_ERROR: "KERNELUP_ERROR: Could not copy kernel upgrade script"
    }

    def __init__(self, act, template):
        """Constructor for BoardTemplateParser"""
        logging.info("Xml Template: " + template)
        self.action = act
        self.imagePath = ""
        self.xmlTemplate = template
        self.boardDom = None
        self.workDir = ""
        self.packageGroups = []
        self.packages = []
        self.rbfUtils = RbfUtils()
        self.imageData = []
        self.stockKernels = []
        self.repoNames = []
        self.rbfScript = open("rbf.sh", "w")
        self.initramfsScript = None
        self.boardScript = None
        self.cleanupScript = None
        self.rootSshKey = "none"
        self.rootFiles = "none"
        self.loopDevice = None
        self.hostName = "localhost"
        self.rootPass = "password1234"
        self.kernelPath = "none"
        self.reposDom = []
        self.selinuxConf = "disabled"
        self.finalizeScript = "none"
        self.initrdPath = "none"
        self.firmwareDir = "none"
        self.dtbDir = "none"
        self.ubootPath = "none"
        self.linuxDistro = "none"
        self.stage1Loader = "none"
        self.imageSize = "0M"
        self.rootDeviceUUID = None
        self.etcOverlay = "none"
        self.extlinuxConf = "false"
        self.kernelType = "none"
        self.boardName = "custom"
        self.rootDeviceIndex = 3
        self.packageInstaller = ""
        self.releaseVer = ""

    def __del__(self):
        """Destructor for BoardTemplateParser"""
        self.rbfScript.close()

    @classmethod
    def getTagValue(cls, dom, domTag):
        """Extracts Tag Value from DOMTree"""
        xmlTag = dom.getElementsByTagName(domTag)[0]
        return xmlTag.firstChild.data

    def setTemplate(self, filename):
        """Set XML Template"""
        self.xmlTemplate = filename

    def parseTemplate(self):
        """Parses xmlTemplate"""
        logging.info("Parsing: " + self.xmlTemplate)
        try:
            self.boardDom = parse(self.xmlTemplate)
        except ExpatError as error:
            logging.error("Error Parsing XML Template File: " + str(error))
            return BoardTemplateParser.ERROR_PARSING_XML

        try:
            self.boardName = self.getTagValue(self.boardDom, "board")
            self.workDir = self.getTagValue(self.boardDom, "workdir")
            self.finalizeScript = self.getTagValue(self.boardDom,\
                                                   "finalizescript")
            self.loopDevice = subprocess.check_output(['losetup', '-f']).strip()
            self.selinuxConf = self.getTagValue(self.boardDom, "selinux")
            self.etcOverlay = self.getTagValue(self.boardDom, "etcoverlay")
            self.linuxDistro = self.getTagValue(self.boardDom, "distro")
            self.extlinuxConf = self.getTagValue(self.boardDom, "extlinuxconf")
            self.hostName = self.getTagValue(self.boardDom, "hostname")
            self.rootFiles = self.getTagValue(self.boardDom, "rootfiles")
            self.stage1Loader = self.getTagValue(self.boardDom, "stage1loader")
            self.ubootPath = self.getTagValue(self.boardDom, "uboot")
            self.firmwareDir = self.getTagValue(self.boardDom, "firmware")
            self.rootPass = self.getTagValue(self.boardDom, "rootpass")
            self.rootSshKey = self.getTagValue(self.boardDom, "rootsshkey")
            self.releaseVer = self.getTagValue(self.boardDom, "releasever")
            self.packageInstaller = self.getTagValue(self.boardDom, "installer")
            if not checkCommandExistsAccess([self.packageInstaller]):
                logging.error("Please install " + self.packageInstaller)
                return BoardTemplateParser.NO_INSTALLER
        except IndexError as error:
            logging.error("Error While Reading XML Tags: " + str(error))
            return BoardTemplateParser.ERROR_PARSING_XML_TAGS

        logging.info("Successfully Parsed Board Template For: "\
                     + self.boardName)
        return 0

    @classmethod
    def getShellExitString(cls, exitCode):
        """Generates Shell Exit command. Used to check command execution"""
        return "if [ $? != 0 ]; then exit " + str(exitCode) + "; fi\n\n"

    def getShellErrorString(self, exitCode):
        """Generates Shell Error command. Used to check command execution"""
        return "if [ $? != 0 ]; then echo [INFO ]  "\
                + self.RbfScriptErrors[exitCode] + ";"\
                + " read -p \"Press Enter To Continue\"; fi\n\n"

    def getPackageErrorString(self, exitCode):
        """Generates Shell Error command. Used to check command execution"""
        return "if [ $? != 0 ]; then echo [INFO ]  "\
                + self.RbfScriptErrors[exitCode] + "; read -p "\
                + "\"Retry (y/n)? \" -n 1 ACTION; if [ \"$ACTION\" == \"y\" ]; "\
                + "then continue; else break; fi; else break; fi\n"

    def createImage(self):
        """Creates Image File"""
        self.rbfScript.write("echo [INFO ]   $0 Detaching Loopback Device: "
                             + self.loopDevice + "\n")
        self.rbfScript.write(self.delDeviceIfExists(self.loopDevice))
        logging.info("Creating Image File")
        imageDom = self.boardDom.getElementsByTagName("image")[0]
        if imageDom.hasAttribute("size") and imageDom.hasAttribute("type") and\
           imageDom.hasAttribute("path"):
            self.imageSize = imageDom.getAttribute("size")
            imageType = imageDom.getAttribute("type")
            self.imagePath = imageDom.getAttribute("path")
            if self.imageSize[-1:] in ("M", "G") and\
               self.rbfUtils.isSizeInt(self.imageSize[0:-1]):
                logging.info("Creating Image: " + self.imageSize + " "
                             + imageType + " " + self.imagePath)
            else:
                logging.error("Invalid Image Size: " + self.imageSize + " (Has "
                              + "to be an Integer with suffix M for MB and G " +
                              " for GB)")
                return BoardTemplateParser.ERROR_IMAGE_SIZE
        else:
            logging.error("No image tag found or image tag incomplete.")
            return BoardTemplateParser.ERROR_IMAGE_FILE

        self.imageSize = self.rbfUtils.getImageSizeInM(self.imageSize)

        if os.path.exists(self.imagePath):
            logging.error("Image Already Exists")
            return BoardTemplateParser.IMAGE_EXISTS

        self.rbfScript.write("echo [INFO ]    $0 Creating " + self.imagePath
                             + "\n")
        self.rbfScript.write("dd if=/dev/zero of=\"" + self.imagePath + "\" " +
                             "bs=1M count=0 seek=" + self.imageSize[0:-1] + " "
                             + "&>> rbf.log \n")
        self.rbfScript.write(self.getShellExitString(BoardTemplateParser\
                                                     .DD_ERROR))
        return 0

    def verifyPrimaryPartitionSizes(self, partitionsDom):
        """Check if Primary & Extended part size is exceeding total img size"""
        logging.info("Verifying that Primary & Extended partition sizes doesn't"
                     +" exceed image size")
        partitionSizeSum = 0
        foundRoot = False
        for partitions in partitionsDom:
            partition = partitions.getElementsByTagName("partition")
            for p in partition:
                if p.getAttribute("mountpoint") == "/":
                    foundRoot = True
                if p.getAttribute("type") == "logical":
                    continue
                sizeString = p.getAttribute("size")
                sizeNumber = sizeString[0:-1]
                if not self.rbfUtils.isSizeInt(sizeNumber):
                    logging.error("Primary Parititon Size Error. Only Integers "
                                  + "with suffix G or M allowed. You Specified "
                                  + sizeString)
                    return False
                size = self.rbfUtils.getImageSizeInM(sizeString)
                sizeSuffix = size[-1:]
                if not (sizeSuffix == "M" or sizeSuffix == "G"):
                    logging.error("Primary Parititon Size Error. Only Integers "
                                  + "with suffix G or M allowed. You Specified "
                                  + sizeString)
                    return False
                partitionSizeSum = partitionSizeSum + int(size[0:-1])
        logging.info("Image Size: " + self.imageSize + " Parititon Size Sum: "
                     + str(partitionSizeSum) + "M")
        if not foundRoot:
            logging.error("No Root Found. Check Parititon Data")
            return False
        if int(self.imageSize[0:-1]) >= partitionSizeSum:
            return True
        else:
            logging.error("Primary Parititon Sizes Exceed Image Size")
            return False

    def verifyLogicalPartitionSizes(self, partitionsDom):
        """Check if Logical part size is exceeding Extended part size"""
        logging.info("Verifying that Logical partition sizes don't exceed "\
                      + "Extended partition image size")
        extendedPartitionSize = "OM"
        logicalPartitionSizeSum = 0
        for partitions in partitionsDom:
            partition = partitions.getElementsByTagName("partition")
            extendedPartitionSize = "0M"
            for p in partition:
                ptype = p.getAttribute("type")
                if ptype == "primary":
                    continue
                if ptype == "extended":
                    extendedPartitionSize = self.rbfUtils.getImageSizeInM(\
                                                         p.getAttribute("size"))
                    logging.info("Extended Parititon Size: "
                                 + extendedPartitionSize)
                    continue
                if ptype == "logical":
                    sizeString = p.getAttribute("size")
                    logging.info("Found Logical Paritition: " + sizeString)
                    sizeNumber = sizeString[0:-1]
                    if not self.rbfUtils.isSizeInt(sizeNumber):
                        logging.error("Logical Parititon Size Error. Only "\
                        + "Integers with suffix G or M allowed. You Specified "\
                        + sizeString)
                        return False
                    size = self.rbfUtils.getImageSizeInM(sizeString)

                    sizeSuffix = size[-1:]
                    if not (sizeSuffix == "M" or sizeSuffix == "G"):
                        logging.error("Logical Parititon Size Error. Only "\
                        + "Integers with suffix G or M allowed. You Specified "\
                        + sizeString)
                        return False
                    logicalPartitionSizeSum = logicalPartitionSizeSum + \
                                              int(size[0:-1])
            if int(extendedPartitionSize[0:-1]) >= logicalPartitionSizeSum:
                return True
            else:
                logging.error("Logical Parititon Sizes Exceed Extended " + \
                " Parititon Size")
                return False

    def createPartitions(self):
        """Creates Partitions"""
        logging.info("Creating Partitions")
        partitionsDom = self.boardDom.getElementsByTagName("partitions")

        if partitionsDom == []:
            logging.error("No Partitions Found")
            return BoardTemplateParser.NO_PARTITIONS_FOUND

        if not self.verifyPrimaryPartitionSizes(partitionsDom):
            return BoardTemplateParser.PRIMARY_PARTITION_SIZES_ERROR

        if not self.verifyLogicalPartitionSizes(partitionsDom):
            return BoardTemplateParser.LOGICAL_PARTITION_SIZES_ERROR

        self.rbfScript.write("losetup " + self.loopDevice + " \"" +\
                                            self.imagePath + "\" &>> rbf.log\n")
        self.rbfScript.write(self.getShellExitString(\
                                             BoardTemplateParser.LOSETUP_ERROR))

        partedString = "parted " + self.loopDevice + " --align optimal -s "\
                        + "mklabel msdos "
        extendedStart = False
        extendedStartSector = "0"
        extendedEndSector = "0"
        primaryEndSector = "0"
        logicalEndSector = "0"
        primaryPartitionCount = 0
        logicalPartitionCount = 0
        begin = self.rbfUtils.PARTITION_BEGIN
        imageEnd = self.rbfUtils.calcParitionEndSector("0", self.imageSize)
        for partitions in partitionsDom:
            partition = partitions.getElementsByTagName("partition")
            for p in partition:
                partuuid = str(uuid.uuid4())
                if p.hasAttribute("size") and p.hasAttribute("type") and \
                p.hasAttribute("fs") and p.hasAttribute("mountpoint"):
                    size = self.rbfUtils.getImageSizeInM(p.getAttribute("size"))
                    ptype = p.getAttribute("type")
                    fs = p.getAttribute("fs")
                    mountpoint = p.getAttribute("mountpoint")

                    if fs == "vfat":
                        partuuid = partuuid.upper()[:8]

                    if extendedStart is True and ptype == "extended":
                        logging.error("Cannot have more than 1 extended "\
                        + "paritition")
                        return BoardTemplateParser.INVALID_PARTITION_DATA

                    if ptype == "logical" and extendedStart is False:
                        logging.error("Cannot Create Logical Parititon before "\
                        + "Extended")
                        return BoardTemplateParser.LOGICAL_PART_ERROR

                    if (ptype == "primary" or ptype == "extended") and \
                    primaryPartitionCount == 4:
                        logging.error("Cannot Have More Than 4 Primary "\
                        + "Partitions")
                        return BoardTemplateParser.TOTAL_PARTITIONS_ERROR

                    if ptype == "primary" or ptype == "extended":
                        primaryPartitionCount = primaryPartitionCount + 1
                        index = str(primaryPartitionCount)

                    # Adjust partition indexes. parted seems to create logical
                    # partitions from index 5
                    if ptype == "logical":
                        index = str(self.rbfUtils.LOGICAL_PARTITION_START_INDEX\
                                     + logicalPartitionCount)
                        logicalPartitionCount = logicalPartitionCount + 1

                    if mountpoint == "/":
                        self.rootDeviceIndex = index
                        self.rootDeviceUUID = partuuid
                    # ignore filesystem and mountpoint for extended partition
                    if ptype == "extended" and extendedStart == False:
                        fs = ""
                        mountpoint = ""
                        extendedStart = True
                        extendedStartSector = str(int(primaryEndSector) + 1)
                        extendedEndSector = \
                            self.rbfUtils.calcParitionEndSector(\
                                                      extendedStartSector, size)

                    # fix mountpoint for swap
                    if fs == "swap":
                        mountpoint = "swap"

                    # if this is the first partition start at sector 2048
                    if primaryPartitionCount == 1:
                        begin = self.rbfUtils.PARTITION_BEGIN
                        end = self.rbfUtils.calcParitionEndSector(begin, size)
                        primaryEndSector = end
                    elif ptype in ("primary", "extended"):
                        begin = str(int(primaryEndSector) + 1)
                        end = self.rbfUtils.calcParitionEndSector(begin, size)
                        # don't go beyond image end
                        if int(end) > int(imageEnd):
                            end = imageEnd
                        if ptype == "primary":
                            primaryEndSector = end
                        elif ptype == "extended":
                            extendedEndSector = end
                            primaryEndSector = extendedEndSector
                    elif ptype == "logical" and logicalPartitionCount == 1:
                        # need to start first logical partitions after 2048
                        # sectors
                        begin = str(int(extendedStartSector) + \
                                int(self.rbfUtils.PARTITION_BEGIN))
                        end = self.rbfUtils.calcParitionEndSector(begin, size)
                        # don't go beyong extended sector end
                        if int(end) > int(extendedEndSector):
                            end = extendedEndSector
                        logicalEndSector = end
                    elif ptype == "logical" and logicalPartitionCount > 1:
                        # need to start new logical partitions after 2049
                        # sectors
                        begin = str(int(logicalEndSector) + \
                                int(self.rbfUtils.PARTITION_BEGIN) + 1)
                        end = self.rbfUtils.calcParitionEndSector(begin, size)
                        logging.info("Logical: " + begin + " " + end)
                        # don't go beyong extended sector end
                        if int(end) > int(extendedEndSector):
                            end = extendedEndSector
                        logicalEndSector = end

                    logging.info("Creating Partition " + index + " " + size + \
                    " " + ptype + " " + fs + " " + mountpoint + " " + partuuid)

                    x = [index, size, begin, ptype, fs, mountpoint, partuuid]
                    self.imageData.append(x)

                    # parted names swap as linux-swap and vfat as fat32
                    if fs == "swap":
                        fs = "linux-swap"
                    elif fs == "vfat":
                        fs = "fat32"
                    partedString = partedString + "mkpart " + ptype + " " + fs \
                                   + " " + begin + "s " + end + "s "
                else:
                    logging.error("Invalid Partition Data")
                    return BoardTemplateParser.INVALID_PARTITION_DATA

            self.rbfScript.write("echo [INFO ]   $0 Creating Parititons\n")
            self.rbfScript.write(partedString + " &>> rbf.log \n")
            self.rbfScript.write(self.getShellExitString(\
                                            BoardTemplateParser.PARTED_ERROR))
            return 0

    @classmethod
    def delDeviceIfExists(cls, device):
        """Generates command to detach loop device if it exists"""
        return "[ -b " + device + " ] && losetup -d " + device + \
               " &>> rbf.log\n"

    def createFilesystems(self):
        """Creates Filesystem"""
        self.rbfScript.write("partprobe " + self.loopDevice + " &>> rbf.log\n")
        self.rbfScript.write(self.getShellExitString(\
                                           BoardTemplateParser.PARTPROBE_ERROR))
        for i in range(0, len(self.imageData)):
            if self.imageData[i][BoardTemplateParser.PTYPE] == "extended":
                continue
            fs = self.imageData[i][BoardTemplateParser.FS]
            index = self.imageData[i][BoardTemplateParser.INDEX]
            partuuid = self.imageData[i][BoardTemplateParser.UUID]

            self.rbfScript.write("[ -b " + self.loopDevice + "p" + index\
            + " ] && echo [INFO ]   $0 Creating Filesystem " + fs\
            + " on partition " + index + " || exit "\
            + str(BoardTemplateParser.PARTITION_DOES_NOT_EXIST) + "\n")

            if fs == "vfat":
                if not checkCommandExistsAccess(['mkfs.vfat']):
                    logging.error("Please Install mkfs.vfat")
                    return BoardTemplateParser.SYS_MKFS_COMMANDS_NOT_FOUND
                self.rbfScript.write("mkfs.vfat -n " + partuuid + " " + \
                              self.loopDevice + "p" + index + " &>> rbf.log \n")
            elif fs == "swap":
                if not checkCommandExistsAccess(['mkswap']):
                    logging.error("Please Install mkswap")
                    return BoardTemplateParser.SYS_MKFS_COMMANDS_NOT_FOUND
                self.rbfScript.write("mkswap -U " + partuuid + " " + \
                              self.loopDevice + "p" + index + " &>> rbf.log \n")
            else:
                if not checkCommandExistsAccess(['mkfs.'+fs]):
                    logging.error("Please Install mkfs."+fs)
                    return BoardTemplateParser.SYS_MKFS_COMMANDS_NOT_FOUND
                self.rbfScript.write("mkfs." + fs + " -U " + partuuid + " " + \
                              self.loopDevice + "p" + index + " &>> rbf.log \n")
        return 0

    def mountPartitions(self):
        """Mounting Partitions"""
        logging.info("Mounting Partitions")
        self.rbfScript.write("mkdir -p " + self.workDir + "\n")
        self.rbfScript.write(self.getShellExitString(\
                                  BoardTemplateParser.COULD_NOT_CREATE_WORKDIR))
        for i in range(0, len(self.imageData)):
            index = self.imageData[i][BoardTemplateParser.INDEX]
            mountpoint = self.imageData[i][BoardTemplateParser.MOUNTPOINT]
            if mountpoint == "/":
                logging.info("Mounting Parititon " + index + " on " + \
                              self.workDir + mountpoint)
                self.rbfScript.write("echo [INFO ]   $0 Mouting Parititon " + \
                                      index + " on " + mountpoint+"\n")
                self.rbfScript.write("mount " + self.loopDevice + "p" + index \
                                        + " " +self.workDir + mountpoint + "\n")
                self.rbfScript.write(self.getShellExitString(\
                                            BoardTemplateParser.MOUNTING_ERROR))
                for j in range(0, len(self.imageData)):
                    pm = self.imageData[j][BoardTemplateParser.MOUNTPOINT]
                    if pm not in ("/", "swap", ""):
                        self.rbfScript.write("mkdir -p " + self.workDir + \
                                              mountpoint + pm + "\n")


        for i in range(0, len(self.imageData)):
            if self.imageData[i][BoardTemplateParser.PTYPE] == "extended":
                continue
            index = self.imageData[i][BoardTemplateParser.INDEX]
            mountpoint = self.imageData[i][BoardTemplateParser.MOUNTPOINT]
            if mountpoint not in ("/", "swap", ""):
                logging.info("Mounting Parititon " + index + " on " + \
                              self.workDir + mountpoint)
                self.rbfScript.write("echo [INFO ]   $0 Mouting Parititon " + \
                                      index + " on " + mountpoint+"\n")
                self.rbfScript.write("mount " + self.loopDevice + "p" + index \
                                     + " " +self.workDir + mountpoint + "\n")
                self.rbfScript.write(self.getShellExitString(\
                                            BoardTemplateParser.MOUNTING_ERROR))

        self.rbfScript.write("mkdir " + self.workDir + "/proc " + self.workDir \
                             + "/sys " + self.workDir + "/dev\n")
        self.rbfScript.write("mount -t proc proc " + self.workDir + "/proc\n")
        self.rbfScript.write("mount --bind /dev " + self.workDir + "/dev\n")

    def writeRepos(self):
        """Writes Repos to /etc/yum.repos.d"""
        self.rbfScript.write("rm -rf " + self.workDir + "/etc/yum.repos.d\n")
        self.rbfScript.write("mkdir -p " + self.workDir + "/etc/yum.repos.d\n")
        self.reposDom = self.boardDom.getElementsByTagName("repos")
        if self.reposDom == []:
            return BoardTemplateParser.NO_REPOSITORY
        for repos in self.reposDom:
            repo = repos.getElementsByTagName("repo")
            for r in repo:
                if not (r.hasAttribute("name") and r.hasAttribute("path")):
                    return BoardTemplateParser.INCORRECT_REPOSITORY
                name = r.getAttribute("name")
                path = r.getAttribute("path")
                logging.info("Found Repo: " + name + " " + path)
                name = name + "_rbf"
                self.repoNames.append(name)
                if self.action == "build" and self.packageInstaller == "dnf":
                    #write repo to host
                    repoFile = open("/etc/yum.repos.d/" + name + ".repo", "w")
                    repoFile.write("[" + name + "]\n")
                    repoFile.write("name=" + name + "\n")
                    repoFile.write("baseurl=" + path + "\n")
                    repoFile.write("gpgcheck=0\nenabled=1\n")
                    repoFile.close()
                #write repo to installroot
                repoString = "cat > " + self.workDir + "/etc/yum.repos.d/" + \
                              name + ".repo << EOF\n"
                repoString = repoString + "[" + name + "]\n"
                repoString = repoString + "name=" + name + "\n"
                repoString = repoString + "baseurl=" + path + "\n"
                repoString = repoString + "gpgcheck=0\nenabled=1\n"
                repoString = repoString + "EOF\n"
                self.rbfScript.write(repoString)
                self.rbfScript.write(self.getShellExitString(\
                                          BoardTemplateParser.WRITE_REPO_ERROR))
        return 0

    @classmethod
    def generatePackageString(cls, packageList):
        """Generates String from supplied List"""
        packageString = ""
        for p in packageList:
            packageString = p + ' ' + packageString
        return packageString

    def installPackages(self):
        """Installing Packages"""
        packagesDom = self.boardDom.getElementsByTagName("packages")
        if packagesDom == []:
            logging.error("No Packages Supplied. Please Fix Template")
            return BoardTemplateParser.NO_PACKAGES

        for packageElement in packagesDom:
            try:
                groupPackageEl = packageElement.getElementsByTagName('group')[0]
                groupPackageString = groupPackageEl.childNodes[0].data
            except IndexError:
                groupPackageString = ""
            p = groupPackageString.split(',')
            for i in range(0, len(p)):
                self.packageGroups.append(p[i])

            try:
                packageEl = packageElement.getElementsByTagName('package')[0]
                packageString = packageEl.childNodes[0].data
            except IndexError:
                packageString = ""
            p = packageString.split(',')
            for i in range(0, len(p)):
                self.packages.append(p[i])

        packageGroupsString = self.generatePackageString(\
                                                     self.packageGroups).strip()
        packagesString = self.generatePackageString(self.packages).strip()
        logging.info("Installing Package Groups: " + packageGroupsString)
        logging.info("Installing Packages: " + packagesString)

        repoEnableString = "--disablerepo=* "
        for r in self.repoNames:
            repoEnableString = repoEnableString + "--enablerepo=" + r + " "
        self.rbfScript.write("rpm --root " + self.workDir + " --initdb\n")
        self.rbfScript.write(self.getShellExitString(\
                                          BoardTemplateParser.RPMDB_INIT_ERROR))
        if len(packageGroupsString) > 0:
            self.rbfScript.write("echo [INFO ]  $0 Installing Package Groups."\
            + " Please Wait\n")
            self.rbfScript.write("while (true)\ndo\n")
            self.rbfScript.write(self.packageInstaller + " " + \
                    repoEnableString + \
                    " --installroot=" + self.workDir + \
                    " --releasever=" + self.releaseVer + " groupinstall -y " + \
                    packageGroupsString+" 2>> rbf.log\n")
            self.rbfScript.write(self.getPackageErrorString(\
                                       BoardTemplateParser.GROUP_INSTALL_ERROR))
            self.rbfScript.write("done\n\n")

        if len(packagesString) > 0:
            self.rbfScript.write("echo [INFO ]  $0 Installing Packages."\
            + " Please Wait\n")
            self.rbfScript.write("while (true)\ndo\n")
            self.rbfScript.write(self.packageInstaller + " " + \
                    repoEnableString + \
                    " --installroot=" + self.workDir + \
                    " --releasever=" + self.releaseVer + " install -y " + \
                    packagesString+" 2>> rbf.log\n")
            self.rbfScript.write(self.getPackageErrorString(\
                                     BoardTemplateParser.PACKAGE_INSTALL_ERROR))
            self.rbfScript.write("done\n\n")
        return 0

    def installKernel(self):
        """Installing Kernel"""
        if self.ubootPath != "none" and not os.path.exists(self.ubootPath):
            logging.info("Could Not Find uboot in:" + self.ubootPath)

        logging.info("Installing Kernel")
        kernelDom = self.boardDom.getElementsByTagName("kernel")
        for k in kernelDom:
            if k.hasAttribute("type"):
                self.kernelType = k.getAttribute("type")
                logging.info("Kernel Type: " + self.kernelType)
            else:
                logging.error("No Kernel Type Specified")
                return BoardTemplateParser.NO_KERNEL_TYPE

        if self.kernelType == "custom":
            for k in kernelDom:
                self.kernelPath = \
                    k.getElementsByTagName('image')[0].childNodes[0].data
                self.initrdPath = \
                    k.getElementsByTagName('initrd')[0].childNodes[0].data
                self.dtbDir = \
                    k.getElementsByTagName('dtbdir')[0].childNodes[0].data
                modulesPath = \
                    k.getElementsByTagName('modules')[0].childNodes[0].data
                logging.info("Using Custom Kernel: " + self.kernelPath)
                logging.info("Using Initrd: " + self.initrdPath)
                logging.info("Using Modules: " + modulesPath)
                logging.info("Using DTB: " + self.dtbDir)

                self.rbfScript.write("echo [INFO ]  $0 Copying Custom Kernel\n")
                self.rbfScript.write("cp -rv " + self.kernelPath + " " + \
                                      self.workDir + "/boot &>> rbf.log \n")
                self.rbfScript.write(self.getShellExitString(\
                                         BoardTemplateParser.COPY_KERNEL_ERROR))

                if self.initrdPath != "none":
                    self.rbfScript.write("cp -rv " + self.initrdPath + " " + \
                                          self.workDir + "/boot &>> rbf.log \n")
                    self.rbfScript.write(self.getShellExitString(\
                                         BoardTemplateParser.COPY_KERNEL_ERROR))
                if self.dtbDir != "none":
                    self.rbfScript.write("cp -rv " + self.dtbDir + " " + \
                                          self.workDir + "/boot &>> rbf.log \n")
                    self.rbfScript.write(self.getShellExitString(\
                                         BoardTemplateParser.COPY_KERNEL_ERROR))

                self.rbfScript.write("echo [INFO ]  $0 Copying Custom Kernel"\
                + " Modules\n")
                if modulesPath != "none":
                    self.rbfScript.write("mkdir -p " + self.workDir + \
                                         "/lib/modules &>> rbf.log \n")
                    self.rbfScript.write(self.getShellExitString(\
                                         BoardTemplateParser.COPY_KERNEL_ERROR))
                    self.rbfScript.write("cp -rv " + modulesPath + " " + \
                             self.workDir + "/lib/modules/" + " &>> rbf.log \n")
                    self.rbfScript.write(self.getShellExitString(\
                                         BoardTemplateParser.COPY_KERNEL_ERROR))

        elif self.kernelType == "stock":
            for k in kernelDom:
                logging.info("Using Stock Kernel")
                repoEnableString = "--disablerepo=* "
                for r in self.repoNames:
                    repoEnableString = repoEnableString + "--enablerepo=" \
                                       + r + " "
                self.rbfScript.write("echo [INFO ]  $0 Installing Kernel"\
                + " Packages. Please Wait\n")
                self.rbfScript.write("while (true)\ndo\n")
                self.rbfScript.write(self.packageInstaller + " " + \
                            repoEnableString + " --installroot=" + \
                            self.workDir +  " --releasever=" + self.releaseVer \
                            + " install -y " \
                            + "kernel dracut-config-generic 2>> rbf.log\n")
                self.rbfScript.write(self.getPackageErrorString(\
                              BoardTemplateParser.KERNEL_PACKAGE_INSTALL_ERROR))
                self.rbfScript.write("done\n\n")

        elif self.kernelType == "none":
            logging.info("Not Installing Any Kernel")

        if self.firmwareDir != "none" and not os.path.exists(self.firmwareDir):
            logging.error("Could Not Find Firmware in:" + self.firmwareDir)
            return BoardTemplateParser.NO_FIRMWARE_FOUND

        if self.firmwareDir != "none":
            self.rbfScript.write("mkdir -p " + self.workDir + \
                                 "/lib/firmware &>> rbf.log \n")
            self.rbfScript.write(self.getShellExitString(\
                                       BoardTemplateParser.COPY_FIRMWARE_ERROR))
            self.rbfScript.write("cp -rv " + self.firmwareDir + " " + \
                                 self.workDir + "/lib/firmware/ &>> rbf.log \n")
            self.rbfScript.write(self.getShellExitString(\
                                       BoardTemplateParser.COPY_FIRMWARE_ERROR))
        return 0

    def createInitramfs(self):
        """Creates Initramfs for stock kernel"""
        self.initramfsScript = open("initramfs.sh", "w")
        if self.kernelType == "stock":
            logging.info("Creating Initramfs")
            if not os.path.exists(self.workDir+"/lib/modules"):
                logging.info("No Kernels Found")
                self.stockKernels = []
                return
            self.stockKernels = os.listdir(self.workDir+"/lib/modules")
            for kernelVer in self.stockKernels:
                self.initramfsScript.write("echo [INFO ]  $0 Creating \
                Initramfs\n")
                self.initramfsScript.write("if [ -f " + self.workDir + \
                "/boot/initramfs-" + kernelVer + \
                ".img ]; then echo  [INFO ]  $0 Initramfs Exists; " + \
                "else chroot " + self.workDir + \
                " dracut /boot/initramfs-" + \
                kernelVer + ".img " + kernelVer + "; fi 2>> rbf.log\n")

    def showFiles(self, directory, depth):
        """Walks a directory tree and shows files and directories"""
        contents = os.listdir(directory)
        for c in contents:
            contentDisplayString = "         "
            i = 0
            while i < depth:
                contentDisplayString = contentDisplayString + "\t"
                i = i + 1
            contentDisplayString = contentDisplayString + "-" + c
            logging.info(contentDisplayString)
            os.chown(directory+os.sep+c, 0, 0)
            if os.path.isfile(directory+os.sep+c):
                os.chmod(directory+os.sep+c, 0644)
            if os.path.isdir(directory+os.sep+c):
                os.chmod(directory+os.sep+c, 0755)
                self.showFiles(directory+os.sep+c, depth+1)

    def generateBoardTemplate(self):
        """Generates minimal board template for new rootfs"""
        doc = Document()
        root = doc.createElement("template")
        board = doc.createElement("board")
        distro = doc.createElement("distro")

        board.appendChild(doc.createTextNode(self.boardName))
        distro.appendChild(doc.createTextNode(self.linuxDistro))

        doc.appendChild(root)
        for i in [board, distro]:
            root.appendChild(i)

        return doc.toprettyxml()

    def finalActions(self):
        """Sets Hostname, RootPass, SELinux Status"""
        hostnameConfig = open(self.etcOverlay + "/hostname", "w")
        hostnameConfig.write(self.hostName)
        hostnameConfig.close()

        #copy board details to rootfs
        rbfConfigPath = self.etcOverlay + "/rbf"
        self.makeDirTree(rbfConfigPath)
        templateFile = open(rbfConfigPath + "/board.xml", "w")
        templateFile.write(self.generateBoardTemplate())
        templateFile.close()

        #copy kernel upgrade script to /usr/sbin/
        if os.path.isfile("kernelup.d/rbf"+self.boardName+".sh") and \
           os.access("kernelup.d/rbf"+self.boardName+".sh", os.X_OK):
            self.rbfScript.write("cp kernelup.d/rbf" + self.boardName + ".sh " \
                                 + self.workDir + "/usr/sbin/\n")
            self.rbfScript.write(self.getShellErrorString(\
                                            BoardTemplateParser.KERNELUP_ERROR))

        logging.info("Copying Etc Overlay: " + self.etcOverlay)
        #show files being copied from etcOverlay. This is important because we
        #are not automatically clearing the etc overlay after each
        #RootFS Build Factory Run
        self.showFiles(self.etcOverlay, 0)
        self.rbfScript.write("cp -rpv " + self.etcOverlay + "/* " + \
                              self.workDir + "/etc/ &>> rbf.log \n")
        self.rbfScript.write(self.getShellExitString(\
                                         BoardTemplateParser.ETC_OVERLAY_ERROR))

        logging.info("Setting root password")
        self.rbfScript.write("echo \"root:" + self.rootPass + "\" | chpasswd " \
                             + "--root " + self.workDir + " &>> rbf.log\n")
        self.rbfScript.write(self.getShellErrorString(\
                                           BoardTemplateParser.ROOT_PASS_ERROR))

        if self.rootSshKey != "none":
            if os.path.exists(self.rootSshKey):
                logging.info("Setting up root ssh public key")
                self.rbfScript.write("mkdir -p " + self.workDir + \
                                     "/root/.ssh\n")
                self.rbfScript.write("cat " + self.rootSshKey + " >> " + \
                                  self.workDir + "/root/.ssh/authorized_keys\n")
                self.rbfScript.write(self.getShellErrorString(\
                                        BoardTemplateParser.ROOT_SSH_KEY_ERROR))
            else:
                logging.error("Could not find root ssh public key in: " + \
                               self.rootSshKey)
                return BoardTemplateParser.SSH_KEY_NOT_FOUND

        logging.info("Setting SELinux status to " + self.selinuxConf)
        self.rbfScript.write("sed -i 's/SELINUX=enforcing/SELINUX=" + \
                             self.selinuxConf + "/' " + self.workDir + \
                             "/etc/selinux/config  &>> rbf.log \n")
        self.rbfScript.write(self.getShellErrorString(\
                                             BoardTemplateParser.SELINUX_ERROR))

        self.rbfScript.write("exit 0\n")
        self.rbfScript.close()
        return 0

    def callBoardScripts(self):
        """Call Board Script and Finalize Script"""
        self.boardScript = open("boardscript.sh", "w")
        if os.path.isfile("boards.d/"+self.boardName+".sh") and \
           os.access("boards.d/"+self.boardName+".sh", os.X_OK):
            boardScriptCommand = "./boards.d/" + self.boardName + ".sh " + \
            self.loopDevice + " " + self.stage1Loader +" " + self.ubootPath  + \
            " " + self.workDir + " " + self.rootFiles + " " + \
            self.rootDeviceIndex + " " + self.rootDeviceUUID + "\n"
            logging.info("Board Script: " + boardScriptCommand)
            self.boardScript.write("echo [INFO ]  $0 Running Board Script: " + \
                                 boardScriptCommand)
            self.boardScript.write(boardScriptCommand)
            self.boardScript.write(self.getShellErrorString(\
                                        BoardTemplateParser.BOARD_SCRIPT_ERROR))
        else:
            logging.info("Board Script Not Found or Not Executable")

        logging.info("Finalize Script: " + self.finalizeScript)
        self.boardScript.write("echo [INFO ]  $0 Running Finalize Script: " + \
                              self.finalizeScript +"\n")
        self.boardScript.write(self.finalizeScript+"\n")
        self.boardScript.write(self.getShellErrorString(\
                                     BoardTemplateParser.FINALIZE_SCRIPT_ERROR))
        self.boardScript.write("exit 0\n")
        self.boardScript.close()

    def getPartition(self, mountpoint):
        """Gets Partition UUID/LABEL From Dict"""
        for i in range(0, len(self.imageData)):
            if self.imageData[i][BoardTemplateParser.MOUNTPOINT] == mountpoint:
                if self.imageData[i][BoardTemplateParser.FS] == "vfat":
                    return "LABEL="+self.imageData[i][BoardTemplateParser.UUID]
                else:
                    return "UUID=" + self.imageData[i][BoardTemplateParser.UUID]

    @classmethod
    def getBootPath(cls, path):
        """Returns Path for extlinux.conf"""
        if "/" not in path:
            bootPath = "/" + path
        else:
            bootPath = path[path.rfind("/"):]
        return bootPath

    def configureExtLinux(self):
        """Creating extlinux.conf"""
        if self.extlinuxConf == "false":
            self.initramfsScript.close()
            return

        self.initramfsScript.write("mkdir " + self.workDir + "/boot/extlinux\n")
        self.initramfsScript.write(self.getShellExitString(\
                                        BoardTemplateParser.EXTLINUXCONF_ERROR))

        extlinuxContents = "#Created by RootFS Build Factory\nui menu.c32\n"\
        + "menu autoboot " + self.linuxDistro + "\nmenu title "\
        + self.linuxDistro + " Options\n#menu hidden\ntimeout 60\n"\
        + "totaltimeout 600\n"
        if self.kernelType == "custom":
            logging.info("Creating extlinux.conf in " + self.workDir + \
                         "/boot/extlinux")
            bootKernelPath = self.getBootPath(self.kernelPath)
            if len(self.initrdPath) != 0:
                bootInitrdPath = self.getBootPath(self.initrdPath)
            else:
                bootInitrdPath = ""
            bootFdtdir = self.getBootPath(self.dtbDir)

            extlinuxContents = extlinuxContents + "label " + self.linuxDistro\
            + "\n\t" + "kernel " + bootKernelPath\
            + "\n\tappend enforcing=0 root=" + self.getPartition("/") +"\n\t"\
            + "fdtdir " + bootFdtdir + "\n"
            if bootInitrdPath != "none":
                extlinuxContents = extlinuxContents + "\tinitrd " + \
                                   bootInitrdPath + "\n"
            self.initramfsScript.write("cat > " + self.workDir + \
                                    "/boot/extlinux/extlinux.conf << EOF\n" + \
                                    extlinuxContents + "EOF\n")
            self.initramfsScript.write(self.getShellExitString(\
                                        BoardTemplateParser.EXTLINUXCONF_ERROR))
        elif self.kernelType == "stock":
            for kernelVer in self.stockKernels:
                extlinuxContents = extlinuxContents + "label " + \
                self.linuxDistro + "\n\t" + "kernel /vmlinuz-" + kernelVer + \
                "\n\tappend enforcing=0 root=" + self.getPartition("/") + \
                "\n\tfdtdir /dtb-" + kernelVer + "\n\tinitrd /initramfs-" + \
                kernelVer + ".img\n\n"
            self.initramfsScript.write("cat > " + self.workDir + \
                                       "/boot/extlinux/extlinux.conf << EOF\n" \
                                       + extlinuxContents + "EOF\n")
            self.initramfsScript.write(self.getShellExitString(\
                                        BoardTemplateParser.EXTLINUXCONF_ERROR))

        self.initramfsScript.close()

    def makeBootable(self):
        """Creates /etc/fstab"""
        if not os.path.exists(self.etcOverlay):
            logging.error("Need Etc Overlay To Continue")
            return BoardTemplateParser.NO_ETC_OVERLAY

        fstab = open(self.etcOverlay+"/fstab", "w")
        fstab.write("#Generated by RootFS Build Factory\n")
        for i in range(0, len(self.imageData)):
            if self.imageData[i][BoardTemplateParser.PTYPE] == "extended":
                continue
            mountpoint = self.imageData[i][BoardTemplateParser.MOUNTPOINT]
            partitionPath = self.getPartition(mountpoint)
            fs = self.imageData[i][BoardTemplateParser.FS]
            fstab.write(partitionPath + " " + mountpoint + " " + fs + \
                        " noatime 0 0\n")
        fstab.close()
        return 0

    @classmethod
    def makeDirTree(cls, path):
        """Makes Dir Tree"""
        subprocess.call(['mkdir', '-p', path])

    def configureNetwork(self):
        """Configure Network"""
        logging.info("Reading Network Config")
        totalNetworkInterfaces = 0
        networkDom = self.boardDom.getElementsByTagName("network")
        if networkDom == []:
            logging.error("No Network Config Found")
            return BoardTemplateParser.NO_NETWORK

        networkConfigPath = self.etcOverlay+"/sysconfig/network-scripts"

        for n in networkDom:
            interface = n.getElementsByTagName("interface")
            for i in interface:
                name = i.getAttribute("name")
                config = i.getAttribute("config")
                logging.info("Found Network Interface: " + name + " " + config)
                if config == "static":
                    try:
                        el = i.getElementsByTagName("ipaddress")[0]
                        ipaddress = el.childNodes[0].data
                        el = i.getElementsByTagName("subnetmask")[0]
                        subnetmask = el.childNodes[0].data
                        el = i.getElementsByTagName("gateway")[0]
                        gateway = el.childNodes[0].data
                        el = i.getElementsByTagName("dns1")[0]
                        dns1 = el.childNodes[0].data
                        try:
                            el = i.getElementsByTagName("dns2")[0]
                            dns2 = el.childNodes[0].data
                        except IndexError:
                            dns2 = ""
                    except IndexError:
                        logging.error("Error reading static interface info. " +\
                        "Ignoring " + name)
                        continue

                    logging.info("IP Addres: " + name + " " + ipaddress)

                    self.makeDirTree(networkConfigPath)
                    ifcfg = open(networkConfigPath+"/ifcfg-"+name, "w")
                    ifcfg.write("TYPE=\"Ethernet\"\n")
                    ifcfg.write("BOOTPROTO=\"none\"\n")
                    ifcfg.write("NM_CONTROLLED=\"yes\"\n")
                    ifcfg.write("DEFROUTE=\"yes\"\n")
                    ifcfg.write("NAME=\""+name+"\"\n")
                    ifcfg.write("UUID=\""+str(uuid.uuid4())+"\"\n")
                    ifcfg.write("ONBOOT=\"yes\"\n")
                    ifcfg.write("IPADDR0=\""+ipaddress+"\"\n")
                    ifcfg.write("NETMASK0=\""+subnetmask+"\"\n")
                    ifcfg.write("GATEWAY0=\""+gateway+"\"\n")
                    ifcfg.write("DNS1=\""+dns1+"\"\n")
                    if dns2 != "":
                        ifcfg.write("DNS2=\""+dns2+"\"\n")
                    ifcfg.close()
                    totalNetworkInterfaces = totalNetworkInterfaces + 1
                elif config == "dhcp":
                    self.makeDirTree(networkConfigPath)
                    ifcfg = open(networkConfigPath+"/ifcfg-"+name, "w")
                    ifcfg.write("TYPE=\"Ethernet\"\n")
                    ifcfg.write("BOOTPROTO=\"dhcp\"\n")
                    ifcfg.write("NM_CONTROLLED=\"yes\"\n")
                    ifcfg.write("DEFROUTE=\"yes\"\n")
                    ifcfg.write("NAME=\""+name+"\"\n")
                    ifcfg.write("UUID=\""+str(uuid.uuid4())+"\"\n")
                    ifcfg.write("ONBOOT=\"yes\"\n")
                    ifcfg.close()
                    totalNetworkInterfaces = totalNetworkInterfaces + 1

        return totalNetworkInterfaces

    def cleanUp(self):
        """CleanUp Steps"""
        logging.info("Clean Up")
        self.cleanupScript = open("cleanup.sh", "w")
        for i in range(0, len(self.imageData)):
            if self.imageData[i][BoardTemplateParser.PTYPE] == "extended":
                continue
            if self.imageData[i][BoardTemplateParser.MOUNTPOINT] != "/" \
            and self.imageData[i][BoardTemplateParser.MOUNTPOINT] != "swap":
                self.cleanupScript.write("umount " + self.workDir + \
                self.imageData[i][BoardTemplateParser.MOUNTPOINT]+"\n")

        self.cleanupScript.write("umount " + self.workDir + "/proc\n")
        self.cleanupScript.write("umount -l " + self.workDir + "/dev/\n")
        self.cleanupScript.write("sleep 2\n")
        self.cleanupScript.write("umount " + self.workDir + "\n")
        self.cleanupScript.write(self.delDeviceIfExists(self.loopDevice))
        self.cleanupScript.write("exit 0\n")
        self.cleanupScript.close()
        if self.action == "build":
            cleanupRet = subprocess.call(["bash", "cleanup.sh"])
            if cleanupRet != 0:
                logging.error("Did Not Execute Clean Up Cleanly")
        logging.info("If you need any help, please provide rbf.log rbf.sh "\
                     + "initramfs.sh cleanup.sh boardscript.sh " + \
                     self.xmlTemplate + " and the above output.")


if __name__ == "__main__":
    initLogging()
    if os.getuid() != 0:
        logging.error("You need to be root to use RootFS Build Factory")
        sys.exit(BoardTemplateParser.NOT_ROOT)

    if len(sys.argv) != 3:
        printUsage()
        sys.exit(BoardTemplateParser.INCORRECT_ARGUMENTS)

    action = sys.argv[1]
    xmlTemplate = sys.argv[2]

    if not os.path.exists(xmlTemplate):
        logging.error("XML Template Not Found: " + xmlTemplate)
        sys.exit(BoardTemplateParser.TEMPLATE_NOT_FOUND)

    if action == "build" and not platform.uname()[5].startswith("arm"):
        logging.error("This script is not meant to be run on " + \
                      platform.uname()[5])

    if checkCommandExistsAccess(['echo', 'dd', 'parted', 'read', 'losetup', \
    'mount', 'mkdir', 'rm', 'cat', 'cp', 'rpm', 'sed', 'chroot', \
    'partprobe', 'chpasswd']):
        logging.info("All Commands Found. Continuing")
    else:
        logging.error("Cannot Continue")
        sys.exit(BoardTemplateParser.COMMANDS_NOT_FOUND)

    if sys.argv[1] == "parse" or sys.argv[1] == "build":
        logging.info("Arguments Correct. Continuing")
    else:
        printUsage()
        sys.exit(BoardTemplateParser.INCORRECT_ARGUMENTS)

    boardParser = BoardTemplateParser(action, xmlTemplate)
    ret = boardParser.parseTemplate()
    if ret != 0:
        sys.exit(ret)
    ret = boardParser.createImage()
    if ret != 0:
        sys.exit(ret)
    ret = boardParser.createPartitions()
    if ret != 0:
        sys.exit(ret)
    ret = boardParser.createFilesystems()
    if ret != 0:
        sys.exit(ret)
    boardParser.mountPartitions()
    ret = boardParser.writeRepos()
    if ret != 0:
        sys.exit(ret)
    ret = boardParser.installPackages()
    if ret != 0:
        sys.exit(ret)
    ret = boardParser.makeBootable()
    if ret != 0:
        sys.exit(ret)
    boardParser.configureNetwork()
    ret = boardParser.installKernel()
    if ret != 0:
        sys.exit(ret)
    ret = boardParser.finalActions()
    if ret != 0:
        sys.exit(ret)

    if action == "build":
        logging.info("Running RootFS Build Factory script")
        rbfRet = subprocess.call(["bash", "rbf.sh"])
        if rbfRet == 0:
            logging.info("Successfully Executed rbf.sh")
        else:
            logging.error(boardParser.RbfScriptErrors[rbfRet])
            boardParser.cleanUp()
            sys.exit(rbfRet)

        boardParser.createInitramfs()
        boardParser.configureExtLinux()
        initramfsRet = subprocess.call(["bash", "initramfs.sh"])
        if initramfsRet != 0:
            logging.error(boardParser.RbfScriptErrors[initramfsRet])
            boardParser.cleanUp()
            sys.exit(initramfsRet)

        boardParser.callBoardScripts()
        boardScriptRet = subprocess.call(["bash", "boardscript.sh"])
        if boardScriptRet != 0:
            logging.error(boardParser.RbfScriptErrors[boardScriptRet])
            boardParser.cleanUp()
            sys.exit(boardScriptRet)

    boardParser.cleanUp()
    sys.exit(0)

