#!/usr/bin/python
"""@package extlinuxconf plugin
Configure /boot/extlinux/extlinux.conf on kernel updates
"""
import os
import subprocess
from xml.dom.minidom import parse
from xml.parsers.expat import ExpatError
from yum.plugins import TYPE_CORE

requires_api_version = '2.5'
plugin_type = TYPE_CORE

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
        print("Bad Board Template")
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
        print("Commands Not Found: " + notFoundString)

    if len(notExecList) != 0:
        notExecString = ""
        for command in notExecList:
            notExecString = notExecString + command + ", "

        notExecString = notExecString[0:-2]
        print("Commands Not Executable: " + notExecString)

    if len(notFoundList) == 0 and len(notExecList) == 0:
        return True
    else:
        return False

def posttrans_hook(conduit):
    """Post Transaction Hook"""
    tsInfo = conduit.getTsInfo()
    for txmbr in tsInfo:
        packageName = txmbr.po.name
        packageState = txmbr.ts_state
        packageVer = txmbr.po.version
        packageRelease = txmbr.po.release
        packageArch = txmbr.po.arch
        conduit.info(2, packageName + " " + packageState + " " + packageVer + \
                        " " + packageRelease + " " + packageArch)
        if (packageState == "i" or packageState == "u") and \
            packageName.startswith("kernel-core"):
            #get board details
            (boardName, linuxDistro) = getBoardDetailsFromTemplate()
            kernelUpScript = "rbf" + boardName + ".sh"

            if not checkCommandExistsAccess([kernelUpScript]):
                conduit.info(2, "Please fix boot configuration manually")
                return

            #determine distro name
            try:
                redhatReleaseFile = open("/etc/redhat-release", "r")
                redhatRelease = redhatReleaseFile.readlines()[0].strip()
                redhatReleaseFile.close()
            except IOError:
                redhatRelease = linuxDistro

            #determine new kernel version
            kernelString = packageVer + "-" + packageRelease + "." + packageArch

            #determine root path
            rootPath = getRootPathFromProc()
            if rootPath == None:
                conduit.info(2, "Could not find path to / in /proc/cmdline." \
                             + "Please fix boot configuration manually")
                return

            conduit.info(2, "Executing kernelup script for " + boardName)
            kernelupRet = subprocess.call([kernelUpScript,\
                          redhatRelease, kernelString, rootPath])
            if kernelupRet != 0:
                conduit.info(2, "Error Execuing Kernel Up Script for " + \
                             boardName)


