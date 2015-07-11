#!/usr/bin/python
# pylint: disable=
"""@package TemplateCreator
Cretor for Board XML Template

Creates XML Template
"""

import os
import sys
from dialog import Dialog
from rbfutils import RbfUtils
from xml.dom.minidom import parse, Document
from xml.parsers.expat import ExpatError

class BoardTemplateCreator(object):
    """Board Template Creator"""
    SIZE, PTYPE, FS, MOUNTPOINT = range(0, 4)
    REPO_NAME, REPO_URL = range(0, 2)
    IF_NAME, IF_CONFIG, IF_IP, IF_NETMASK, IF_GATEWAY, IF_DNS1, IF_DNS2 \
                                                                   = range(0, 7)
    BOARDS_DIR = "boards.d"
    NO_FILE, ERROR_PARSING_XML, ERROR_PARSING_XML_TAGS, INVALID_IMAGE_SIZE, \
    ERROR_CUSTOM_KERNEL_INFO, ERROR_READING_PARTITIONS, NO_IMAGE, \
    INVALID_PARTITION_SIZE, EXTENDED_PARTITION_ERROR, TOTAL_PARTITIONS_ERROR, \
    PRIMARY_PARTITION_EXCEEDS, LOGICAL_BEFORE_EXTENDED, \
    LOGICAL_PARTITION_EXCEEDS, NO_PARTITIONS, INCORRECT_REPOSITORY, \
    NO_PACKAGES, BAD_NETWORK_DATA, NO_NETWORK, NO_KERNEL, NO_KERNEL_TYPE \
                                                               = range(100, 120)
    RbfDialogErrors = {
        NO_FILE: "NO_FILE: Could not find XML File",
        ERROR_PARSING_XML: "ERROR_PARSING_XML: Error Parsing XML File",
        ERROR_PARSING_XML_TAGS: "ERROR_PARSING_XML_TAGS: Could not read all "\
        + "XML Elements",
        INVALID_IMAGE_SIZE: "INVALID_IMAGE_SIZE: Should be integer with suffer"\
        + " M for MB and G for GB",
        ERROR_CUSTOM_KERNEL_INFO: "ERROR_CUSTOM_KERNEL_INFO: Error Reading"\
        + " custom Kernel Info",
        ERROR_READING_PARTITIONS: "ERROR_READING_PARTITIONS: You will have to"\
        + " create partitions manually",
        NO_IMAGE: "Please create an Image First",
        INVALID_PARTITION_SIZE: "Invalid Size. Has to be an Integer with"\
        + " suffix M for MB and G for GB",
        EXTENDED_PARTITION_ERROR: "Only 1 Extended Partition Allowed",
        TOTAL_PARTITIONS_ERROR: "Cannot create more than 4 primary partitions",
        PRIMARY_PARTITION_EXCEEDS: "Primary Partition Sizes exceed Image Size",
        LOGICAL_BEFORE_EXTENDED: "Cannot Create Logical Before Extended",
        LOGICAL_PARTITION_EXCEEDS: "Logical Partition Sizes Exceed Extended"\
        + " Partition Size",
        NO_PARTITIONS: "No Partitions Found",
        INCORRECT_REPOSITORY: "Incorrect Repo Info",
        NO_PACKAGES: "No Packages Defined",
        BAD_NETWORK_DATA: "Bad Network Data: Not all interfaces were added to"\
        + " config",
        NO_NETWORK: "No Network Data Found",
        NO_KERNEL: "No Kernel Info Found",
        NO_KERNEL_TYPE: "No Kernel Type Specified"
        }

    def __init__(self):
        """Constructor"""
        self.dialogInstance = Dialog(dialog="dialog")
        self.rbfUtils = RbfUtils()
        self.dialogInstance.add_persistent_args(["--backtitle",
                                                 "RootFS Build Factory"])
        self.xmlTemplate = "none"
        self.imageSize = ""
        self.imagePath = ""
        self.imageData = []
        self.boardName = ""
        self.partitionInfo = ""
        self.totalPartitionCount = 0
        self.primaryCount = 0
        self.extendedStart = False
        self.stage1Loader = "none"
        self.ubootPath = "none"
        self.rootFiles = "none"
        self.rootPass = ""
        self.rootSshKey = "none"
        self.firmwarePath = "none"
        self.extlinuxConf = "false"
        self.kernelType = "stock"
        self.kernelPath = "none"
        self.initrdPath = "none"
        self.modulesPath = "none"
        self.dtbPath = "none"
        self.repoData = []
        self.totalRepos = 0
        self.groupPackageString = "core"
        self.packageString = ""
        self.packageInstaller = "yum"
        self.releaseVer = "7"
        self.etcOverlay = "./etc"
        self.finalizeScript = "boards.d/finalize.sh"
        self.linuxDistro = "CentOS"
        self.workDir = "/tmp/temp"
        self.hostName = "localhost"
        self.selinuxConf = "disabled"
        self.networkData = []
        self.totalNetworkInterfaces = 0
        self.networkConf = []
        self.homePath = os.environ['HOME']
        self.lastKnownPath = os.getcwd()
        self.generatedXmlPath = ""
        self.firmwareDir = "none"
        self.boardDom = []

    def showBoards(self):
        """Shows a radiolist of supported boards"""
        knownBoards = sorted(os.listdir(BoardTemplateCreator.BOARDS_DIR))
        boardChoices = []
        for board in knownBoards:
            if board == "finalize.sh":
                continue
            if board[0:-3] == self.boardName:
                b = (board[0:-3].title(), "Run boards.d/"+board+" Script", 1)
            else:
                b = (board[0:-3].title(), "Run boards.d/"+board+" Script", 0)
            boardChoices.append(b)
        boardChoices.append(("Custom", "Customize Image yourself", 0))
        (code, tag) = self.dialogInstance.radiolist("Supported Boards",\
                      width=65, choices=boardChoices)
        if code == Dialog.OK:
            self.boardName = tag.lower()

    def showImageInfo(self):
        """Allows you to select directory and filename of image"""

        while True:
            if self.imagePath != "" and self.imagePath.rfind("/") != -1:
                imageName = self.imagePath[self.imagePath.rfind("/")+1:]
            else:
                imageName = "rootfs-image.img"

            (code, path) = self.dialogInstance.dselect(self.lastKnownPath, 10,\
                           50, title="Select Directory")
            if code in (Dialog.CANCEL, Dialog.ESC):
                break
            (code, filename) = self.dialogInstance.inputbox("Enter filename",\
                               init=imageName)
            self.imagePath = os.path.join(path, filename)
            self.lastKnownPath = path

            if code in (Dialog.CANCEL, Dialog.ESC):
                break
            while True:
                (code, filesize) = self.dialogInstance.inputbox("Please enter"\
                + " a size with suffix M for Megabytes and G for Gigabytes",\
                init="4G")
                if code in (Dialog.CANCEL, Dialog.ESC):
                    break
                if not (filesize[0:-1] == "M" or filesize[0:-1] == "G"):
                    if not self.rbfUtils.isSizeInt(filesize[0:-1]):
                        self.dialogInstance.msgbox("Incorrect Size Specified")
                    else:
                        self.imageSize = filesize
                        break
            break

    def getPartitionDisplayString(self):
        """Generates Paritition Information String"""
        partitionDisplayString = ""
        if len(self.imageData) == 0:
            partitionDisplayString = "No Partitions Defined"
        else:
            partitionDisplayString = ""
            partitionDisplayString = "%-6s%-8s%-10s%-5s%-10s\n\n" % ("Index",\
             "Size", "Type", "FS", "MountPoint")
            for i in range(0, len(self.imageData)):
                partitionDisplayString = partitionDisplayString + \
                ("%-6s%-8s%-10s%-5s%-10s\n") % (str(i+1), \
                self.imageData[i][BoardTemplateCreator.SIZE], \
                self.imageData[i][BoardTemplateCreator.PTYPE], \
                self.imageData[i][BoardTemplateCreator.FS], \
                self.imageData[i][BoardTemplateCreator.MOUNTPOINT])
        return partitionDisplayString

    def validatePartitionData(self, fields):
        """Validates Partition Data"""
        if self.imageSize == "":
            return BoardTemplateCreator.NO_IMAGE
        sizeNumber = fields[BoardTemplateCreator.SIZE][0:-1]
        if not self.rbfUtils.isSizeInt(sizeNumber):
            return BoardTemplateCreator.INVALID_PARTITION_SIZE

        if fields[BoardTemplateCreator.SIZE][-1:] not in ("M", "G"):
            return BoardTemplateCreator.INVALID_PARTITION_SIZE

        if self.extendedStart is True and\
           fields[BoardTemplateCreator.PTYPE].lower() == "extended":
            return BoardTemplateCreator.EXTENDED_PARTITION_ERROR

        # only 4 primary partitions supported
        if self.primaryCount >= 4 and\
           fields[BoardTemplateCreator.PTYPE].lower()\
           in ("primary", "extended"):
            return BoardTemplateCreator.TOTAL_PARTITIONS_ERROR

        # check if total size of primary partitions exceed image size
        if fields[BoardTemplateCreator.PTYPE].lower()\
           in ("primary", "extended"):
            # check if imagesize is a valid one
            if not self.rbfUtils.isSizeInt(self.imageSize[0:-1]):
                self.imagePath = ""
                self.imageSize = ""
                return BoardTemplateCreator.INVALID_IMAGE_SIZE

            imageSizeInM = \
                int(self.rbfUtils.getImageSizeInM(self.imageSize)[0:-1])
            primaryPartSize = 0
            for i in range(0, len(self.imageData)):
                if self.imageData[i][BoardTemplateCreator.PTYPE].lower()\
                   in ("primary", "extended"):
                    primaryPartSize = primaryPartSize +\
                            int(self.rbfUtils.getImageSizeInM(\
                            self.imageData[i][BoardTemplateCreator.SIZE])[0:-1])

            primaryPartSize = primaryPartSize + \
                int(self.rbfUtils.getImageSizeInM(\
                    fields[BoardTemplateCreator.SIZE])[0:-1])
            if primaryPartSize > imageSizeInM:
                return BoardTemplateCreator.PRIMARY_PARTITION_EXCEEDS

        # check if user is creating a logical part before an extended one
        if self.extendedStart is False and\
           fields[BoardTemplateCreator.PTYPE].lower() == "logical":
            return BoardTemplateCreator.LOGICAL_BEFORE_EXTENDED

        # check if logical partition sizes exceed extended partition size
        if fields[BoardTemplateCreator.PTYPE].lower() == "logical":
            logicalPartitionSizes = 0
            for i in range(0, len(self.imageData)):
                size = self.rbfUtils.getImageSizeInM(\
                                   self.imageData[i][BoardTemplateCreator.SIZE])
                if self.imageData[i][BoardTemplateCreator.PTYPE].lower()\
                     == "extended":
                    extendedPartitionSize = int(size[0:-1])
                if self.imageData[i][BoardTemplateCreator.PTYPE].lower()\
                     == "logical":
                    logicalPartitionSizes = logicalPartitionSizes\
                                            + int(size[0:-1])

            logicalPartitionSizes = logicalPartitionSizes\
                 + int(self.rbfUtils.getImageSizeInM(\
                    fields[BoardTemplateCreator.SIZE])[0:-1])
            if logicalPartitionSizes > extendedPartitionSize:
                return BoardTemplateCreator.LOGICAL_PARTITION_EXCEEDS

        return 0

    def addPartition(self):
        """Adds Partition"""
        while True:
            code = self.dialogInstance.scrollbox(\
                   self.getPartitionDisplayString(), width=50,\
                   extra_button=True, extra_label="Add",\
                   title="Partition Details")
            if code == Dialog.EXTRA:
                elements = [("Size (M/G)", 1, 1, "1G", 1, 20, 8, 8),
                            ("Partition Type", 2, 1, "Primary", 2, 20, 8, 8),
                            ("Filesystem", 3, 1, "ext3", 3, 20, 8, 8),
                            ("Mount Point", 4, 1, "/", 4, 20, 8, 20)]

                (code, fields) = self.dialogInstance.form("Partition Info",\
                                 elements, width=50)

                if code == Dialog.OK:
                    ret = self.validatePartitionData(fields)
                    if ret == 0:
                        if fields[BoardTemplateCreator.PTYPE].lower()\
                           in ("primary", "extended"):
                            self.primaryCount = self.primaryCount + 1

                        # ignore FS and MOUNTPOINT for Extended Partition
                        if fields[BoardTemplateCreator.PTYPE].lower()\
                           == "extended":
                            self.extendedStart = True
                            fields[BoardTemplateCreator.FS] = ""
                            fields[BoardTemplateCreator.MOUNTPOINT] = ""
                        # ignore MOUNTPOINT for swap
                        elif fields[BoardTemplateCreator.PTYPE].lower()\
                             == "swap":
                            fields[BoardTemplateCreator.MOUNTPOINT] = ""

                        p = [fields[BoardTemplateCreator.SIZE],\
                             fields[BoardTemplateCreator.PTYPE],\
                             fields[BoardTemplateCreator.FS],\
                             fields[BoardTemplateCreator.MOUNTPOINT]]
                        self.imageData.append(p)
                        self.totalPartitionCount = self.totalPartitionCount + 1
                    else:
                        self.showErrorMessage(ret)
            else:
                break

    def performDelteOperation(self, n):
        """Peforms Actual Partition Delete Operation"""
        self.totalPartitionCount = self.totalPartitionCount - 1
        if self.imageData[n-1][BoardTemplateCreator.PTYPE].lower()\
           in ("primary", "extended"):
            self.primaryCount = self.primaryCount - 1
        if self.imageData[n-1][BoardTemplateCreator.PTYPE].lower()\
           == "extended":
            self.extendedStart = False
            for i in list(reversed(range(0, len(self.imageData)))):
                if self.imageData[i][BoardTemplateCreator.PTYPE].lower()\
                   == "logical":
                    del self.imageData[i]
        del self.imageData[n-1]


    def deletePartition(self):
        """Deletes Partition"""
        while True:
            code = self.dialogInstance.scrollbox(\
                   self.getPartitionDisplayString(), width=50,\
                   extra_button=True, extra_label="Delete",\
                   title="Partition Details")
            if code == Dialog.EXTRA:
                (code, number) = self.dialogInstance.inputbox(\
                                 "Partition Number to Delete", init="",\
                                 title="Delete")
                if self.rbfUtils.isSizeInt(number):
                    n = int(number)
                    if n <= self.totalPartitionCount:
                        self.performDelteOperation(n)
                    else:
                        self.dialogInstance.msgbox("Enter a valid integer\n" +\
                        "You have defined " + str(self.totalPartitionCount) +\
                        " Partition(s)", title="Error")
            else:
                break



    def showPartition(self):
        """Shows Partition Information"""
        self.dialogInstance.scrollbox(self.getPartitionDisplayString(),\
                                            title="Partition Details", width=50)

    def showPartitionInfo(self):
        """Create Partition Layout"""
        while True:
            (code, tag) = self.dialogInstance.menu("Partition Menu", width=60,\
                          choices=[("Add", "Add a Partition"),
                                   ("Delete", "Delete a Partition"),
                                   ("Show", "Show Partition Layout"),
                                   ("Done", "Done configuring")])
            if code in (Dialog.CANCEL, Dialog.ESC):
                break
            if tag == "Add":
                self.addPartition()
            elif tag == "Delete":
                self.deletePartition()
            elif tag == "Show":
                self.showPartition()
            elif tag == "Done":
                break

    def getPath(self, var, message):
        """Get Path to File or Directory"""
        (ret, filepath) = self.dialogInstance.fselect(self.lastKnownPath, 10,\
                          50, title=message, extra_button=True,\
                          extra_label="None")
        if ret == Dialog.OK:
            self.lastKnownPath = filepath[0:filepath.rfind("/")+1]
            return filepath
        elif ret == Dialog.EXTRA:
            return "none"
        else:
            return var

    def getFilePath(self, var, message):
        """Shows File Select Dialog"""
        (ret, filepath) = self.dialogInstance.fselect(self.lastKnownPath, 10,\
                          50, title=message, extra_button=True,\
                          extra_label="None")
        if ret == Dialog.OK:
            if os.path.isfile(filepath):
                self.lastKnownPath = filepath[0:filepath.rfind("/")+1]
                return filepath
            else:
                self.dialogInstance.msgbox("That's not a file")
                return var
        elif ret == Dialog.EXTRA:
            return "none"
        else:
            return var

    def getDirPath(self, var, message):
        """Shows Directory Select Dialog"""
        (ret, dirpath) = self.dialogInstance.dselect(self.lastKnownPath, 10,\
                         50, title=message, extra_button=True,\
                         extra_label="None")
        if ret == Dialog.OK:
            if os.path.isdir(dirpath):
                self.lastKnownPath = dirpath
                return dirpath
            else:
                self.dialogInstance.msgbox("That's not a directory")
                return var
        elif ret == Dialog.EXTRA:
            return "none"
        else:
            return var


    def showBootInfo(self):
        """Bootloader Info"""
        while True:
            (code, tag) = self.dialogInstance.menu("Bootloader Menu", width=60,\
                            choices=[("Stage1 Loader", self.stage1Loader),
                                     ("U-Boot", self.ubootPath),
                                     ("Root Files", self.rootFiles),
                                     ("Firmware Dir", self.firmwarePath),
                                     ("Extlinux Conf", self.extlinuxConf),
                                     ("Done", "Exit Bootloader Config")])

            if code in (Dialog.CANCEL, Dialog.ESC):
                break
            if tag == "Stage1 Loader":
                self.stage1Loader = self.getFilePath(self.stage1Loader,\
                                    "Select Stage1 Loader")
            elif tag == "U-Boot":
                self.ubootPath = self.getFilePath(self.ubootPath,\
                                 "Select U-Boot")
            elif tag == "Root Files":
                self.rootFiles = self.getFilePath(self.rootFiles,\
                                 "Select Root Files")
            elif tag == "Firmware Dir":
                self.firmwarePath = self.getDirPath(self.firmwarePath,\
                                    "Select Firmware Dir")
            elif tag == "Extlinux Conf":
                if self.extlinuxConf == "false":
                    extlinuxChoices = \
                        (["Yes", "Configure /boot/extlinux/extlinux.conf", 0],
                         ["No", "Do not configure extlinux", 1])
                else:
                    extlinuxChoices = \
                        (["Yes", "Configure /boot/extlinux/extlinux.conf", 1],
                         ["No", "Do not configure extlinux", 0])
                (code, tag) = self.dialogInstance.radiolist("Supported Boards",\
                              width=65, choices=extlinuxChoices)
                if code == Dialog.OK:
                    if tag == "Yes":
                        self.extlinuxConf = "true"
                    else:
                        self.extlinuxConf = "false"
            else:
                break

    def showKernelInfo(self):
        """Show Kernel Information"""
        while True:
            kernelChoices = []
            kernelChoices.append(["Kernel Type", self.kernelType])
            if self.kernelType.lower() == "custom":
                kernelChoices.append(["Image", self.kernelPath])
                kernelChoices.append(["Initrd", self.initrdPath])
                kernelChoices.append(["Modules", self.modulesPath])
                kernelChoices.append(["DTB", self.dtbPath])
            kernelChoices.append(["Done", "Exit Kernel Config"])
            (code, tag) = self.dialogInstance.menu("Kernel Menu", width=0,\
                          height=0, menu_height=0, choices=kernelChoices)
            if code in (Dialog.CANCEL, Dialog.ESC):
                break
            if tag == "Kernel Type":
                ktypeChoices = {'Stock': 'Use Distribution Kernel',\
                                'Custom': 'Specify Kernel',\
                                'None': 'No Kernel'}
                typeChoices = []

                for ktype in ktypeChoices.keys():
                    if self.kernelType == ktype.lower():
                        k = (ktype, ktypeChoices[ktype], 1)
                    else:
                        k = (ktype, ktypeChoices[ktype], 0)
                    typeChoices.append(k)

                (code, tag) = self.dialogInstance.radiolist(\
                    "Choose Kernel Type", width=65, choices=typeChoices)
                if code == Dialog.OK:
                    self.kernelType = tag.lower()
            if tag == "Image":
                self.kernelPath = self.getFilePath(self.kernelPath,\
                                  "Kernel Image")
            elif tag == "Initrd":
                self.initrdPath = self.getFilePath(self.initrdPath,\
                                  "Initrd Image")
            elif tag == "Modules":
                self.modulesPath = self.getDirPath(self.modulesPath,\
                                  "Modules Dir")
            elif tag == "DTB":
                self.dtbPath = self.getPath(self.dtbPath,\
                               "DTB Path")
            elif tag == "Done":
                break

    def showMiscInfo(self):
        """Misc Settings"""
        while True:
            (code, tag) = self.dialogInstance.menu("Misc Settings", width=60,\
                            choices=[("Etc Overlay", self.etcOverlay),
                                     ("Finalize Script", self.finalizeScript),
                                     ("Distro Name", self.linuxDistro),
                                     ("Work Dir", self.workDir),
                                     ("Done", "Exit Misc Settings")])
            if code in (Dialog.CANCEL, Dialog.ESC):
                break
            if tag == "Etc Overlay":
                self.etcOverlay = self.getDirPath(self.etcOverlay,\
                                  "Select etc Overlay Dir")
            elif tag == "Finalize Script":
                self.finalizeScript = self.getFilePath(self.finalizeScript,\
                                      "Select Finalize Script")
            elif tag == "Distro Name":
                (code, distroname) = self.dialogInstance.inputbox(\
                                     "Enter Distro Name", init="CentOS",\
                                      title="Distro Name")
                if code == Dialog.OK:
                    self.linuxDistro = distroname
            elif tag == "Work Dir":
                self.workDir = self.getDirPath(self.workDir, "Select Work Dir")
            elif tag == "Done":
                break

    def addRepo(self):
        """Add a repository"""
        while True:
            code = self.dialogInstance.scrollbox(self.getRepoDisplayString(),\
                   width=100, extra_button=True, extra_label="Add Repo",\
                   title="Repo Details")
            if code == Dialog.EXTRA:
                elements = [("Name", 1, 1, "", 1, 20, 20, 20),
                            ("BaseURL", 2, 1, "", 2, 20, 20, 512)]

                (code, fields) = self.dialogInstance.form("Repo Info",\
                                 elements, width=50)
                if code == Dialog.OK:
                    r = [fields[BoardTemplateCreator.REPO_NAME],\
                         fields[BoardTemplateCreator.REPO_URL]]
                    self.repoData.append(r)
                    self.totalRepos = self.totalRepos + 1
            else:
                break

    def deleteRepo(self):
        """Delete a repository"""
        while True:
            code = self.dialogInstance.scrollbox(self.getRepoDisplayString(),\
                   width=100, extra_button=True, extra_label="Del Repo",\
                   title="Repo Details")
            if code == Dialog.EXTRA:
                (code, number) = self.dialogInstance.inputbox(\
                                 "Repo Number to Delete", init="",\
                                 title="Delete")
                if self.rbfUtils.isSizeInt(number):
                    n = int(number)
                    if n <= self.totalRepos:
                        self.totalRepos = self.totalRepos - 1
                        del self.repoData[n-1]
                    else:
                        self.dialogInstance.msgbox("Enter a valid integer\n"\
                        + "You have defined " + str(self.totalRepos)\
                        + " repo(s)", title="Error")
            else:
                break

    def showRepo(self):
        """Show Repository Information"""
        self.dialogInstance.scrollbox(self.getRepoDisplayString(),\
        title="Repo Details", width=100)

    def getRepoDisplayString(self):
        """Generate Repository Display String"""
        repoDisplayString = "%-6s%-20s%-50s\n\n" % ("Index", "Name", "BaseURL")
        for i in range(0, len(self.repoData)):
            repoDisplayString = repoDisplayString + ("%-6s%-20s%-50s\n") %\
            (str(i+1), self.repoData[i][BoardTemplateCreator.REPO_NAME],\
            self.repoData[i][BoardTemplateCreator.REPO_URL])
        return repoDisplayString

    def showEditRepoForm(self, n):
        """Show Repository Edit Form"""
        elements = [("Name", 1, 1,\
                     self.repoData[n-1][BoardTemplateCreator.REPO_NAME], 1, 20,\
                     20, 20),
                    ("Base URL", 2, 1,\
                     self.repoData[n-1][BoardTemplateCreator.REPO_URL], 2, 20,\
                     20, 512)]

        code, fields = self.dialogInstance.form("Edit Repo", elements,\
                       width=50, extra_button=True, extra_label="Delete")
        if code == Dialog.OK:
            self.repoData[n-1][BoardTemplateCreator.REPO_NAME] = \
                                          fields[BoardTemplateCreator.REPO_NAME]
            self.repoData[n-1][BoardTemplateCreator.REPO_URL] = \
                                           fields[BoardTemplateCreator.REPO_URL]
        elif code == Dialog.EXTRA:
            self.totalRepos = self.totalRepos - 1
            del self.repoData[n-1]

    def editRepo(self):
        """Show Edit Repo Dialog"""
        while True:
            code = self.dialogInstance.scrollbox(self.getRepoDisplayString(),\
                   width=100, extra_button=True, extra_label="Edit Repo",\
                   title="Repo Details")
            if code == Dialog.EXTRA:
                (code, number) = self.dialogInstance.inputbox(\
                                 "Repo Number to Edit", init="", title="Edit")
                if self.rbfUtils.isSizeInt(number):
                    n = int(number)
                    if n <= self.totalRepos:
                        self.showEditRepoForm(n)
                    else:
                        self.dialogInstance.msgbox("Enter a valid integer\n"\
                        + "You have defined " + str(self.totalRepos)\
                        + " repo(s)", title="Error")
            else:
                break

    def showRepoConf(self):
        """Repo Conf"""
        while True:
            (code, tag) = self.dialogInstance.menu("Repository Menu", width=60,\
                            choices=[("Add", "Add a Repo"),
                                     ("Edit", "Edit a Repo"),
                                     ("Delete", "Delete a Repo"),
                                     ("Show", "Show Repos"),
                                     ("Done", "Done configuring")])
            if code in (Dialog.CANCEL, Dialog.ESC) or tag == "Done":
                break
            elif tag == "Add":
                self.addRepo()
            elif tag == "Edit":
                self.editRepo()
            elif tag == "Delete":
                self.deleteRepo()
            elif tag == "Show":
                self.showRepo()

    @classmethod
    def getTagValue(cls, dom, domTag):
        """Extracts Tag Value from DOMTree"""
        xmlTag = dom.getElementsByTagName(domTag)[0]
        return xmlTag.firstChild.data

    def setTemplate(self, filename):
        """Sets XML Template File"""
        self.xmlTemplate = filename

    def showErrorMessage(self, ret):
        """Shows Error Message corresponding to ret"""
        self.dialogInstance.msgbox(BoardTemplateCreator.RbfDialogErrors[ret],\
                                   title="Error")

    def readXml(self):
        """Reads XML Template using xml.dom.minidom"""
        try:
            self.boardDom = parse(self.xmlTemplate)
        except ExpatError:
            self.xmlTemplate = "none"
            return BoardTemplateCreator.ERROR_PARSING_XML
        return 0

    def readTags(self):
        """Reads XML Tags"""
        try:
            self.boardName = self.getTagValue(self.boardDom, "board")
            self.workDir = self.getTagValue(self.boardDom, "workdir")
            self.finalizeScript = self.getTagValue(self.boardDom,\
                                                   "finalizescript")
            self.selinuxConf = self.getTagValue(self.boardDom, "selinux")
            self.etcOverlay = self.getTagValue(self.boardDom, "etcoverlay")
            self.linuxDistro = self.getTagValue(self.boardDom, "distro")
            self.extlinuxConf = self.getTagValue(self.boardDom, "extlinuxconf")
            self.hostName = self.getTagValue(self.boardDom, "hostname")

            self.rootPass = self.getTagValue(self.boardDom, "rootpass")
            self.rootSshKey = self.getTagValue(self.boardDom, "rootsshkey")

            self.rootFiles = self.getTagValue(self.boardDom, "rootfiles")
            self.stage1Loader = self.getTagValue(self.boardDom, "stage1loader")
            self.ubootPath = self.getTagValue(self.boardDom, "uboot")
            self.firmwareDir = self.getTagValue(self.boardDom, "firmware")
            self.packageInstaller = self.getTagValue(self.boardDom, "installer")
            self.releaseVer = self.getTagValue(self.boardDom, "releasever")
        except IndexError:
            return BoardTemplateCreator.ERROR_PARSING_XML_TAGS
        return 0

    def readImageData(self):
        """Reads Image Information"""
        imageDom = self.boardDom.getElementsByTagName("image")[0]
        self.imagePath = imageDom.getAttribute("path")
        self.imageSize = imageDom.getAttribute("size")
        if self.imageSize[-1:] not in ("M", "G") or\
           not self.rbfUtils.isSizeInt(self.imageSize[0:-1]):
            self.imageSize = ""
            self.imagePath = ""
            return BoardTemplateCreator.INVALID_IMAGE_SIZE
        return 0

    def readKernelData(self):
        """Reads kernel information"""
        kernelDom = self.boardDom.getElementsByTagName("kernel")
        if kernelDom == []:
            return BoardTemplateCreator.NO_KERNEL
        for k in kernelDom:
            if not k.hasAttribute("type"):
                return BoardTemplateCreator.NO_KERNEL_TYPE
            self.kernelType = k.getAttribute("type")
            if self.kernelType == "custom":
                try:
                    self.kernelPath = \
                        k.getElementsByTagName('image')[0].childNodes[0].data
                    self.initrdPath = \
                        k.getElementsByTagName('initrd')[0].childNodes[0].data
                    self.dtbPath = \
                        k.getElementsByTagName('dtbdir')[0].childNodes[0].data
                    self.modulesPath = \
                        k.getElementsByTagName('modules')[0].childNodes[0].data
                except IndexError:
                    return BoardTemplateCreator.ERROR_CUSTOM_KERNEL_INFO
        return 0

    def readPartitions(self):
        """Reads Partition Information"""
        self.imageData = []
        self.primaryCount = 0
        self.totalPartitionCount = 0
        self.extendedStart = False
        invalidPartitionData = False
        partitionsDom = self.boardDom.getElementsByTagName("partitions")
        if partitionsDom == []:
            return BoardTemplateCreator.NO_PARTITIONS

        for partitions in partitionsDom:
            partition = partitions.getElementsByTagName("partition")
            for p in partition:
                ptype = p.getAttribute("type")
                pdata = [p.getAttribute("size"), ptype, p.getAttribute("fs"),\
                         p.getAttribute("mountpoint")]
                ret = self.validatePartitionData(pdata)
                if ret == 0:
                    if ptype in ("primary", "extended"):
                        self.primaryCount = self.primaryCount + 1
                    if ptype == "extended":
                        self.extendedStart = True
                    self.imageData.append(pdata)
                    self.totalPartitionCount = self.totalPartitionCount + 1
                else:
                    invalidPartitionData = True
                    break
            if invalidPartitionData:
                self.imageData = []
                self.primaryCount = 0
                self.totalPartitionCount = 0
                self.extendedStart = False
                return ret
        return 0

    def readRepoData(self):
        """Reads Repository Information"""
        self.repoData = []
        self.totalRepos = 0
        reposDom = self.boardDom.getElementsByTagName("repos")
        for repos in reposDom:
            repo = repos.getElementsByTagName("repo")
            for r in repo:
                if not (r.hasAttribute("name") and r.hasAttribute("path")):
                    return BoardTemplateCreator.INCORRECT_REPOSITORY
                rdata = [r.getAttribute("name"), r.getAttribute("path")]
                self.repoData.append(rdata)
                self.totalRepos = self.totalRepos + 1
        return 0

    def readPackages(self):
        """Reads Packages"""
        packagesDom = self.boardDom.getElementsByTagName("packages")
        if packagesDom == []:
            return BoardTemplateCreator.NO_PACKAGES
        for packageElement in packagesDom:
            try:
                groupPackageEl = packageElement.getElementsByTagName('group')[0]
                self.groupPackageString = groupPackageEl.childNodes[0].data
            except IndexError:
                self.groupPackageString = ""
            try:
                packageEl = packageElement.getElementsByTagName('package')[0]
                self.packageString = packageEl.childNodes[0].data
            except IndexError:
                self.packageString = ""
        return 0

    def readNetworkData(self):
        """Reads Network Data"""
        self.networkData = []
        self.totalNetworkInterfaces = 0
        badNetworkData = False
        networkDom = self.boardDom.getElementsByTagName("network")
        if networkDom == []:
            return BoardTemplateCreator.NO_NETWORK
        for n in networkDom:
            interface = n.getElementsByTagName("interface")
            for i in interface:
                name = i.getAttribute("name").lower()
                config = i.getAttribute("config").lower()
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
                        badNetworkData = True
                        continue
                else:
                    ipaddress = ""
                    subnetmask = ""
                    gateway = ""
                    dns1 = ""
                    dns2 = ""
                ndata = [name, config, ipaddress,\
                         subnetmask, gateway, dns1, dns2]
                self.networkData.append(ndata)
                self.totalNetworkInterfaces = self.totalNetworkInterfaces + 1
        if badNetworkData:
            return BoardTemplateCreator.BAD_NETWORK_DATA
        else:
            return 0

    def loadTemplate(self):
        """Loads User Selected Template"""
        if not os.path.isfile(self.xmlTemplate):
            return BoardTemplateCreator.NO_FILE

        ret = self.readXml()
        if ret != 0:
            self.showErrorMessage(ret)
            return ret

        ret = self.readTags()
        if ret != 0:
            self.showErrorMessage(ret)
        ret = self.readImageData()
        if ret != 0:
            self.showErrorMessage(ret)
        ret = self.readKernelData()
        if ret != 0:
            self.showErrorMessage(ret)
        ret = self.readPartitions()
        if ret != 0:
            self.showErrorMessage(ret)
        ret = self.readRepoData()
        if ret != 0:
            self.showErrorMessage(ret)
        ret = self.readPackages()
        if ret != 0:
            self.showErrorMessage(ret)
        ret = self.readNetworkData()
        if ret != 0:
            self.showErrorMessage(ret)

    def addInterface(self):
        """Add Network Interface"""
        while True:
            code = self.dialogInstance.scrollbox(\
                   self.getNetworkDisplayString(), width=100,\
                   extra_button=True, extra_label="Add Interface",\
                   title="Network Interface Details")
            if code == Dialog.EXTRA:
                elements = [("Name", 1, 1, "eth0", 1, 20, 8, 8),
                            ("Config(DHCP/Static)", 2, 1, "dhcp", 2, 20, 8, 8),
                            ("IP Addresss", 3, 1, "", 3, 20, 15, 15),
                            ("Netmask", 4, 1, "", 4, 20, 15, 15),
                            ("Gateway", 5, 1, "", 5, 20, 15, 15),
                            ("DNS1", 6, 1, "", 6, 20, 15, 15),
                            ("DNS2", 7, 1, "", 7, 20, 15, 15)]

                (code, fields) = self.dialogInstance.form("Network Interfaces",\
                                 elements, width=50)
                if code == Dialog.OK:
                    i = [fields[BoardTemplateCreator.IF_NAME].lower(),\
                         fields[BoardTemplateCreator.IF_CONFIG].lower(),\
                         fields[BoardTemplateCreator.IF_IP],\
                         fields[BoardTemplateCreator.IF_NETMASK],\
                         fields[BoardTemplateCreator.IF_GATEWAY],\
                         fields[BoardTemplateCreator.IF_DNS1],\
                         fields[BoardTemplateCreator.IF_DNS2]]
                    self.networkData.append(i)
                    self.totalNetworkInterfaces = \
                        self.totalNetworkInterfaces + 1
            else:
                break

    def deleteInterface(self):
        """Delete Network Interface"""
        while True:
            code = self.dialogInstance.scrollbox(\
                   self.getNetworkDisplayString(), width=100,\
                   extra_button=True, extra_label="Del Interface",\
                   title="Network Interface Details")
            if code == Dialog.EXTRA:
                (code, number) = self.dialogInstance.inputbox(\
                                 "Interface Number to Delete", init="",\
                                 title="Delete")
                if self.rbfUtils.isSizeInt(number):
                    n = int(number)
                    if n <= self.totalNetworkInterfaces:
                        self.totalNetworkInterfaces = \
                                                self.totalNetworkInterfaces - 1
                        del self.networkData[n-1]
                    else:
                        self.dialogInstance.msgbox("Enter a valid integer\n"\
                        + "You have defined "\
                        + str(self.totalNetworkInterfaces) + " interface(s)",\
                        title="Error")
            else:
                break

    def showInterface(self):
        """Show Network Interface Information"""
        self.dialogInstance.scrollbox(self.getNetworkDisplayString(),\
            width=100, title="Network Interface Details")

    def getNetworkDisplayString(self):
        """Generates Network Information String"""
        networkDisplayString = "%-6s%-5s%-7s%-16s%-16s%-16s%-16s%-16s\n\n" %\
        ("Index", "Name", "Config", "IP", "Netmask", "Gateway", "DNS1", "DNS2")
        for i in range(0, len(self.networkData)):
            networkDisplayString = networkDisplayString\
                 + "%-6s%-5s%-7s%-16s%-16s%-16s%-16s%-16s\n"\
                 % (str(i+1),\
                 self.networkData[i][BoardTemplateCreator.IF_NAME],\
                 self.networkData[i][BoardTemplateCreator.IF_CONFIG],\
                 self.networkData[i][BoardTemplateCreator.IF_IP],\
                 self.networkData[i][BoardTemplateCreator.IF_NETMASK],\
                 self.networkData[i][BoardTemplateCreator.IF_GATEWAY],\
                 self.networkData[i][BoardTemplateCreator.IF_DNS1],\
                 self.networkData[i][BoardTemplateCreator.IF_DNS2])
        return networkDisplayString

    def showEditInterfaceForm(self, n):
        """Edit Network Interface Form"""
        elements = [\
        ("Name", 1, 1,\
        self.networkData[n-1][BoardTemplateCreator.IF_NAME], 1, 20, 8, 8),
        ("Config(DHCP/Static)", 2, 1,\
        self.networkData[n-1][BoardTemplateCreator.IF_CONFIG], 2, 20, 8, 8),
        ("IP Addresss", 3, 1,\
        self.networkData[n-1][BoardTemplateCreator.IF_IP], 3, 20, 15, 15),
        ("Netmask", 4, 1,\
        self.networkData[n-1][BoardTemplateCreator.IF_NETMASK], 4, 20, 15, 15),
        ("Gateway", 5, 1,\
        self.networkData[n-1][BoardTemplateCreator.IF_GATEWAY], 5, 20, 15, 15),
        ("DNS1", 6, 1,\
        self.networkData[n-1][BoardTemplateCreator.IF_DNS1], 6, 20, 15, 15),
        ("DNS2", 7, 1,\
        self.networkData[n-1][BoardTemplateCreator.IF_DNS2], 7, 20, 15, 15)]

        (code, fields) = self.dialogInstance.form("Network Interfaces",\
                         elements, width=50, extra_button=True,\
                         extra_label="Delete")
        if code == Dialog.OK:
            self.networkData[n-1][BoardTemplateCreator.IF_NAME] = \
                fields[BoardTemplateCreator.IF_NAME].lower()
            self.networkData[n-1][BoardTemplateCreator.IF_CONFIG] = \
                fields[BoardTemplateCreator.IF_CONFIG].lower()
            self.networkData[n-1][BoardTemplateCreator.IF_IP] = \
                fields[BoardTemplateCreator.IF_IP]
            self.networkData[n-1][BoardTemplateCreator.IF_NETMASK] = \
                fields[BoardTemplateCreator.IF_NETMASK]
            self.networkData[n-1][BoardTemplateCreator.IF_GATEWAY] = \
                fields[BoardTemplateCreator.IF_GATEWAY]
            self.networkData[n-1][BoardTemplateCreator.IF_DNS1] = \
                fields[BoardTemplateCreator.IF_DNS1]
            self.networkData[n-1][BoardTemplateCreator.IF_DNS2] = \
                fields[BoardTemplateCreator.IF_DNS2]
        elif code == Dialog.EXTRA:
            self.totalNetworkInterfaces = self.totalNetworkInterfaces - 1
            del self.networkData[n-1]

    def editInterface(self):
        """Edit network interface scrollbox"""
        while True:
            code = \
                self.dialogInstance.scrollbox(self.getNetworkDisplayString(),\
                width=100, extra_button=True, extra_label="Edit Interface",\
                title="Network Interface Details")
            if code == Dialog.EXTRA:
                (code, number) = \
                    self.dialogInstance.inputbox("Interface Number to Edit",\
                    init="", title="Edit")
                if self.rbfUtils.isSizeInt(number):
                    n = int(number)
                    if n <= self.totalNetworkInterfaces:
                        self.showEditInterfaceForm(n)
                    else:
                        self.dialogInstance.msgbox("Enter a valid integer\n"\
                        + "You have defined "\
                        + str(self.totalNetworkInterfaces)\
                        + " interface(s)", title="Error")
            else:
                break

    def showNetworkConf(self):
        """Main Network Interface Dialog"""
        while True:
            (code, tag) = self.dialogInstance.menu("Network Configuration",\
                          width=0, height=0, menu_height=0,\
                          choices=[("Add", "Add an Interface"),
                                   ("Edit", "Edit an Interface"),
                                   ("Delete", "Delete an Interface"),
                                   ("Show", "Show Interfaces"),
                                   ("Done", "Exit Network Config")])
            if code in (Dialog.CANCEL, Dialog.ESC) or tag == "Done":
                break
            elif tag == "Add":
                self.addInterface()
            elif tag == "Edit":
                self.editInterface()
            elif tag == "Delete":
                self.deleteInterface()
            elif tag == "Show":
                self.showInterface()

    def setRootPass(self):
        """Set Root Password"""
        (code1, password1) = \
            self.dialogInstance.passwordbox("Enter Root Password",\
            insecure=True)
        if code1 == Dialog.OK:
            (code2, password2) = \
            self.dialogInstance.passwordbox("Enter Root Password Again",\
            insecure=True)
            if code2 == Dialog.OK:
                if password1 == password2:
                    self.rootPass = password2
                    self.dialogInstance.msgbox("Root Password Set",\
                    title="Password Set")
                else:
                    self.dialogInstance.msgbox("Passwords Don't Match",\
                    title="Password Error")

    def showSysConfig(self):
        """System Configuration"""
        while True:
            (code, tag) = \
                self.dialogInstance.menu("System Configuration", width=0,\
                height=0, menu_height=0,\
                choices=[("Hostname", self.hostName),
                         ("SELinux", self.selinuxConf),
                         ("Root Password", "Set Root Password Here"),
                         ("Root SSH Public Key", self.rootSshKey),
                         ("Network Settings", "Enter Network Config Here"),
                         ("Done", "Exit System Configuration")])
            if code in (Dialog.CANCEL, Dialog.ESC) or tag == "Done":
                break
            elif tag == "Hostname":
                (code, tag) = \
                    self.dialogInstance.inputbox("Please enter a Hostname",\
                    init=self.hostName)
                if code == Dialog.OK:
                    self.hostName = tag
            elif tag == "SELinux":
                selinuxChoices = \
                    {'Enforcing': 'SELinux security policy is enforced',\
                     'Permissive': 'SELinux prints warnings',\
                     'Disabled': 'No SELinux policy is loaded.'}
                configChoices = []

                for selinux in selinuxChoices.keys():
                    if self.selinuxConf == selinux.lower():
                        s = (selinux, selinuxChoices[selinux], 1)
                    else:
                        s = (selinux, selinuxChoices[selinux], 0)
                    configChoices.append(s)

                (code, tag) = \
                    self.dialogInstance.radiolist("Choose SELinux Config",\
                    width=65, choices=configChoices)
                if code == Dialog.OK:
                    self.selinuxConf = tag.lower()

            elif tag == "Root Password":
                self.setRootPass()
            elif tag == "Root SSH Public Key":
                self.rootSshKey = self.getFilePath(self.rootSshKey,\
                                  "Select Root SSH Public Key")
            elif tag == "Network Settings":
                self.showNetworkConf()

    def setPackageInstaller(self):
        """Sets Package Installer"""
        installerChoices = {'yum': 'Use Yum Package Installer',\
                            'dnf': 'Use Dnf Package Installer'}
        configChoices = []
        for installer in installerChoices.keys():
            if self.packageInstaller == installer.lower():
                i = (installer, installerChoices[installer], 1)
            else:
                i = (installer, installerChoices[installer], 0)
            configChoices.append(i)
        (code, tag) = self.dialogInstance.radiolist("Package Installer",\
                                                width=65, choices=configChoices)
        if code == Dialog.OK:
            self.packageInstaller = tag.lower()

    def showPackages(self):
        """Main Package Information Dialog"""
        while True:
            (code, tag) = self.dialogInstance.menu("Packages Menu", width=60,\
                          height=0, menu_height=0,\
                          choices=[("Package Installer", self.packageInstaller),
                                   ("Release Ver", self.releaseVer),
                                   ("Package Groups", self.groupPackageString),
                                   ("Packages", self.packageString),
                                   ("Done", "Exit Package Config")])
            if code in (Dialog.CANCEL, Dialog.ESC) or tag == "Done":
                break
            if tag == "Package Groups":
                (code, self.groupPackageString) = \
                    self.dialogInstance.inputbox("Comma Separated Groups",\
                    title="Package Groups", init=self.groupPackageString)
            elif tag == "Packages":
                (code, self.packageString) = \
                    self.dialogInstance.inputbox("Comma Separated Packages",\
                    title="Packages", init=self.packageString)
            elif tag == "Release Ver":
                (code, self.releaseVer) = \
                    self.dialogInstance.inputbox("Release Ver",\
                    title="Release Ver", init=self.releaseVer)
            elif tag == "Package Installer":
                self.setPackageInstaller()

    def generateTemplate(self):
        """Generates XML Template"""
        doc = Document()
        root = doc.createElement("template")
        board = doc.createElement("board")
        image = doc.createElement("image")
        partitions = doc.createElement("partitions")
        packages = doc.createElement("packages")
        stage1loader = doc.createElement("stage1loader")
        uboot = doc.createElement("uboot")
        rootfiles = doc.createElement("rootfiles")
        firmware = doc.createElement("firmware")
        kernel = doc.createElement("kernel")
        config = doc.createElement("config")
        etcoverlay = doc.createElement("etcoverlay")
        finalizescript = doc.createElement("finalizescript")
        distro = doc.createElement("distro")
        repos = doc.createElement("repos")
        workdir = doc.createElement("workdir")
        extlinuxconf = doc.createElement("extlinuxconf")

        doc.appendChild(root)
        for i in [board, image, partitions, packages, stage1loader, uboot,\
                  rootfiles, firmware, kernel, config, etcoverlay,\
                  finalizescript, distro, repos, workdir, extlinuxconf]:
            root.appendChild(i)

        board.appendChild(doc.createTextNode(self.boardName))
        image.setAttribute("size", self.imageSize)
        image.setAttribute("type", "raw")
        image.setAttribute("path", self.imagePath)

        for i in range(0, len(self.imageData)):
            partition = doc.createElement("partition")
            partition.setAttribute("size",\
                      self.imageData[i][BoardTemplateCreator.SIZE])
            partition.setAttribute("type",\
                      self.imageData[i][BoardTemplateCreator.PTYPE].lower())
            partition.setAttribute("fs",\
                      self.imageData[i][BoardTemplateCreator.FS].lower())
            partition.setAttribute("mountpoint",\
                      self.imageData[i][BoardTemplateCreator.MOUNTPOINT])
            partitions.appendChild(partition)

        groupPackage = doc.createElement("group")
        groupPackage.appendChild(doc.createTextNode(self.groupPackageString))
        package = doc.createElement("package")
        package.appendChild(doc.createTextNode(self.packageString))
        installer = doc.createElement("installer")
        installer.appendChild(doc.createTextNode(self.packageInstaller))
        releasever = doc.createElement("releasever")
        releasever.appendChild(doc.createTextNode(self.releaseVer))
        packages.appendChild(installer)
        packages.appendChild(releasever)
        packages.appendChild(groupPackage)
        packages.appendChild(package)

        stage1loader.appendChild(doc.createTextNode(self.stage1Loader))
        uboot.appendChild(doc.createTextNode(self.ubootPath))
        rootfiles.appendChild(doc.createTextNode(self.rootFiles))
        firmware.appendChild(doc.createTextNode(self.firmwarePath))

        kernel.setAttribute("type", self.kernelType)
        if self.kernelType == "custom":
            image = doc.createElement("image")
            image.appendChild(doc.createTextNode(self.kernelPath))
            initrd = doc.createElement("initrd")
            initrd.appendChild(doc.createTextNode(self.initrdPath))
            modules = doc.createElement("modules")
            modules.appendChild(doc.createTextNode(self.modulesPath))
            dtb = doc.createElement("dtbdir")
            dtb.appendChild(doc.createTextNode(self.dtbPath))
            for i in [image, initrd, modules, dtb]:
                kernel.appendChild(i)

        hostname = doc.createElement("hostname")
        hostname.appendChild(doc.createTextNode(self.hostName))
        selinux = doc.createElement("selinux")
        selinux.appendChild(doc.createTextNode(self.selinuxConf))
        rootpass = doc.createElement("rootpass")
        rootpass.appendChild(doc.createTextNode(self.rootPass))
        rootsshkey = doc.createElement("rootsshkey")
        rootsshkey.appendChild(doc.createTextNode(self.rootSshKey))
        network = doc.createElement("network")

        for i in [hostname, selinux, rootpass, rootsshkey, network]:
            config.appendChild(i)

        for i in range(0, len(self.networkData)):
            interface = doc.createElement("interface")
            interface.setAttribute("name",\
                self.networkData[i][BoardTemplateCreator.IF_NAME].lower())
            interface.setAttribute("config",\
                self.networkData[i][BoardTemplateCreator.IF_CONFIG].lower())
            network.appendChild(interface)
            if self.networkData[i][BoardTemplateCreator.IF_CONFIG] == "static":
                ipaddress = doc.createElement("ipaddress")
                ipText = self.networkData[i][BoardTemplateCreator.IF_IP]
                ipaddress.appendChild(doc.createTextNode(ipText))
                subnetmask = doc.createElement("subnetmask")
                nmaskText = self.networkData[i][BoardTemplateCreator.IF_NETMASK]
                subnetmask.appendChild(doc.createTextNode(nmaskText))
                gateway = doc.createElement("gateway")
                gwText = self.networkData[i][BoardTemplateCreator.IF_GATEWAY]
                gateway.appendChild(doc.createTextNode(gwText))
                dns1 = doc.createElement("dns1")
                dnsText = self.networkData[i][BoardTemplateCreator.IF_DNS1]
                dns1.appendChild(doc.createTextNode(dnsText))
                dns2 = doc.createElement("dns2")
                dnsText = self.networkData[i][BoardTemplateCreator.IF_DNS2]
                dns2.appendChild(doc.createTextNode(dnsText))
                for j in [ipaddress, subnetmask, gateway, dns1, dns2]:
                    interface.appendChild(j)

        etcoverlay.appendChild(doc.createTextNode(self.etcOverlay))
        finalizescript.appendChild(doc.createTextNode(self.finalizeScript))
        distro.appendChild(doc.createTextNode(self.linuxDistro))

        for i in range(0, len(self.repoData)):
            repo = doc.createElement("repo")
            repos.appendChild(repo)
            repo.setAttribute("name",
                              self.repoData[i][BoardTemplateCreator.REPO_NAME])
            repo.setAttribute("path",
                              self.repoData[i][BoardTemplateCreator.REPO_URL])

        workdir.appendChild(doc.createTextNode(self.workDir))
        extlinuxconf.appendChild(doc.createTextNode(self.extlinuxConf))
        return doc.toprettyxml()

    def writeTemplate(self):
        """Validates and writes template to file"""
        if self.boardName == "":
            self.dialogInstance.msgbox("You haven't selected any board.",\
                                       title="Board Error")
            return
        if not self.imageData:
            self.dialogInstance.msgbox("You don't have any paritions defined",\
                                       title="Partition Error")
            return
        if not self.repoData:
            self.dialogInstance.msgbox("You don't have any repos defined",\
                                       title="Repo Error")
            return
        if not self.networkData:
            self.dialogInstance.msgbox(\
            "You don't have any network interfaces defined.\nIgnoring",\
            title="Network Interface Error")

        xmlData = self.generateTemplate()

        (code, dirpath) = self.dialogInstance.dselect(self.lastKnownPath,\
                          10, 50, title="Select Directory to Save Template")
        if code == Dialog.OK:
            (code, filename) = self.dialogInstance.inputbox(\
                               "XML Template Filename")
            if code == Dialog.OK:
                try:
                    self.generatedXmlPath = os.path.join(dirpath, filename)
                    fileWriter = open(self.generatedXmlPath, "w")
                    fileWriter.write(xmlData)
                    fileWriter.close()
                    self.dialogInstance.msgbox("Saved Template to "\
                    + self.generatedXmlPath, width=80, title="Save Template")
                except IOError:
                    self.generatedXmlPath = ""
                    self.dialogInstance.msgbox("Error Saving Template",\
                                               title="Error")

    def generateImage(self):
        """Displays command to generate image from xml template"""
        if self.getFilename(self.generatedXmlPath) == "":
            self.dialogInstance.msgbox("No XML Generated Yet. "\
                                       + "Please select 'Save Template' first",\
                                       width=80, title="No XML Generated Yet")
            return
        if not os.path.exists(self.generatedXmlPath):
            self.dialogInstance.msgbox(self.generatedXmlPath + "does not exist")
            return
        self.dialogInstance.msgbox("To Generate Image " + self.imagePath +\
                                   " using " + self.generatedXmlPath +\
                                   " Please run\n\n./rbf.py build " +\
                                   self.generatedXmlPath, width=80,\
                                   title="Generate Command")

    @classmethod
    def getFilename(cls, filepath):
        """Get Filename"""
        if "/" not in filepath:
            return filepath
        return filepath[filepath.rfind("/")+1:]

    def viewTemplate(self):
        """Display XML Template exactly as it will be written to file"""
        xmlData = self.generateTemplate()
        self.dialogInstance.scrollbox(xmlData)

    def mainMenu(self):
        """Displays Main RootFS Build Factory Menu"""
        while True:
            (code, tag) = \
                self.dialogInstance.menu("Main Menu", width=0, height=0,\
                menu_height=0,\
                choices=[\
                ("Load Template",\
                            self.xmlTemplate[self.xmlTemplate.rfind("/")+1:]),
                ("Board Info", "Selected Board: " + self.boardName),
                ("Image Path", "Image: " + \
                            self.imagePath + " " + self.imageSize),
                ("Partitions", "Define Partition Layout"),
                ("Bootloader", "Bootloader Options"),
                ("Kernel", "Kernel Config"),
                ("Repositories", "Enter Repo Config"),
                ("Packages", "Packages to Install"),
                ("Misc", "Misc Settings"),
                ("System Config", "System Settings"),
                ("View Template", "View Current Template"),
                ("Save Template", "Filename: " + \
                            self.getFilename(self.generatedXmlPath)),
                ("Generate Image", "Using Template: " + \
                            self.getFilename(self.generatedXmlPath)),
                ("Exit", "Exit Board Template Writer")])

            if code in (Dialog.CANCEL, Dialog.ESC) or tag == "Exit":
                break
            elif tag == "Load Template":
                self.xmlTemplate = self.getFilePath(self.xmlTemplate,\
                                   "Select XML Template")
                self.loadTemplate()
            elif tag == "Board Info":
                self.showBoards()
            elif tag == "Image Path":
                self.showImageInfo()
            elif tag == "Partitions":
                self.showPartitionInfo()
            elif tag == "Bootloader":
                self.showBootInfo()
            elif tag == "Kernel":
                self.showKernelInfo()
            elif tag == "Repositories":
                self.showRepoConf()
            elif tag == "Packages":
                self.showPackages()
            elif tag == "Misc":
                self.showMiscInfo()
            elif tag == "System Config":
                self.showSysConfig()
            elif tag == "View Template":
                self.viewTemplate()
            elif tag == "Save Template":
                self.writeTemplate()
            elif tag == "Generate Image":
                self.generateImage()

if __name__ == "__main__":
    if os.getuid() != 0:
        print("You need to be root to use RootFS Build Factory")
        sys.exit(1)

    d = BoardTemplateCreator()
    d.mainMenu()

