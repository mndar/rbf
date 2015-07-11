#!/usr/bin/python
# pylint: disable=

"""@package rbfutilstest
Tests for RBF Utilities
"""

import os
import sys
import unittest
sys.path.append("..")
import rbfutils

class RbfUtilsTest(unittest.TestCase):
    """Tests for RBF Dialog Interface"""
    def setUp(self):
        self.utils = rbfutils.RbfUtils()

    def tearDown(self):
        del self.utils

    def test_calcParitionEndSector(self):
        """Tests calcParitionEndSector function"""
        self.assertEqual(\
            self.utils.calcParitionEndSector("2048", "500M"), "1026047")

    def test_calcParitionEndSize(self):
        """Tests calcParitionEndSize function"""
        self.assertEqual(self.utils.calcParitionEndSize("1M", "500M"), "501M")

    def test_getImageSizeInM(self):
        """Tests getImageSizeInM function"""
        self.assertEqual(self.utils.getImageSizeInM("1G"), "1024M")
        self.assertEqual(self.utils.getImageSizeInM("500M"), "500M")

    def test_isSizeInt(self):
        """Tests isSizeInt Function"""
        self.assertTrue(self.utils.isSizeInt("1"))
        self.assertFalse(self.utils.isSizeInt("1.1"))

if __name__ == '__main__':
    if os.getuid() != 0:
        print("You need to be root to use RootFS Build Factory")
        sys.exit(1)
    unittest.main(verbosity=2, buffer=True, exit=False)

