#!/usr/bin/python
"""@package utils
Utility Functions for RootFS Build Factory
"""
class RbfUtils(object):
    """RBF Utilities"""
    PARTITION_BEGIN = "2048"
    LOGICAL_PARTITION_START_INDEX = 5
    #PARTITION_BEGIN = "1M"
    SECTOR_SIZE = "512"
    def __init__(self):
        """RootFS Build Factory Utils"""

    def calcParitionEndSector(self, begin, size):
        """Calculates End Sector when provided with Begin Sector"""
        size = self.getImageSizeInM(size)
        size = size[0:len(size)-1]
        endSector = int(begin) + int(size)*1024*1024/int(self.SECTOR_SIZE) -1
        return str(endSector)

    def calcParitionEndSize(self, begin, size):
        """Calculates End Size when provided with Begin Size"""
        size = self.getImageSizeInM(size)
        endSize = int(begin[0:-1]) + int(size[0:-1])
        return str(endSize)+"M"

    @classmethod
    def getImageSizeInM(cls, imageSize):
        """Converts Size in G to M"""
        if imageSize[-1] == "G":
            imageSize = str(int(imageSize[0:-1])*1024) + "M"
        return imageSize

    @classmethod
    def isSizeInt(cls, size):
        """Tests if size is an integer"""
        try:
            int(size)
            return True
        except ValueError:
            return False

