#!/usr/bin/python2

import os
import sys
from dialog import Dialog
from rbfutils import RbfUtils
from xml.dom.minidom import parse, Document

class BoardTemplateCreator():
    SIZE, PTYPE, FS, MOUNTPOINT = range (0,4)
    REPO_NAME, REPO_URL = range(0,2)
    IF_NAME, IF_CONFIG, IF_IP, IF_NETMASK, IF_GATEWAY, IF_DNS1, IF_DNS2 = range(0,7)
    BOARDS_DIR="boards.d"
    def __init__(self):
        #self.dialogInstance = Dialog(dialog="Xdialog", compat="Xdialog")
        self.dialogInstance = Dialog(dialog="dialog")
        self.rbfUtils = RbfUtils()
        self.dialogInstance.add_persistent_args(["--backtitle", "RootFS Build Factory"])
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
        self.firmwarePath = "none"
        self.extlinuxConf = "false"
        self.kernelType = "stock"
        self.kernelPath = "none"
        self.initrdPath = "none"
        self.modulesPath = "none"
        self.dtbPath = "none"
        self.repoData = []
        self.totalRepos = 0
        self.groupPackageString = "@core"
        self.packageString = ""
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
        self.lastKnownPath = self.homePath
        self.generatedXmlPath = ""
        
    def showBoards(self):
        """Shows a radiolist of supported boards"""
        knownBoards = os.listdir(BoardTemplateCreator.BOARDS_DIR)
        boardChoices=[]        
        for board in knownBoards:
            if board == "finalize.sh":
                continue
            if board[0:-3] == self.boardName:
                b = (board[0:-3].title(),"Run boards.d/"+board+" Script",1)
            else:
                b = (board[0:-3].title(),"Run boards.d/"+board+" Script",0)
            boardChoices.append(b)
        boardChoices.append(("Custom","You will have to customize Image yourself",0))
        (code, tag) = self.dialogInstance.radiolist("Supported Boards", width=65, choices=boardChoices)
        if code == Dialog.OK:
            self.boardName = tag.lower()
    
    def showImageInfo(self):
        """Allows you to select directory and filename of image"""
        
        while True:
            if self.imagePath != "" and self.imagePath.rfind("/") != -1:
                imageName = self.imagePath[self.imagePath.rfind("/")+1:]
            else:
                imageName = "rootfs-image.img"
                
            (code, path) = self.dialogInstance.dselect(self.lastKnownPath, 10, 50, title="Select Directory")
            if code in (Dialog.CANCEL, Dialog.ESC):
                    break
            (code, filename) = self.dialogInstance.inputbox("Please enter a filename", init=imageName)
            self.imagePath = path + os.sep + filename
            self.lastKnownPath = path
            
            if code in (Dialog.CANCEL, Dialog.ESC):
                break
            while True:
                (code, filesize) = self.dialogInstance.inputbox("Please enter a size with suffix M for Megabytes and G for Gigabyes", init="4G")
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
        partitionDisplayString=""
        if len(self.imageData) == 0:
            partitionDisplayString="No Partitions Defined"
        else:
            partitionDisplayString=""
            #partitionDisplayString="Index\tSize\tType\tFilesystem\tMountPoint\n"            
            #partitionDisplayString= "%-10s\t%-10s\t%-10s\t%-10s\t%-10s\n" % ("Index", "Size", "Type", "Filesystem", "MountPoint")
            for i in range(0, len(self.imageData)):
                #partitionDisplayString = partitionDisplayString + ("%-10s %-10s %-10s %-10s %-10s\n") % (str(i+1), self.imageData[i][BoardTemplateCreator.SIZE], self.imageData[i][BoardTemplateCreator.PTYPE], self.imageData[i][BoardTemplateCreator.FS], self.imageData[i][BoardTemplateCreator.MOUNTPOINT])
                #partitionDisplayString = partitionDisplayString + "{0:-20}{1:20}{2:20}{3:20}{4:20}\n".format(str(i+1), self.imageData[i][BoardTemplateCreator.SIZE], self.imageData[i][BoardTemplateCreator.PTYPE], self.imageData[i][BoardTemplateCreator.FS], self.imageData[i][BoardTemplateCreator.MOUNTPOINT])
                partitionDisplayString = partitionDisplayString + str(i+1).expandtabs(20) + "\t".expandtabs(20) + self.imageData[i][BoardTemplateCreator.SIZE] + "\t".expandtabs(20) + self.imageData[i][BoardTemplateCreator.PTYPE] + "\t".expandtabs(20) + self.imageData[i][BoardTemplateCreator.FS] + "\t".expandtabs(20) + self.imageData[i][BoardTemplateCreator.MOUNTPOINT] + "\n"
            print(partitionDisplayString)
        return partitionDisplayString
    
    def validatePartitionData(self, fields):
        if self.imageSize == "":
            self.dialogInstance.msgbox("Please create an Image first")
            return False
       
        if fields[BoardTemplateCreator.SIZE][-1:] not in ("M","G"):
            self.dialogInstance.msgbox("Invalid Size. Has to be an Integer with suffix M for MB and G for GB",width=80,title="Partition Size Error")
            return False
        
        if self.extendedStart == True and fields[BoardTemplateCreator.PTYPE].lower() == "extended":
            self.dialogInstance.msgbox("Only 1 Extended Partition Allowed")
            return False
        
        #only 4 primary partitions supported
        if self.primaryCount >= 4 and fields[BoardTemplateCreator.PTYPE].lower() in ("primary","extended"):            
            self.dialogInstance.msgbox("Cannot create more than 4 primary partitions",title="Partition Error")
            return False
            
        #check if total size of primary partitions exceed image size
        if fields[BoardTemplateCreator.PTYPE].lower() in ("primary","extended"):            
            imageSizeInM = int(self.rbfUtils.getImageSizeInM(self.imageSize)[0:-1])
            primaryPartSize = 0
            for i in range(0,len(self.imageData)):
                if self.imageData[i][BoardTemplateCreator.PTYPE].lower() in ("primary","extended"):
                    primaryPartSize = primaryPartSize + int(self.rbfUtils.getImageSizeInM(self.imageData[i][BoardTemplateCreator.SIZE])[0:-1])
            
            primaryPartSize = primaryPartSize + int(self.rbfUtils.getImageSizeInM(fields[BoardTemplateCreator.SIZE])[0:-1])
            if primaryPartSize > imageSizeInM:
                self.dialogInstance.msgbox("Primary Partition Sizes exceed Image Size",width=80,title="Partition Error")
                return False
                    
        #check if user is trying to create a logical partition before an extended one
        if self.extendedStart == False and fields[BoardTemplateCreator.PTYPE].lower() == "logical":            
                self.dialogInstance.msgbox("Cannot Create Logical Before Extended",title="Partition Error")
                return False        
            
        
        #check if logical partition sizes exceed extended partition size
        if fields[BoardTemplateCreator.PTYPE].lower() == "logical":
            logicalPartitionSizes = 0
            for i in range(0,len(self.imageData)):
                size = self.rbfUtils.getImageSizeInM(self.imageData[i][BoardTemplateCreator.SIZE])
                if self.imageData[i][BoardTemplateCreator.PTYPE].lower() == "extended":
                    extendedPartitionSize = int(size[0:-1])
                if self.imageData[i][BoardTemplateCreator.PTYPE].lower() == "logical":
                    logicalPartitionSizes = logicalPartitionSizes + int(size[0:-1])
            
            logicalPartitionSizes = logicalPartitionSizes + int(self.rbfUtils.getImageSizeInM(fields[BoardTemplateCreator.SIZE])[0:-1])
            if logicalPartitionSizes > extendedPartitionSize:
                self.dialogInstance.msgbox("Logical Partition Sizes Exceed Extended Partition Size", title="Logical Partition Error")
                return False

        return True        
            
    def addPartition(self):
        while True:
            code = self.dialogInstance.msgbox(self.getPartitionDisplayString(), width=50, extra_button=True, extra_label="Add", title="Partition Details")
            if code == Dialog.EXTRA:
                elements = [ ("Size (M/G)", 1, 1, "1G", 1, 20, 8, 8),
                             ("Partition Type", 2, 1, "Primary", 2, 20, 8, 8),
                             ("Filesystem", 3, 1, "ext3", 3, 20, 8, 4),
                             ("Mount Point", 4, 1, "/", 4, 20, 8, 8)]
                             
                (code, fields) = self.dialogInstance.form("Partition Info",elements,width=50)
                
                if code == Dialog.OK:

                    if self.validatePartitionData(fields):
                        if fields[BoardTemplateCreator.PTYPE].lower() in ("primary","extended"):
                            self.primaryCount = self.primaryCount + 1
                            
                        #ignore FS and MOUNTPOINT for Extended Partition    
                        if fields[BoardTemplateCreator.PTYPE].lower() == "extended":
                            self.extendedStart = True
                            fields[BoardTemplateCreator.FS] = ""
                            fields[BoardTemplateCreator.MOUNTPOINT] = ""
                        #ignore MOUNTPOINT for swap    
                        elif fields[BoardTemplateCreator.PTYPE].lower() == "swap":
                            fields[BoardTemplateCreator.MOUNTPOINT] = ""
                            
                        p = [ fields[BoardTemplateCreator.SIZE], fields[BoardTemplateCreator.PTYPE], fields[BoardTemplateCreator.FS], fields[BoardTemplateCreator.MOUNTPOINT] ]
                        self.imageData.append(p)
                        self.totalPartitionCount = self.totalPartitionCount + 1
            else:
                break
        
    def performDelteOperation(self, n):
        self.totalPartitionCount = self.totalPartitionCount - 1
        if self.imageData[n-1][BoardTemplateCreator.PTYPE].lower() in ("primary","extended"):
            self.primaryCount = self.primaryCount - 1                        
        if self.imageData[n-1][BoardTemplateCreator.PTYPE].lower() == "extended":
            self.extendedStart = False
            for i in list(reversed(range(0,len(self.imageData)))):
                if self.imageData[i][BoardTemplateCreator.PTYPE].lower() == "logical":
                    del self.imageData[i]
        del self.imageData[n-1]
        
        
    def deletePartition(self):
        while True:
            code = self.dialogInstance.msgbox(self.getPartitionDisplayString(), width=50, extra_button=True, extra_label="Delete", title="Partition Details")
            if code == Dialog.EXTRA:
                (code, number) = self.dialogInstance.inputbox("Partition Number to Delete", init="",title="Delete")
                if self.rbfUtils.isSizeInt(number):
                    n = int(number)
                    if n <= self.totalPartitionCount:
                        self.performDelteOperation(n)
                    else:
                        self.dialogInstance.msgbox("Enter a valid integer\nYou have defined " + str(self.totalPartitionCount) + " Partition(s)", title="Error")
            else:
                break
                
   
                
    def showPartition(self):
        code = self.dialogInstance.msgbox(self.getPartitionDisplayString(),title="Partition Details",width=50)
        
    def showPartitionInfo(self):        
        """Create Partition Layout"""
        while True:
            (code, tag) = self.dialogInstance.menu(
            "Partition Menu",
            width=60,
            choices=[("Add", "Add a Partition"),
                     ("Delete", "Delete a Partition"),
                     ("Show", "Define Partition Layout"),
                     ("Done", "Select this if you are done configuring")])
            
            if tag == "Add":
                self.addPartition()
            elif tag == "Delete":
                self.deletePartition()
            elif tag == "Show":
                self.showPartition()
            elif tag == "Done":
                break
    
    def getPath(self,var, message):
        (ret, filepath) = self.dialogInstance.fselect(self.lastKnownPath, 10, 50, title=message, extra_button=True, extra_label="None")
        if ret == Dialog.OK:
            self.lastKnownPath = filepath[0:filepath.rfind("/")+1]
            return filepath
        elif ret == Dialog.EXTRA:
            return "none"
        else:
            return var
    
    
    def getFilePath(self,var, message):
        (ret, filepath) = self.dialogInstance.fselect(self.lastKnownPath, 10, 50, title=message, extra_button=True, extra_label="None")
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
            
    def getDirPath(self,var,message):
        (ret, dirpath) = self.dialogInstance.dselect(self.lastKnownPath, 10, 50, title="Select Firmware Dir", extra_button=True, extra_label="None")        
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
            (code, tag) = self.dialogInstance.menu("Bootloader Menu", width=60,
            choices=[("Stage1 Loader", self.stage1Loader),
                     ("U-Boot", self.ubootPath),
                     ("Root Files", self.rootFiles),
                     ("Firmware Dir", self.firmwarePath),
                     ("Extlinux Conf", self.extlinuxConf),
                     ("Done", "Exit Bootloader Config")])
                     
            if code in (Dialog.CANCEL, Dialog.ESC):
                break
            if tag == "Stage1 Loader":  
                self.stage1Loader = self.getFilePath(self.stage1Loader, "Select Stage1 Loader")
            elif tag == "U-Boot":
                self.ubootPath = self.getFilePath(self.ubootPath, "Select U-Boot")
            elif tag == "Root Files":
                self.rootFiles = self.getFilePath(self.rootFiles, "Select Root Files")
            elif tag == "Firmware Dir":
                self.firmwarePath = self.getDirPath(self.firmwarePath, "Select Firmware Dir")
            elif tag == "Extlinux Conf":
                if self.extlinuxConf == "false":
                    extlinuxChoices = (["Yes", "Configure /boot/extlinux/extlinux.conf", 0],
                                       ["No", "Do not configure extlinux", 1])
                else:
                    extlinuxChoices = (["Yes", "Configure /boot/extlinux/extlinux.conf", 1],
                                       ["No", "Do not configure extlinux", 0])
                (code, tag) = self.dialogInstance.radiolist("Supported Boards", width=65, choices=extlinuxChoices)
                if code == Dialog.OK:
                    if tag == "Yes":
                        self.extlinuxConf = "true"
                    else:
                        self.extlinuxConf = "false"
            else:
                break
    
    def showKernelInfo(self):
        while True:
            kernelChoices = []
            kernelChoices.append(["Kernel Type", self.kernelType])
            if self.kernelType.lower() == "custom":
                kernelChoices.append(["Image", self.kernelPath])
                kernelChoices.append(["Initrd", self.initrdPath])
                kernelChoices.append(["Modules", self.modulesPath])
                kernelChoices.append(["DTB", self.dtbPath])
            kernelChoices.append(["Done", "Exit Kernel Config"])
            (code, tag) = self.dialogInstance.menu("Kernel Menu", width=60, choices=kernelChoices)
            if code in (Dialog.CANCEL, Dialog.ESC):
                break;
            if tag == "Kernel Type":
                ktypeChoices = {'Stock': 'Use Distribution Kernel','Custom': 'Specify Kernel', 'None': 'No Kernel'}
                typeChoices = []
                
                for ktype in ktypeChoices.keys():
                    if self.kernelType == ktype.lower():
                        k = (ktype, ktypeChoices[ktype], 1)
                    else:
                        k = (ktype, ktypeChoices[ktype], 0)
                    typeChoices.append(k)
                    
                (code, tag) = self.dialogInstance.radiolist("Choose Kernel Type", width=65, choices=typeChoices)
                if code == Dialog.OK:
                    self.kernelType = tag.lower()
            if tag == "Image":
                self.kernelPath = self.getFilePath(self.kernelPath,"Kernel Image")
            elif tag == "Initrd":
                self.initrdPath = self.getFilePath(self.initrdPath,"Initrd Image")
            elif tag == "Modules":
                self.modulesPath = self.getDirPath(self.modulesPath,"Modules Dir")
            elif tag == "DTB":
                self.dtbPath = self.getPath(self.dtbPath,"DTB Path")
            elif tag == "Done":
                break
    
    def showMiscInfo(self):
        """Misc Settings"""
        while True:
            (code, tag) = self.dialogInstance.menu("Misc Settings",width=60,
            choices=[("Etc Overlay", self.etcOverlay),
                     ("Finalize Script", self.finalizeScript),
                     ("Distro Name", self.linuxDistro),
                     ("Work Dir", self.workDir),
                     ("Done", "Exit Misc Settings")])
            if code in (Dialog.CANCEL,Dialog.ESC):
                break;
            if tag == "Etc Overlay":
                self.etcOverlay = self.getDirPath(self.etcOverlay, "Select etc Overlay Dir")
            elif tag == "Finalize Script":
                self.finalizeScript = self.getFilePath(self.finalizeScript, "Select Finalize Script")
            elif tag == "Work Dir":
                self.workDir = self.getDirPath(self.workDir, "Select Work Dir")
            elif tag == "Done":
                break
    
    def addRepo(self):
        while True:
            code = self.dialogInstance.msgbox(self.getRepoDisplayString(), width=100, extra_button=True, extra_label="Add Repo", title="Repo Details")
            if code == Dialog.EXTRA:
                elements = [ ("Name", 1, 1, "", 1, 20, 20, 20),
                             ("BaseURL", 2, 1, "", 2, 20, 20, 512)]
                             
                code, fields = self.dialogInstance.form("Repo Info",elements,width=50)
                if code == Dialog.OK:
                    r = [ fields[BoardTemplateCreator.REPO_NAME], fields[BoardTemplateCreator.REPO_URL] ]
                    self.repoData.append(r)
                    self.totalRepos = self.totalRepos + 1
            else:
                break
    
    def deleteRepo(self):
        while True:
            code = self.dialogInstance.msgbox(self.getRepoDisplayString(), width=100, extra_button=True, extra_label="Del Repo", title="Repo Details")
            if code == Dialog.EXTRA:
                (code, number) = self.dialogInstance.inputbox("Repo Number to Delete", init="",title="Delete")
                if self.rbfUtils.isSizeInt(number):
                    n = int(number)
                    if n <= self.totalRepos:
                        self.totalRepos = self.totalRepos - 1
                        del self.repoData[n-1]
                    else:
                        self.dialogInstance.msgbox("Enter a valid integer\nYou have defined " + str(self.totalRepos) + " repo(s)", title="Error")
            else:
                break
                                
    def showRepo(self):
        code = self.dialogInstance.msgbox(self.getRepoDisplayString(),title="Repo Details",width=100)
    
    def getRepoDisplayString(self):
        repoDisplayString = ""
        for i in range(0,len(self.repoData)):
            repoDisplayString = repoDisplayString + str(i+1) + "\t" + self.repoData[i][BoardTemplateCreator.REPO_NAME] + "\t" + self.repoData[i][BoardTemplateCreator.REPO_URL] + "\n"
        return repoDisplayString
       
    def showEditRepoForm(self,n):
        elements = [ ("Name", 1, 1, self.repoData[n-1][BoardTemplateCreator.REPO_NAME], 1, 20, 20, 20),
                     ("Base URL", 2, 1, self.repoData[n-1][BoardTemplateCreator.REPO_URL], 2, 20, 20, 512)]
                     
        code, fields = self.dialogInstance.form("Edit Partition", elements, width=50, extra_button=True, extra_label="Delete")
        if code == Dialog.OK:
            self.repoData[n-1][BoardTemplateCreator.REPO_NAME] = fields[BoardTemplateCreator.REPO_NAME]
            self.repoData[n-1][BoardTemplateCreator.REPO_URL] = fields[BoardTemplateCreator.REPO_URL]
        elif code == Dialog.EXTRA:
            self.totalRepos = self.totalRepos - 1
            del self.repoData[n-1]
    
    def editRepo(self):
        while True:
            code = self.dialogInstance.msgbox(self.getRepoDisplayString(), width=100, extra_button=True, extra_label="Edit Repo", title="Repo Details")
            if code == Dialog.EXTRA:
                (code, number) = self.dialogInstance.inputbox("Repo Number to Edit", init="",title="Edit")
                if self.rbfUtils.isSizeInt(number):
                    n = int(number)
                    if n <= self.totalRepos:
                        self.showEditRepoForm(n)
                    else:
                        self.dialogInstance.msgbox("Enter a valid integer\nYou have defined " + str(self.totalRepos) + " repo(s)", title="Error")
            else:
                break 
    
    def showRepoConf(self):
        """Repo Conf"""
        while True:
            (code, tag) = self.dialogInstance.menu(
            "Repository Menu",
            width=60,
            choices=[("Add", "Add a Repo"),
                     ("Edit", "Edit a Repo"),
                     ("Delete", "Delete a Repo"),
                     ("Show", "Show Repos"),
                     ("Done", "Select this if you are done configuring")])
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
    
    def getTagValue(self, dom, domTag):
        """Extracts Tag Value from DOMTree"""
        xmlTag = dom.getElementsByTagName(domTag)
        for x in xmlTag:
            return x.childNodes[0].data            
    
    def loadTemplate(self):
        self.xmlTemplate = self.getFilePath(self.xmlTemplate,"Select XML Template")
        if not os.path.isfile(self.xmlTemplate):
            return
        try:
            self.boardDom = parse(self.xmlTemplate)
        except:
            self.dialogInstance.msgbox("Error Parsing XML Template File")
            self.xmlTemplate="none"
            return
        
        #try:    
        self.boardName = self.getTagValue(self.boardDom,"board")        
        self.workDir = self.getTagValue(self.boardDom,"workdir")        
        self.finalizeScript = self.getTagValue(self.boardDom,"finalizescript")
        self.selinuxConf = self.getTagValue(self.boardDom,"selinux")
        self.etcOverlay = self.getTagValue(self.boardDom,"etcoverlay")
        self.linuxDistro = self.getTagValue(self.boardDom,"distro")
        self.extlinuxConf = self.getTagValue(self.boardDom,"extlinuxconf")
        self.hostName = self.getTagValue(self.boardDom,"hostname")
        self.rootFiles = self.getTagValue(self.boardDom,"rootfiles")
        self.stage1Loader = self.getTagValue(self.boardDom,"stage1loader")
        self.ubootPath = self.getTagValue(self.boardDom,"uboot")
        self.firmwareDir = self.getTagValue(self.boardDom,"firmware")
        
        imageDom = self.boardDom.getElementsByTagName("image")[0]
        self.imagePath = imageDom.getAttribute("path")
        self.imageSize = imageDom.getAttribute("size")
        
        kernelDom = self.boardDom.getElementsByTagName("kernel")
        for k in kernelDom:
            self.kernelType = k.getAttribute("type")
            if self.kernelType == "custom":
                try:
                    self.kernelPath = k.getElementsByTagName('image')[0].childNodes[0].data
                    self.initrdPath = k.getElementsByTagName('initrd')[0].childNodes[0].data
                    self.dtbPath = k.getElementsByTagName('dtbdir')[0].childNodes[0].data
                    self.modulesPath = k.getElementsByTagName('modules')[0].childNodes[0].data
                except:
                    self.dialogInstance.msgbox("Error reading Custom Kernel Info",title="Custom Kernel Error")
    
        self.imageData = []    
        self.primaryCount = 0
        self.totalPartitionCount = 0
        self.extendedStart = False
        partitionsDom = self.boardDom.getElementsByTagName("partitions")
        for partitions in partitionsDom:
            partition = partitions.getElementsByTagName("partition")
            for p in partition:
                ptype = p.getAttribute("type")
                pdata = [p.getAttribute("size"), ptype, p.getAttribute("fs"), p.getAttribute("mountpoint")]
                self.imageData.append(pdata)
                self.totalPartitionCount = self.totalPartitionCount + 1
                if ptype in ("primary","extended"):
                    self.primaryCount = self.primaryCount + 1
                if self.extendedStart == True and ptype == "extended":
                    self.dialogInstance.msgbox("Cannot have more than 1 Extended Partition",title="Partition Error")
                if ptype == "extended":
                    self.extendedStart = True
       
        self.repoData = []
        self.totalRepos = 0
        reposDom = self.boardDom.getElementsByTagName("repos")
        for repos in reposDom:
            repo = repos.getElementsByTagName("repo")
            for r in repo:
                rdata = [r.getAttribute("name"), r.getAttribute("path")]
                self.repoData.append(rdata)
                self.totalRepos = self.totalRepos + 1
                
        packagesDom = self.boardDom.getElementsByTagName("packages")
        for packageElement in packagesDom:
            try:
                self.groupPackageString = packageElement.getElementsByTagName('group')[0].childNodes[0].data
            except:
                self.groupPackageString = ""
            try: 
                self.packageString = packageElement.getElementsByTagName('package')[0].childNodes[0].data
            except:
                self.packageString = ""
         
        self.networkData = []
        self.totalNetworkInterfaces = 0
        networkDom = self.boardDom.getElementsByTagName("network")
        for n in networkDom:
            interface = n.getElementsByTagName("interface")
            for i in interface:
                name = i.getAttribute("name").lower()
                config = i.getAttribute("config").lower()
                if config == "static":
                    ipaddress = i.getElementsByTagName("ipaddress")[0].childNodes[0].data
                    subnetmask = i.getElementsByTagName("subnetmask")[0].childNodes[0].data
                    gateway = i.getElementsByTagName("gateway")[0].childNodes[0].data
                    nameserver = i.getElementsByTagName("nameserver")[0].childNodes[0].data
                else:
                    ipaddress = ""
                    subnetmask = ""
                    gateway = ""
                    nameserver = ""
                ndata = [name, config, ipaddress, subnetmask, gateway, nameserver, "" ]
                self.networkData.append(ndata)
                self.totalNetworkInterfaces = self.totalNetworkInterfaces + 1
        #except:                        
        #    self.dialogInstance.msgbox("Incorrect XMl. Please load a working one")
        
        
    def addInterface(self):
        while True:
            code = self.dialogInstance.msgbox(self.getNetworkDisplayString(), width=100, extra_button=True, extra_label="Add Interface", title="Network Interface Details")
            if code == Dialog.EXTRA:
                elements = [ ("Name", 1, 1, "eth0", 1, 20, 8, 8),
                             ("Config(DHCP/Static)", 2, 1, "dhcp", 2, 20, 8, 8),
                             ("IP Addresss", 3, 1, "", 3, 20, 15, 15),
                             ("Netmask", 4, 1, "", 4, 20, 15, 15),
                             ("Gateway", 5, 1, "", 5, 20, 15, 15),
                             ("DNS1", 6, 1, "", 6, 20, 15, 15),
                             ("DNS2", 7, 1, "", 7, 20, 15, 15)]
                             
                code, fields = self.dialogInstance.form("Network Interfaces",elements,width=50)
                if code == Dialog.OK:
                    i = [ fields[BoardTemplateCreator.IF_NAME].lower(), fields[BoardTemplateCreator.IF_CONFIG].lower(), fields[BoardTemplateCreator.IF_IP], fields[BoardTemplateCreator.IF_NETMASK], fields[BoardTemplateCreator.IF_GATEWAY], fields[BoardTemplateCreator.IF_DNS1], fields[BoardTemplateCreator.IF_DNS2]]
                    self.networkData.append(i)
                    self.totalNetworkInterfaces = self.totalNetworkInterfaces + 1
            else:
                break
    
    def deleteInterface(self):
        while True:
            code = self.dialogInstance.msgbox(self.getNetworkDisplayString(), width=100, extra_button=True, extra_label="Del Interface", title="Network Interface Details")
            if code == Dialog.EXTRA:
                (code, number) = self.dialogInstance.inputbox("Interface Number to Delete", init="",title="Delete")
                if self.rbfUtils.isSizeInt(number):
                    n = int(number)
                    if n <= self.totalNetworkInterfaces:
                        self.totalNetworkInterfaces = self.totalNetworkInterfaces - 1
                        del self.networkData[n-1]
                    else:
                        self.dialogInstance.msgbox("Enter a valid integer\nYou have defined " + str(self.totalNetworkInterfaces) + " interface(s)", title="Error")
            else:
                break
                                
    def showInterface(self):
        code = self.dialogInstance.msgbox(self.getNetworkDisplayString(), width=100, title="Network Interface Details")
    
    def getNetworkDisplayString(self):
        networkDisplayString = ""
        for i in range(0,len(self.networkData)):
            networkDisplayString = networkDisplayString + str(i+1) + "\t" + self.networkData[i][BoardTemplateCreator.IF_NAME] + "\t" + self.networkData[i][BoardTemplateCreator.IF_CONFIG] + "\t" + self.networkData[i][BoardTemplateCreator.IF_IP] + "\t" + self.networkData[i][BoardTemplateCreator.IF_NETMASK] + "\t" + self.networkData[i][BoardTemplateCreator.IF_GATEWAY] + "\t" + self.networkData[i][BoardTemplateCreator.IF_DNS1] + "\t" + self.networkData[i][BoardTemplateCreator.IF_DNS2] + "\n"
        return networkDisplayString
    
    def showEditInterfaceForm(self,n):
        elements = [ ("Name", 1, 1, self.networkData[n-1][BoardTemplateCreator.IF_NAME], 1, 20, 8, 8),
                     ("Config(DHCP/Static)", 2, 1, self.networkData[n-1][BoardTemplateCreator.IF_CONFIG], 2, 20, 8, 8),
                     ("IP Addresss", 3, 1, self.networkData[n-1][BoardTemplateCreator.IF_IP], 3, 20, 15, 15),
                     ("Netmask", 4, 1, self.networkData[n-1][BoardTemplateCreator.IF_NETMASK], 4, 20, 15, 15),
                     ("Gateway", 5, 1, self.networkData[n-1][BoardTemplateCreator.IF_GATEWAY], 5, 20, 15, 15),
                     ("DNS1", 6, 1, self.networkData[n-1][BoardTemplateCreator.IF_DNS1], 6, 20, 15, 15),
                     ("DNS2", 7, 1, self.networkData[n-1][BoardTemplateCreator.IF_DNS2], 7, 20, 15, 15)]
                             
        code, fields = self.dialogInstance.form("Network Interfaces",elements,width=50, extra_button=True, extra_label="Delete")
        if code == Dialog.OK:
            self.networkData[n-1][BoardTemplateCreator.IF_NAME] = fields[BoardTemplateCreator.IF_NAME].lower()
            self.networkData[n-1][BoardTemplateCreator.IF_CONFIG] = fields[BoardTemplateCreator.IF_CONFIG].lower()
            self.networkData[n-1][BoardTemplateCreator.IF_IP] = fields[BoardTemplateCreator.IF_IP]
            self.networkData[n-1][BoardTemplateCreator.IF_NETMASK] = fields[BoardTemplateCreator.IF_NETMASK]
            self.networkData[n-1][BoardTemplateCreator.IF_GATEWAY] = fields[BoardTemplateCreator.IF_GATEWAY]
            self.networkData[n-1][BoardTemplateCreator.IF_DNS1] = fields[BoardTemplateCreator.IF_DNS1]
            self.networkData[n-1][BoardTemplateCreator.IF_DNS2] = fields[BoardTemplateCreator.IF_DNS2]
        elif code == Dialog.EXTRA:
            self.totalNetworkInterfaces = self.totalNetworkInterfaces - 1
            del self.networkData[n-1]
            
    def editInterface(self):
        while True:
            code = self.dialogInstance.msgbox(self.getNetworkDisplayString(), width=100, extra_button=True, extra_label="Edit Interface", title="Network Interface Details")
            if code == Dialog.EXTRA:
                (code, number) = self.dialogInstance.inputbox("Interface Number to Edit", init="",title="Edit")
                if self.rbfUtils.isSizeInt(number):
                    n = int(number)
                    if n <= self.totalNetworkInterfaces:
                        self.showEditInterfaceForm(n)
                    else:
                        self.dialogInstance.msgbox("Enter a valid integer\nYou have defined " + str(self.totalNetworkInterfaces) + " interface(s)", title="Error")
            else:
                break
    
    def showNetworkConf(self):
        while True:
            (code, tag) = self.dialogInstance.menu(
            "Network Configuration",
            width=60,
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
    
    def showSysConfig(self):
        """System Configuration"""
        while True:
            (code, tag) = self.dialogInstance.menu("System Configuration",width=60,height=20,
            choices=[("Hostname", self.hostName),
                     ("SELinux", self.selinuxConf),
                     ("Network Settings", "Enter Network Config Here"),
                     ("Done", "Exit System Configuration")])
            if code in (Dialog.CANCEL, Dialog.ESC) or tag == "Done":
                break
            elif tag == "Hostname":
                (code, tag) = self.dialogInstance.inputbox("Please enter a Hostname", init=self.hostName)
                if code == Dialog.OK:
                    self.hostName = tag
            elif tag == "SELinux":
                selinuxChoices = {'Enforcing': 'SELinux security policy is enforced','permissive': 'SELinux prints warnings instead of enforcing', 'Disabled': 'No SELinux policy is loaded.'}
                configChoices = []
                
                for selinux in selinuxChoices.keys():
                    if self.selinuxConf == selinux.lower():
                        s = (selinux, selinuxChoices[selinux], 1)
                    else:
                        s = (selinux, selinuxChoices[selinux], 0)
                    configChoices.append(s)
                    
                (code, tag) = self.dialogInstance.radiolist("Choose SELinux Config", width=65, choices=configChoices)
                if code == Dialog.OK:
                    self.selinuxConf = tag.lower()
            elif tag == "Network Settings":
                self.showNetworkConf()
    
    def showPackages(self):
        while True:
            (code, tag) = self.dialogInstance.menu("Packages Menu", width=60, height=20, menu_height=20,
            choices=[("Package Groups", self.groupPackageString),
                     ("Packages", self.packageString),
                     ("Done", "Exit Package Config")])
            if code in (Dialog.CANCEL,Dialog.ESC) or tag == "Done":
                break;
            if tag == "Package Groups":
                (code, self.groupPackageString) = self.dialogInstance.inputbox("Comma Separated List of Groups",title="Package Groups", init=self.groupPackageString)
            elif tag == "Packages":
                (code, self.packageString) = self.dialogInstance.inputbox("Comma Separated List of Packages", title="Packages", init=self.packageString)
                
    def writeTemplate(self):
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
        for i in [board,image,partitions,packages,stage1loader,uboot,rootfiles,firmware,kernel,config,etcoverlay,finalizescript,distro,repos,workdir,extlinuxconf]:
            root.appendChild(i)
        
        board.appendChild(doc.createTextNode(self.boardName))
        image.setAttribute("size", self.imageSize)
        image.setAttribute("type", "raw")
        image.setAttribute("path", self.imagePath)
        
        for i in range(0,len(self.imageData)):
            partition = doc.createElement("partition")
            partition.setAttribute("size", self.imageData[i][BoardTemplateCreator.SIZE])
            partition.setAttribute("type", self.imageData[i][BoardTemplateCreator.PTYPE].lower())
            partition.setAttribute("fs", self.imageData[i][BoardTemplateCreator.FS].lower())
            partition.setAttribute("mountpoint", self.imageData[i][BoardTemplateCreator.MOUNTPOINT])
            partitions.appendChild(partition)
        
        groupPackage = doc.createElement("group")
        groupPackage.appendChild(doc.createTextNode(self.groupPackageString))
        package = doc.createElement("package")
        package.appendChild(doc.createTextNode(self.packageString))
        packages.appendChild(groupPackage)
        packages.appendChild(package)
        
        stage1loader.appendChild(doc.createTextNode(self.stage1Loader))
        uboot.appendChild(doc.createTextNode(self.ubootPath))
        rootfiles.appendChild(doc.createTextNode(self.rootFiles))
        firmware.appendChild(doc.createTextNode(self.firmwarePath))
        
        kernel.setAttribute("type",self.kernelType)
        if self.kernelType == "custom":
            image = doc.createElement("image")            
            image.appendChild(doc.createTextNode(self.kernelPath))
            initrd = doc.createElement("initrd")
            initrd.appendChild(doc.createTextNode(self.initrdPath))
            modules = doc.createElement("modules")
            modules.appendChild(doc.createTextNode(self.modulesPath))
            dtb = doc.createElement("dtbdir")
            dtb.appendChild(doc.createTextNode(self.dtbPath))
            for i in [image,initrd,modules,dtb]:
                kernel.appendChild(i)
        
        hostname = doc.createElement("hostname")
        hostname.appendChild(doc.createTextNode(self.hostName))
        selinux = doc.createElement("selinux")
        selinux.appendChild(doc.createTextNode(self.selinuxConf))
        network = doc.createElement("network")
        
        for i in [hostname,selinux,network]:
            config.appendChild(i)
        
        for i in range(0,len(self.networkData)):
            interface = doc.createElement("interface")
            interface.setAttribute("name", self.networkData[i][BoardTemplateCreator.IF_NAME].lower())
            interface.setAttribute("config", self.networkData[i][BoardTemplateCreator.IF_CONFIG].lower())
            network.appendChild(interface)
            if self.networkData[i][BoardTemplateCreator.IF_CONFIG] == "static":
                ipaddress = doc.createElement("ipaddress")
                ipaddress.appendChild(doc.createTextNode(self.networkData[i][BoardTemplateCreator.IF_IP]))
                subnetmask = doc.createElement("subnetmask")
                subnetmask.appendChild(doc.createTextNode(self.networkData[i][BoardTemplateCreator.IF_NETMASK]))
                gateway = doc.createElement("gateway")
                gateway.appendChild(doc.createTextNode(self.networkData[i][BoardTemplateCreator.IF_GATEWAY]))
                nameserver = doc.createElement("nameserver")
                nameserver.appendChild(doc.createTextNode(self.networkData[i][BoardTemplateCreator.IF_DNS1]))
                for j in [ipaddress,subnetmask,gateway,nameserver]:
                    interface.appendChild(j)
        
        etcoverlay.appendChild(doc.createTextNode(self.etcOverlay))
        finalizescript.appendChild(doc.createTextNode(self.finalizeScript))
        distro.appendChild(doc.createTextNode(self.linuxDistro))
        
        for i in range(0,len(self.repoData)):
            repo = doc.createElement("repo")
            repos.appendChild(repo)
            repo.setAttribute("name",self.repoData[i][BoardTemplateCreator.REPO_NAME])
            repo.setAttribute("path",self.repoData[i][BoardTemplateCreator.REPO_URL])
        
        workdir.appendChild(doc.createTextNode(self.workDir))
        extlinuxconf.appendChild(doc.createTextNode(self.extlinuxConf))
        
        (code , dirpath) = self.dialogInstance.dselect(self.lastKnownPath,10,50,title="Select Directory to Save Template")
        if code == Dialog.OK:
            (code, filename) = self.dialogInstance.inputbox("XML Template Filename")
            if code == Dialog.OK:
                try:
                    self.generatedXmlPath = dirpath + os.sep + filename
                    fileWriter = open(self.generatedXmlPath,"w")
                    fileWriter.write(doc.toprettyxml())
                    fileWriter.close()
                    self.dialogInstance.msgbox("Saved Template to " + self.generatedXmlPath, width=80, title="Save Template")
                except:
                    self.generatedXmlPath = ""
                    self.dialogInstance.msgbox("Error Saving Template",title="Error")
   
    def generateImage(self):
        if self.getFilename(self.generatedXmlPath) == "":
            self.dialogInstance.msgbox("No XML Generated Yet. Please select 'Save Template' first")
            return
        if not os.path.exists(self.generatedXmlPath):
            self.dialogInstance.msgbox(self.generatedXmlPath + "does not exist")
            return
        code = self.dialogInstance.msgbox("To Generate Image " + self.imagePath + " using " + self.generatedXmlPath +" Please run\n\n./rbf.py build " + self.generatedXmlPath, width=80, title="Generate Command")
            
    def getFilename(self,filepath):
        if not "/" in filepath:
            return filepath
        return filepath[filepath.rfind("/")+1:]
    
    def mainMenu(self):
        """Displays Main RootFS Build Factory Menu"""
        while True:
            (code, tag) = self.dialogInstance.menu("Main Menu",width=60, height=20, menu_height=20,
            choices=[("Load Template", self.xmlTemplate[self.xmlTemplate.rfind("/")+1:]),
                     ("Board Info", "Selected Board: " + self.boardName),
                     ("Image Path", "Image: " + self.imagePath + " " + self.imageSize),
                     ("Partitions", "Define Partition Layout"),
                     ("Bootloader", "Bootloader Options"),
                     ("Kernel", "Kernel Config"),
                     ("Repositories", "Enter Repo Config"),
                     ("Packages", "Packages to Install"),
                     ("Misc", "Misc Settings"),
                     ("System Config", "System Settings"),
                     ("Save Template", "Filename: " + self.getFilename(self.generatedXmlPath)),
                     ("Generate Image", "Using Template: " + self.getFilename(self.generatedXmlPath)),
                     ("Exit", "Exit Board Template Writer")])
            
            if code in (Dialog.CANCEL, Dialog.ESC) or tag == "Exit":
                break;
            elif tag == "Load Template":
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
            elif tag == "Save Template":
                self.writeTemplate();
            elif tag == "Generate Image":
                self.generateImage();

                

if __name__ == "__main__":
    if os.getuid() != 0:
        print("You need to be root to use RootFS Build Factory")
        sys.exit(1)
        
    d = BoardTemplateCreator()
    d.mainMenu()

