#!/usr/bin/python
# pylint: disable=

"""@package rbftest
Tests for RootFS Build Factory
"""

import unittest
import os
import sys
sys.path.append("..")
import rbf

class RbfTest(unittest.TestCase):
    """Tests for RootFS Build Factory"""
    def setUp(self):
        self.parser = rbf.BoardTemplateParser("parse", "test_templates/bad.xml")

    def tearDown(self):
        del self.parser

    def test_checkCommandExistsAccess(self):
        """Tests checkCommandExistsAccess function"""
        #check if 'ls' is found in PATH
        self.assertTrue(rbf.checkCommandExistsAccess(['ls']))
        #check if 'abcd' if found in PATH
        self.assertFalse(rbf.checkCommandExistsAccess(['abcd']))

    def test_parseTemplate(self):
        """Tests parseTemplate function"""
        #bad xml template
        self.parser.setTemplate("test_templates/bad.xml")
        self.assertEqual(self.parser.parseTemplate(), \
                         rbf.BoardTemplateParser.ERROR_PARSING_XML)

        #xml template with missing tags
        self.parser.setTemplate("test_templates/incomplete.xml")
        self.assertEqual(self.parser.parseTemplate(), \
                         rbf.BoardTemplateParser.ERROR_PARSING_XML_TAGS)

        #good xml template
        self.parser.setTemplate("test_templates/good.xml")
        self.assertEqual(self.parser.parseTemplate(), 0)

    def test_createImage(self):
        """tests createImage function"""
        #image size without suffix
        self.parser.setTemplate("test_templates/bad_image_size.xml")
        self.assertEqual(self.parser.parseTemplate(), 0)
        self.assertEqual(self.parser.createImage(), \
                         rbf.BoardTemplateParser.ERROR_IMAGE_SIZE)

        #image tag incomplete. no size specified
        self.parser.setTemplate("test_templates/bad_image_tag.xml")
        self.assertEqual(self.parser.parseTemplate(), 0)
        self.assertEqual(self.parser.createImage(), \
                         rbf.BoardTemplateParser.ERROR_IMAGE_FILE)

        #image tag ok but image already exists
        self.parser.setTemplate("test_templates/image_exists.xml")
        self.assertEqual(self.parser.parseTemplate(), 0)
        testImage = open("test.img", "w")
        testImage.close()
        self.assertEqual(self.parser.createImage(), \
                         rbf.BoardTemplateParser.IMAGE_EXISTS)
        os.remove("test.img")

        #good xml template
        self.parser.setTemplate("test_templates/good.xml")
        self.assertEqual(self.parser.parseTemplate(), 0)
        self.assertEqual(self.parser.createImage(), 0)

    def test_createPartitions(self):
        """Test createPartitions function"""
        #no partitions specified
        self.parser.setTemplate("test_templates/no_partitions.xml")
        self.assertEqual(self.parser.parseTemplate(), 0)
        self.assertEqual(self.parser.createImage(), 0)
        self.assertEqual(self.parser.createPartitions(), \
                         rbf.BoardTemplateParser.NO_PARTITIONS_FOUND)

        #primary partition sizes exceed image size
        self.parser.setTemplate("test_templates/primary_partitions_exceed.xml")
        self.assertEqual(self.parser.parseTemplate(), 0)
        self.assertEqual(self.parser.createImage(), 0)
        self.assertEqual(self.parser.createPartitions(), \
                         rbf.BoardTemplateParser.PRIMARY_PARTITION_SIZES_ERROR)

        #logical partition sizes exceed extended partition size
        self.parser.setTemplate("test_templates/logical_partitions_exceed.xml")
        self.assertEqual(self.parser.parseTemplate(), 0)
        self.assertEqual(self.parser.createImage(), 0)
        self.assertEqual(self.parser.createPartitions(), \
                         rbf.BoardTemplateParser.LOGICAL_PARTITION_SIZES_ERROR)

        #incorrect template. has 2 extended partitions
        self.parser.setTemplate("test_templates/two_extended.xml")
        self.assertEqual(self.parser.parseTemplate(), 0)
        self.assertEqual(self.parser.createImage(), 0)
        self.assertEqual(self.parser.createPartitions(), \
                        rbf.BoardTemplateParser.INVALID_PARTITION_DATA)

        #trying to create logical partition before extended
        self.parser.setTemplate("test_templates/logical_before_extended.xml")
        self.assertEqual(self.parser.parseTemplate(), 0)
        self.assertEqual(self.parser.createImage(), 0)
        self.assertEqual(self.parser.createPartitions(), \
                         rbf.BoardTemplateParser.LOGICAL_PART_ERROR)

        #total primary partitions > 4
        self.parser.setTemplate("test_templates/five_primary_partitions.xml")
        self.assertEqual(self.parser.parseTemplate(), 0)
        self.assertEqual(self.parser.createImage(), 0)
        self.assertEqual(self.parser.createPartitions(), \
                         rbf.BoardTemplateParser.TOTAL_PARTITIONS_ERROR)

        #good xml template
        self.parser.setTemplate("test_templates/good.xml")
        self.assertEqual(self.parser.parseTemplate(), 0)
        self.assertEqual(self.parser.createImage(), 0)
        self.assertEqual(self.parser.createPartitions(), 0)

    def test_writeRepos(self):
        """Test writeRepos function"""
        #no repo information
        self.parser.setTemplate("test_templates/no_repos.xml")
        self.assertEqual(self.parser.parseTemplate(), 0)
        self.assertEqual(self.parser.writeRepos(), \
                         rbf.BoardTemplateParser.NO_REPOSITORY)

        #incorrect repo information
        self.parser.setTemplate("test_templates/incorrect_repo.xml")
        self.assertEqual(self.parser.parseTemplate(), 0)
        self.assertEqual(self.parser.writeRepos(), \
                         rbf.BoardTemplateParser.INCORRECT_REPOSITORY)

        #good xml template
        self.parser.setTemplate("test_templates/good.xml")
        self.assertEqual(self.parser.parseTemplate(), 0)
        self.assertEqual(self.parser.writeRepos(), 0)

    def test_installPackages(self):
        """Tests installPackages function"""
        #no packages specified
        self.parser.setTemplate("test_templates/no_packages.xml")
        self.assertEqual(self.parser.parseTemplate(), 0)
        self.assertEqual(self.parser.installPackages(), \
                         rbf.BoardTemplateParser.NO_PACKAGES)

        #good xml template
        self.parser.setTemplate("test_templates/good.xml")
        self.assertEqual(self.parser.parseTemplate(), 0)
        self.assertEqual(self.parser.installPackages(), 0)

    def test_generatePackageString(self):
        """Tests generatePackageString function"""
        self.assertEqual(self.parser.generatePackageString(\
                                ['package1', 'package2']), "package2 package1 ")

    def test_installKernel(self):
        """Tests installKernel function"""
        #missing u-boot
        self.parser.setTemplate("test_templates/bad_uboot.xml")
        self.assertEqual(self.parser.parseTemplate(), 0)
        self.assertEqual(self.parser.installKernel(), \
                         rbf.BoardTemplateParser.NO_UBOOT)

        #no kernel type specified
        self.parser.setTemplate("test_templates/no_kernel_type.xml")
        self.assertEqual(self.parser.parseTemplate(), 0)
        self.assertEqual(self.parser.installKernel(), \
                         rbf.BoardTemplateParser.NO_KERNEL_TYPE)

        #missing firmware
        self.parser.setTemplate("test_templates/bad_firmware.xml")
        self.assertEqual(self.parser.parseTemplate(), 0)
        self.assertEqual(self.parser.installKernel(), \
                         rbf.BoardTemplateParser.NO_FIRMWARE_FOUND)

        #good xml template. no firmware (none)
        self.parser.setTemplate("test_templates/firmware_none.xml")
        self.assertEqual(self.parser.parseTemplate(), 0)
        self.assertEqual(self.parser.installKernel(), 0)


    def test_finalActions(self):
        """Tests finalActions function"""
        #missing ssh key
        self.parser.setTemplate("test_templates/bad_ssh_key.xml")
        self.assertEqual(self.parser.parseTemplate(), 0)
        self.parser.etcOverlay = "."
        self.assertEqual(self.parser.finalActions(), \
                         rbf.BoardTemplateParser.SSH_KEY_NOT_FOUND)

    def test_makeBootable(self):
        """Tests makeBootable function"""
        #bad etc overlay
        self.parser.setTemplate("test_templates/bad_etc_overlay.xml")
        self.assertEqual(self.parser.parseTemplate(), 0)
        self.assertEqual(self.parser.makeBootable(), \
                         rbf.BoardTemplateParser.NO_ETC_OVERLAY)

        #good xml template
        self.parser.setTemplate("test_templates/etc_overlay.xml")
        self.assertEqual(self.parser.parseTemplate(), 0)
        self.assertEqual(self.parser.makeBootable(), 0)

    def test_getBootPath(self):
        """Tests getBootPath Function"""
        self.assertEqual(self.parser.getBootPath("/path/to/some/file"), "/file")

    def test_getPartition(self):
        """Tests getPartition Function"""
        #tests getPartition function which is used in generation of fstab
        self.parser.setTemplate("test_templates/partitions.xml")
        self.assertEqual(self.parser.parseTemplate(), 0)
        self.assertEqual(self.parser.createImage(), 0)
        self.assertEqual(self.parser.createPartitions(), 0)
        self.assertTrue(self.parser.getPartition("/boot").startswith("LABEL="))
        self.assertTrue(self.parser.getPartition("/").startswith("UUID="))

    def get_partitions(self, filename):
        """Extract partitions DOM from XML Template"""
        self.parser.setTemplate(filename)
        self.assertEqual(self.parser.parseTemplate(), 0)
        self.assertEqual(self.parser.createImage(), 0)
        partitionsDom = self.parser.boardDom.getElementsByTagName("partitions")
        return partitionsDom

    def test_verifyPrimaryPartitionSizes(self):
        """Tests verifyPrimaryPartitionSizes function"""
        #non integer partition size
        partitionsDom = self.get_partitions(\
                                          "test_templates/partitions_test1.xml")
        self.assertFalse(self.parser.verifyPrimaryPartitionSizes(partitionsDom))

        #wrong suffix partition size
        partitionsDom = self.get_partitions(\
                                          "test_templates/partitions_test2.xml")
        self.assertFalse(self.parser.verifyPrimaryPartitionSizes(partitionsDom))

        #No root partition
        partitionsDom = self.get_partitions(\
                                          "test_templates/partitions_test3.xml")
        self.assertFalse(self.parser.verifyPrimaryPartitionSizes(partitionsDom))

        #primary partition sizes > image size
        partitionsDom = self.get_partitions(\
                                          "test_templates/partitions_test4.xml")
        self.assertFalse(self.parser.verifyPrimaryPartitionSizes(partitionsDom))

        #primary partition sizes <= image size
        partitionsDom = self.get_partitions("test_templates/good.xml")
        self.assertTrue(self.parser.verifyPrimaryPartitionSizes(partitionsDom))

    def test_verifyLogicalPartitionSizes(self):
        """Tests verifyLogicalPartitionSizes function"""
        #non integer partition size
        partitionsDom = self.get_partitions("test_templates/logical_test1.xml")
        self.assertFalse(self.parser.verifyLogicalPartitionSizes(partitionsDom))

        #wrong suffix partition size
        partitionsDom = self.get_partitions("test_templates/logical_test2.xml")
        self.assertFalse(self.parser.verifyLogicalPartitionSizes(partitionsDom))

        #logical partition sizes > extended partition size
        partitionsDom = self.get_partitions("test_templates/logical_test3.xml")
        self.assertFalse(self.parser.verifyLogicalPartitionSizes(partitionsDom))

        #logical partition sizes <= extended partition size
        partitionsDom = self.get_partitions("test_templates/logical_test4.xml")
        self.assertTrue(self.parser.verifyLogicalPartitionSizes(partitionsDom))

    def test_getTagValue(self):
        """Tests getTagValue function"""
        self.parser.setTemplate("test_templates/good.xml")
        self.assertEqual(self.parser.parseTemplate(), 0)
        self.assertEqual(self.parser.getTagValue(\
                                   self.parser.boardDom, "board"), "cubietruck")

    def test_configureNetwork(self):
        """Tests configureNetwork function"""
        #good xml template
        self.parser.setTemplate("test_templates/good.xml")
        self.assertEqual(self.parser.parseTemplate(), 0)
        self.assertEqual(self.parser.configureNetwork(), 1)

        #two network interfaces specified but only one correct
        self.parser.setTemplate("test_templates/two_network_one_incorrect.xml")
        self.assertEqual(self.parser.parseTemplate(), 0)
        self.assertEqual(self.parser.configureNetwork(), 1)

        #no network interfaces specified
        self.parser.setTemplate("test_templates/no_network.xml")
        self.assertEqual(self.parser.parseTemplate(), 0)
        self.assertEqual(self.parser.configureNetwork(), \
                         rbf.BoardTemplateParser.NO_NETWORK)

if __name__ == '__main__':
    if os.getuid() != 0:
        print("You need to be root to use RootFS Build Factory")
        sys.exit(1)
    unittest.main(verbosity=2, buffer=True, exit=False)

