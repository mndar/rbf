#!/usr/bin/python2
# pylint: disable=

"""@ package changeuuid
Changes UUIDs of all partitions

Changes UUIDs of all partitions
"""

import os
import subprocess
import sys
import logging
import uuid
import time

def printUsage():
    """Prints Usage"""
    logging.info("./changeuuid.py <change|pretend> <device> <mountpoint>")

def initLogging():
    """Initialize Logging"""
    logFormatter = logging.Formatter("[%(levelname)-5.5s]  %(message)s")
    rootLogger = logging.getLogger()
    rootLogger.setLevel(logging.INFO)

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


class ChangeUuid(object):
    """Changes UUIDs of all parititons in the image file"""
    PARTITION, LABEL, UUID, FSTYPE, NEW_UUID = range(0,5)
    NOT_ROOT, INCORRECT_ARGUMENTS, COMMANDS_NOT_FOUND, NO_ROOT_PARTITION, \
    NO_LABEL_UUID, NO_MOUNTPOINT = range(100,106)
    
    def __init__(self, action, dev, mount, files):
        """Constructor for Change UUID Script"""
        self.deviceName = dev
        self.mountPoint = mount
        self.partitionData = []
        self.processFiles = files
        if action == "pretend":
            self.action = "pretend"
        elif action == "change":
            self.action = "change"
        else:
            logging.error("Incorrect action")
            sys.exit(1)
            
    def findPartitions(self):
        """Find all partitions in image and store them in a list"""
        self.partitions = []
        deviceName = self.deviceName[self.deviceName.rfind('/')+1:]
        for i in reversed(os.listdir("/dev")):
            if i.startswith(deviceName) and i != deviceName:
                self.partitions.append("/dev/"+i)
        logging.info(self.partitions)

    def findPartitionWithFile(self, filePath):
        """Finds partition with given filePath and mounts it"""
        for i in range(0,len(self.partitionData)):
            if self.partitionData[i][ChangeUuid.FSTYPE] == "swap":
                continue
            ret = subprocess.call(["mount", "-o", "rw", \
                               self.partitionData[i][ChangeUuid.PARTITION],\
                               self.mountPoint])
            if ret != 0:
                logging.error("Couldn't mount partition " + \
                              self.partitionData[i][ChangeUuid.PARTITION])
                sys.exit(1)
            if os.path.exists(self.mountPoint + filePath):
                logging.info("Mounting " +\
                             self.partitionData[i][ChangeUuid.PARTITION] +\
                             " " + self.mountPoint)
                return True                    
            else:
                logging.info("Unmounting " +\
                             self.partitionData[i][ChangeUuid.PARTITION] +\
                             " " + self.mountPoint)
                time.sleep(2)
                ret = subprocess.call(["umount", self.mountPoint])
                if ret != 0:
                    logging.error("Couldn't unmount mountpoint " + \
                                   self.mountPoint)
                    sys.exit(1)
        return False

    def processFile(self, filePath):
        """Reads the entire file, performs search and replace. Writes it Back"""
        logging.info("Processing File: " + self.mountPoint + filePath)
        fileHandle = open(self.mountPoint + filePath, "r") 
        fileString = fileHandle.read()
        fileHandle.close()
        print("**** Old " + filePath + " ****\n" + fileString)
        for i in range(0,len(self.partitionData)):
            if self.partitionData[i][ChangeUuid.FSTYPE] == "vfat":
                fileString = fileString.replace(\
                         self.partitionData[i][ChangeUuid.LABEL],\
                         self.partitionData[i][ChangeUuid.NEW_UUID].upper()[:8])
            else:
                fileString = fileString.replace(\
                          self.partitionData[i][ChangeUuid.UUID],\
                          self.partitionData[i][ChangeUuid.NEW_UUID])
        print("**** New " + filePath + " ****\n" + fileString)
        time.sleep(2)
        if self.action == "pretend":
            ret = subprocess.call(["umount", self.mountPoint])
            if ret != 0:
                logging.error("Couldn't unmount mountpoint " + self.mountPoint)
                sys.exit(1)
            return
        logging.info("Writing " + self.mountPoint + filePath)
        fileHandle = open(self.mountPoint + filePath, "w") 
        fileHandle.write(fileString)
        fileHandle.close()
        logging.info("Unmounting " + self.mountPoint)
        ret = subprocess.call(["umount", self.mountPoint])
        if ret != 0:
            logging.error("Couldn't unmount mountpoint " + self.mountPoint)
            sys.exit(1)
            
    def createNewFiles(self):
        """Finds partition with a given file present.
           Exits on first such partition and the processes the file"""
        logging.info("Unmounting all partitions on " + self.deviceName)
        for i in range(0,len(self.partitionData)):
            subprocess.call(['umount', \
                                   self.partitionData[i][ChangeUuid.PARTITION]])
            
        for filePath in self.processFiles:
            if (self.findPartitionWithFile(filePath)):
                self.processFile(filePath)
        
   
    @classmethod
    def getValue(cls, blkidString, fieldName):
        """Extracts value of fieldName from blkidString"""
        try:
            fieldName = " " + fieldName
            pos1 = blkidString.index(fieldName) + len(fieldName) + 1
            pos2 = blkidString.index("\"", pos1+1)
            return blkidString[pos1+1:pos2]
        except ValueError:
            return ""

    def processUuid(self):
        """Change Labels/Uuids of all partitions"""
        for i in range(0,len(self.partitionData)):
            logging.info("Changing UUID/LABEL for " + \
                self.partitionData[i][ChangeUuid.PARTITION])
            if self.partitionData[i][ChangeUuid.FSTYPE] == "vfat":
                logging.info("Old:" + \
                    self.partitionData[i][ChangeUuid.LABEL] + " New:" + \
                    self.partitionData[i][ChangeUuid.NEW_UUID].upper()[:8])
                if self.action == "pretend":
                    continue
                ret = subprocess.call(["dosfslabel", \
                    self.partitionData[i][ChangeUuid.PARTITION], \
                    self.partitionData[i][ChangeUuid.NEW_UUID].upper()[:8]])
                if ret != 0:
                    logging.error("Couldn't change partition LABEL")
                    sys.exit(1)
            elif self.partitionData[i][ChangeUuid.FSTYPE] == "swap":
                logging.info("Old:" + \
                    self.partitionData[i][ChangeUuid.UUID] + " New:" + \
                    self.partitionData[i][ChangeUuid.NEW_UUID])
                if self.action == "pretend":
                    continue
                ret = subprocess.call(["mkswap", "-U", \
                    self.partitionData[i][ChangeUuid.NEW_UUID], \
                    self.partitionData[i][ChangeUuid.PARTITION]])
                if ret != 0:
                    logging.error("Couldn't create swap partition UUID")
                    sys.exit(1)
            elif self.partitionData[i][ChangeUuid.FSTYPE].startswith("ext"):
                logging.info("Old:" + \
                    self.partitionData[i][ChangeUuid.UUID] + " New:" + \
                    self.partitionData[i][ChangeUuid.NEW_UUID])
                if self.action == "pretend":
                    continue
                ret = subprocess.call(["tune2fs", "-U", \
                    self.partitionData[i][ChangeUuid.NEW_UUID], \
                    self.partitionData[i][ChangeUuid.PARTITION]])
                if ret != 0:
                    logging.error("Couldn't change partition UUID")
                    sys.exit(1)
            else:
                logging.error("Cannot change UUID for " + \
                    self.partitionData[i][ChangeUuid.PARTITION] + \
                    " with filesystem " + \
                    self.partitionData[i][ChangeUuid.FSTYPE])
            
    def buildLabelUuidList(self):
        """Runs blkid on all partitions and build a list of old and new UUIDs"""
        for partition in self.partitions:
            blkidString = subprocess.check_output(['blkid', partition]).strip()
            uuidValue = self.getValue(blkidString, "UUID")
            fstypeValue = self.getValue(blkidString, "TYPE")
            labelValue = self.getValue(blkidString, "LABEL")
            newUuidValue = str(uuid.uuid4())
            if fstypeValue == "vfat":
                logging.info(partition + " " + fstypeValue + " " + uuidValue + \
                            " " + newUuidValue.upper()[:8])
            else:
                logging.info(partition + " " + fstypeValue + " " + uuidValue + \
                            " " + newUuidValue)
            if fstypeValue.startswith("ext") or fstypeValue in ['vfat', 'swap']:
                self.partitionData.append([partition, labelValue, uuidValue, \
                                             fstypeValue, newUuidValue])
            else:
                logging.error("Cannot presently handle filesystem " + \
                              fstypeValue + " on " + partition)
        
if __name__ == "__main__":
    initLogging()
    if os.getuid() != 0:
        logging.error("You need to be root to use RootFS Build Factory")
        sys.exit(ChangeUuid.NOT_ROOT)
        
    if len(sys.argv) != 4:
        printUsage()
        sys.exit(ChangeUuid.INCORRECT_ARGUMENTS)
    
    if not os.path.isdir(sys.argv[3]):
        logging.error("Mountpoint " + sys.argv[3] + " doesn't exist")
        sys.exit(ChangeUuid.NO_MOUNTPOINT)

    if not checkCommandExistsAccess(['losetup', 'mount', 'umount', \
                                    'dosfslabel', 'blkid']):
        logging.error("Cannot Continue")
        sys.exit(ChangeUuid.COMMANDS_NOT_FOUND)
    
    uuidRegenerator = ChangeUuid(sys.argv[1], sys.argv[2], sys.argv[3], \
                        ["/etc/fstab", "/extlinux/extlinux.conf", "/boot.ini"])
    uuidRegenerator.findPartitions()
    uuidRegenerator.buildLabelUuidList()
    uuidRegenerator.createNewFiles()
    uuidRegenerator.processUuid()
    sys.exit(0)

