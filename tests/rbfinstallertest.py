#!/usr/bin/python
# pylint: disable=

"""@package rbfdialogtest
Tests for RBF Installer
"""

import os
import sys
import unittest
sys.path.append("..")
import rbfinstaller

class RbfInstallerTest(unittest.TestCase):
    """Tests RBF Installer"""
    def setUp(self):
        self.installer = rbfinstaller.BoardInstaller("someimage.img", \
                                                     "/dev/sdX")

    def tearDown(self):
        del self.installer

    def test_loadBoards(self):
        """Tests loadBoards function"""
        # invalid boards.d
        self.assertEqual(self.installer.loadBoards(), \
                         rbfinstaller.BoardInstaller.NO_BOARDS)

    def test_findUboot(self):
        """Tests findUboot function"""
        self.assertEqual(self.installer.findUboot("someboard"), "none")

    def test_getDeviceName(self):
        """Tests getDeviceName function"""
        self.assertEqual(self.installer.getDeviceName(), "")

    def test_getFilename(self):
        """Tests getFilename function"""
        self.assertEqual(self.installer.getFilename("test"), "test")
        self.assertEqual(self.installer.getFilename("/path/to/filename"), \
                         "filename")

if __name__ == '__main__':
    if os.getuid() != 0:
        print("You need to be root to use RootFS Build Factory")
        sys.exit(1)
    unittest.main(verbosity=2, buffer=True, exit=False)

