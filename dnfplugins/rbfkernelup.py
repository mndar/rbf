#!/usr/bin/python
"""@package rbfkernelup plugin
Configure system on kernel updates
"""
import os
import subprocess
from xml.dom.minidom import parse
from xml.parsers.expat import ExpatError
import dnf
from dnfpluginscore import logger

def getRootPathFromProc():
    """Gets root param from /proc/cmdline"""
    cmdlineFile = open("/proc/cmdline")
    cmdlineText = cmdlineFile.readlines()[0].strip()
    cmdlineFile.close()

    cmdlineElements = cmdlineText.split(" ")
    for element in cmdlineElements:
        if element.startswith("root="):
            return element[5:]
    return None

def getBoardDetailsFromTemplate():
    """Gets Board Name From /etc/rbf/board.xml"""
    try:
        boardDom = parse("/etc/rbf/board.xml")
        boardName = boardDom.getElementsByTagName("board")[0].firstChild.data
        linuxDistro = boardDom.getElementsByTagName("distro")[0].firstChild.data
        return (boardName, linuxDistro)
    except (ExpatError, IndexError):
        logger.error("Bad Board Template")
        return ("generic", "Linux")

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
        logger.error("Commands Not Found: " + notFoundString)

    if len(notExecList) != 0:
        notExecString = ""
        for command in notExecList:
            notExecString = notExecString + command + ", "

        notExecString = notExecString[0:-2]
        logger.error("Commands Not Executable: " + notExecString)

    if len(notFoundList) == 0 and len(notExecList) == 0:
        return True
    else:
        return False

class RbfKernelUp(dnf.Plugin):
    """RbfKernelUp Class"""
    name = "rbfkernel up"

    def __init__(self, base, cli):
        self.base = base

    def transaction(self):
        """Post Transaction Hook"""
        for item in self.base.transaction:
            installedPacks = item.installs()
            for pack in installedPacks:
                logger.info("Installed: " + pack.name + \
                            " Version: " + pack.version + \
                            " Release: " + pack.release + \
                            " Arch: " + pack.arch)
                if pack.name.startswith("kernel-core"):
                    #get board details
                    (boardName, linuxDistro) = getBoardDetailsFromTemplate()
                    kernelUpScript = "rbf" + boardName + ".sh"

                    if not checkCommandExistsAccess([kernelUpScript]):
                        logger.error("Please fix boot configuration manually")
                        return

                    #determine distro name
                    try:
                        redhatReleaseFile = open("/etc/redhat-release", "r")
                        redhatRelease = redhatReleaseFile.readlines()[0].strip()
                        redhatReleaseFile.close()
                    except IOError:
                        redhatRelease = linuxDistro

                    #determine new kernel version
                    kernelString = pack.version + "-" + pack.release + "." + \
                                   pack.arch

                    #determine root path
                    rootPath = getRootPathFromProc()
                    if rootPath == None:
                        logger.error("Could not find path to / in " + \
                                     "/proc/cmdline. Please fix boot " + \
                                     "configuration manually")
                        return

                    logger.info("Executing kernelup script for " + boardName)
                    kernelupRet = subprocess.call([kernelUpScript,\
                                  redhatRelease, kernelString, rootPath])
                    if kernelupRet != 0:
                        logger.error("Error Execuing Kernel Up Script for " + \
                                     boardName)


