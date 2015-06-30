#!/usr/bin/python
import os
import sys
import subprocess
from rbfutils import RbfUtils

class BoardInstaller():
    BOARDS_DIR="boards.d"
    SPECIAL_BOARDS=['odroidc1','rpi2']    
    MLO_BOARDS=['beaglebone','pandaboard']
    NOT_ROOT,SHOW_HELP, NOT_FILE, NO_WRITE_PERMISSION, NO_BOARDS, NO_FILES = range(0,6)
    def __init__(self, imagePath, devicePath):
        """In case of SPECIAL_BOARDS: Writes RBF Generated Image to microSD"""
        """In case of Other Boards: Writes Generic/QEMU image to microSD and then Board Specific U-Boot to microSD"""
        self.imagePath = imagePath
        self.devicePath = devicePath
        self.supportedBoards = {}
        self.boardCount = 0
        self.stage1Loader = "none"
        self.ubootPath = "none"
        self.rbfUtils = RbfUtils()
        try:
            for board in sorted(os.listdir(BoardInstaller.BOARDS_DIR)):
                if board in ("finalize.sh","qemu.sh"):
                    continue
                board = board[:-3]
                self.boardCount = self.boardCount + 1
                self.supportedBoards[self.boardCount] = board
        except:
            print("Could not find " + BoardInstaller.BOARDS_DIR)
            sys.exit(BoardInstaller.NO_BOARDS)

    def chooseBoard(self):
        """Choose from Supported Boards"""
        print("Select Board:")
        for b in self.supportedBoards.keys():
            print("\t" + str(b) + ": " + self.supportedBoards[b].title())
        while True:
            x = raw_input("Which Board? ")
            if self.rbfUtils.isSizeInt(x):
                boardIndex = int(x)
                if boardIndex <= self.boardCount:
                    return boardIndex
            else:
                print("Invalid Input")
    
    def findUboot(self,boardName):
        """Find u-boot for specified board"""
        path = "files/"+boardName+"/"
        try:
            for u in os.listdir(path):
                if u.startswith("u-boot"):
                    return path+u
            return "none"
        except:
            print("Could not find board files")
            sys.exit(BoardInstaller.NO_FILES)
            
    def createScript(self, boardIndex):
        """Create rbfinstaller.sh"""
        self.rbfInstaller = open("rbfinstaller.sh","w")
        self.rbfInstaller.write("dd if=\"" + self.imagePath + "\" of=" + self.devicePath + " bs=1M\n")
        boardName = self.supportedBoards[boardIndex]
        print("Writing U-Boot for " + boardName)
        if boardName in BoardInstaller.SPECIAL_BOARDS:
            print("For " + boardName + ", can only write image " + self.getFilename(self.imagePath) + " to microSD. Cannot run board script.")
        elif boardName in BoardInstaller.MLO_BOARDS:
            print("Will also install MLO to device " + self.devicePath)
            self.stage1Loader = "files/" + boardName + "/MLO"            
            self.ubootPath = self.findUboot(boardName)
            if self.ubootPath != "none":
                self.rbfInstaller.write("boards.d/" + boardName + ".sh " + self.devicePath + " " + self.stage1Loader + " " + self.ubootPath + "\n")
        else:
            self.stage1Loader = "none"
            self.ubootPath = self.findUboot(boardName)
            if self.ubootPath != "none":
                self.rbfInstaller.write("boards.d/" + boardName + ".sh " + self.devicePath + " " + self.stage1Loader + " " + self.ubootPath + "\n")
        self.rbfInstaller.write("sync\n")
        self.rbfInstaller.close()
            
    def getDeviceName(self):
        blockDevice = self.devicePath[self.devicePath.rfind("/")+1:]
        blockDeviceVendor = "none"
        blockDeviceModel = "none"
        
        try:
            blockDeviceFile = open("/sys/class/block/" + blockDevice + "/device/model","r")
            blockDeviceModel = blockDeviceFile.readlines()[0].strip()
            blockDeviceFile.close()
            blockDeviceFile = open("/sys/class/block/" + blockDevice + "/device/vendor","r")
            blockDeviceVendor = blockDeviceFile.readlines()[0].strip()
            blockDeviceFile.close()
            return "[" + blockDeviceVendor + " " + blockDeviceModel + "]"
        except:
            return ""
            
    def getFilename(self, filePath):
        if "/" not in filePath:
            return filePath
        else:
            return filePath[filePath.rfind("/")+1:]
            
if ( __name__ == "__main__"):
    if os.getuid() != 0:
        print("You need to be root to use RootFS Build Factory")
        sys.exit(BoardInstaller.NOT_ROOT)

    if len(sys.argv) != 3:
        print("Usage: ./rbfinstaller.py <imagePath> <device>")
        sys.exit(BoardInstaller.SHOW_HELP)
        
    imagePath = sys.argv[1]
    devicePath = sys.argv[2]
    if not os.path.isfile(imagePath):
        print(imagePath + " is not a file")
        sys.exit(BoardInstaller.NOT_FILE)
    if not os.access(devicePath,os.W_OK):
        print("No Write Permission to " + devicePath)
        sys.exit(BoardInstaller.NO_WRITE_PERMISSION)
        
    bi = BoardInstaller(imagePath, devicePath)
    boardIndex = bi.chooseBoard()
    bi.createScript(boardIndex)
    deviceName = bi.getDeviceName()
    answer = raw_input("Write " + bi.getFilename(imagePath) + " to " + devicePath + " " + deviceName + "?(yes/no): ")
    if answer == "yes":
        print("Writing " + bi.getFilename(imagePath) + " to " + devicePath + " " + deviceName + "...")
        installerRet = subprocess.call(['/usr/bin/bash','rbfinstaller.sh'])
    else:
        print("Exiting")
    sys.exit(0)
    
