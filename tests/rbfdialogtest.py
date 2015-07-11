#!/usr/bin/python
# pylint: disable=

"""@package rbfdialogtest
Tests for RBF Dialog Interface
"""

import os
import sys
import unittest
sys.path.append("..")
import rbfdialog

class RbfDialogTest(unittest.TestCase):
    """Tests for RBF Dialog Interface"""
    def setUp(self):
        self.creator = rbfdialog.BoardTemplateCreator()

    def tearDown(self):
        del self.creator

    def test_readXml(self):
        """Tests readXml function"""
        #bad xml
        self.creator.setTemplate("test_templates/bad.xml")
        self.assertEqual(self.creator.readXml(), \
                         rbfdialog.BoardTemplateCreator.ERROR_PARSING_XML)

        #good xml
        self.creator.setTemplate("test_templates/good.xml")
        self.assertEqual(self.creator.readXml(), 0)

    def test_readTags(self):
        """Tests readTags function"""

        #incorrect tags
        self.creator.setTemplate("test_templates/incomplete.xml")
        self.assertEqual(self.creator.readXml(), 0)
        self.assertEqual(self.creator.readTags(), \
                         rbfdialog.BoardTemplateCreator.ERROR_PARSING_XML_TAGS)

        #good xml
        self.creator.setTemplate("test_templates/good.xml")
        self.assertEqual(self.creator.readXml(), 0)
        self.assertEqual(self.creator.readTags(), 0)

    def test_readImageData(self):
        """Tests readImageData function"""
        #bad image size
        self.creator.setTemplate("test_templates/bad_image_size.xml")
        self.assertEqual(self.creator.readXml(), 0)
        self.assertEqual(self.creator.readImageData(), \
                         rbfdialog.BoardTemplateCreator.INVALID_IMAGE_SIZE)

        #non integer image size
        self.creator.setTemplate("test_templates/non_integer_image_size.xml")
        self.assertEqual(self.creator.readXml(), 0)
        self.assertEqual(self.creator.readImageData(), \
                         rbfdialog.BoardTemplateCreator.INVALID_IMAGE_SIZE)

        #good xml
        self.creator.setTemplate("test_templates/good.xml")
        self.assertEqual(self.creator.readXml(), 0)
        self.assertEqual(self.creator.readImageData(), 0)

    def test_readKernelData(self):
        """Tests readKernelData function"""
        #kernel information missing
        self.creator.setTemplate("test_templates/no_kernel.xml")
        self.assertEqual(self.creator.readXml(), 0)
        self.assertEqual(self.creator.readKernelData(), \
                         rbfdialog.BoardTemplateCreator.NO_KERNEL)

        #kernel type missing
        self.creator.setTemplate("test_templates/no_kernel_type.xml")
        self.assertEqual(self.creator.readXml(), 0)
        self.assertEqual(self.creator.readKernelData(), \
                         rbfdialog.BoardTemplateCreator.NO_KERNEL_TYPE)

        #custom kernel info missing/incorrect
        self.creator.setTemplate("test_templates/bad_custom_kernel.xml")
        self.assertEqual(self.creator.readXml(), 0)
        self.assertEqual(self.creator.readKernelData(), \
                        rbfdialog.BoardTemplateCreator.ERROR_CUSTOM_KERNEL_INFO)

        #good custom kernel info
        self.creator.setTemplate("test_templates/good_custom_kernel.xml")
        self.assertEqual(self.creator.readXml(), 0)
        self.assertEqual(self.creator.readKernelData(), 0)

    def test_readPartitions(self):
        """Tests readPartitions function"""
        #partition info missing
        self.creator.setTemplate("test_templates/no_partitions.xml")
        self.assertEqual(self.creator.readXml(), 0)
        self.assertEqual(self.creator.readPartitions(), \
                         rbfdialog.BoardTemplateCreator.NO_PARTITIONS)

        #good xml
        self.creator.setTemplate("test_templates/good.xml")
        self.assertEqual(self.creator.readXml(), 0)
        self.assertEqual(self.creator.readImageData(), 0)
        self.assertEqual(self.creator.readPartitions(), 0)

    def test_readRepoData(self):
        """Tests readRepoData function"""
        #repo data incorrect
        self.creator.setTemplate("test_templates/incorrect_repo.xml")
        self.assertEqual(self.creator.readXml(), 0)
        self.assertEqual(self.creator.readRepoData(), \
                         rbfdialog.BoardTemplateCreator.INCORRECT_REPOSITORY)

        #good xml
        self.creator.setTemplate("test_templates/good.xml")
        self.assertEqual(self.creator.readXml(), 0)
        self.assertEqual(self.creator.readRepoData(), 0)

    def test_readPackages(self):
        """Tests readPackages function"""
        #no packages tag in xml
        self.creator.setTemplate("test_templates/no_packages.xml")
        self.assertEqual(self.creator.readXml(), 0)
        self.assertEqual(self.creator.readPackages(), \
                         rbfdialog.BoardTemplateCreator.NO_PACKAGES)

        #good xml
        self.creator.setTemplate("test_templates/good.xml")
        self.assertEqual(self.creator.readXml(), 0)
        self.assertEqual(self.creator.readPackages(), 0)

    def test_readNetworkData(self):
        """Tests readNetworkData function"""
        #no network information
        self.creator.setTemplate("test_templates/no_network.xml")
        self.assertEqual(self.creator.readXml(), 0)
        self.assertEqual(self.creator.readNetworkData(), \
                         rbfdialog.BoardTemplateCreator.NO_NETWORK)

        #missing data in network config
        self.creator.setTemplate("test_templates/two_network_one_incorrect.xml")
        self.assertEqual(self.creator.readXml(), 0)
        self.assertEqual(self.creator.readNetworkData(), \
                         rbfdialog.BoardTemplateCreator.BAD_NETWORK_DATA)

        #good xml
        self.creator.setTemplate("test_templates/good.xml")
        self.assertEqual(self.creator.readXml(), 0)
        self.assertEqual(self.creator.readNetworkData(), 0)

    def test_validatePartitionData(self):
        """Tests validatePartitionData function"""
        #test without reading image data first
        partitionFields = ['1G', 'primary', 'ext4', '/']
        self.creator.setTemplate("test_templates/good.xml")
        self.assertEqual(self.creator.readXml(), 0)
        #self.assertEqual(self.creator.readImageData(), 0)
        self.assertEqual(self.creator.validatePartitionData(partitionFields), \
                         rbfdialog.BoardTemplateCreator.NO_IMAGE)

        #non integer partition size
        partitionFields = ['1.1G', 'primary', 'ext4', '/']
        self.creator.setTemplate("test_templates/good.xml")
        self.assertEqual(self.creator.readXml(), 0)
        self.assertEqual(self.creator.readImageData(), 0)
        self.assertEqual(self.creator.validatePartitionData(partitionFields), \
                         rbfdialog.BoardTemplateCreator.INVALID_PARTITION_SIZE)

        #partition size with no suffix
        partitionFields = ['1', 'primary', 'ext4', '/']
        self.creator.setTemplate("test_templates/good.xml")
        self.assertEqual(self.creator.readXml(), 0)
        self.assertEqual(self.creator.readImageData(), 0)
        self.assertEqual(self.creator.validatePartitionData(partitionFields), \
                         rbfdialog.BoardTemplateCreator.INVALID_PARTITION_SIZE)

        #two extended partitions
        partitionFields = ['1G', 'extended', '', '']
        self.creator.setTemplate("test_templates/one_extended.xml")
        self.assertEqual(self.creator.readXml(), 0)
        self.assertEqual(self.creator.readImageData(), 0)
        self.assertEqual(self.creator.readPartitions(), 0)
        self.assertEqual(self.creator.validatePartitionData(partitionFields), \
                        rbfdialog.BoardTemplateCreator.EXTENDED_PARTITION_ERROR)


        #five primary partitions
        partitionFields = ['1G', 'primary', 'ext4', '/']
        self.creator.setTemplate("test_templates/four_primary_partitions.xml")
        self.assertEqual(self.creator.readXml(), 0)
        self.assertEqual(self.creator.readImageData(), 0)
        self.assertEqual(self.creator.readPartitions(), 0)
        self.assertEqual(self.creator.validatePartitionData(partitionFields), \
                         rbfdialog.BoardTemplateCreator.TOTAL_PARTITIONS_ERROR)

        #primary partition sizes exceed image size
        partitionFields = ['1G', 'primary', 'ext4', '/var']
        self.creator.setTemplate("test_templates/good.xml")
        self.assertEqual(self.creator.readXml(), 0)
        self.assertEqual(self.creator.readImageData(), 0)
        self.assertEqual(self.creator.readPartitions(), 0)
        self.assertEqual(self.creator.validatePartitionData(partitionFields), \
                       rbfdialog.BoardTemplateCreator.PRIMARY_PARTITION_EXCEEDS)

        #trying to create a logical partition before extended one
        partitionFields = ['1G', 'logical', 'ext4', '/var']
        self.creator.setTemplate("test_templates/good.xml")
        self.assertEqual(self.creator.readXml(), 0)
        self.assertEqual(self.creator.readImageData(), 0)
        self.assertEqual(self.creator.readPartitions(), 0)
        self.assertEqual(self.creator.validatePartitionData(partitionFields), \
                         rbfdialog.BoardTemplateCreator.LOGICAL_BEFORE_EXTENDED)

        #logical partition sizes exceed extended size
        partitionFields = ['1G', 'logical', 'ext4', '/var']
        self.creator.setTemplate("test_templates/one_extended.xml")
        self.assertEqual(self.creator.readXml(), 0)
        self.assertEqual(self.creator.readImageData(), 0)
        self.assertEqual(self.creator.readPartitions(), 0)
        self.assertEqual(self.creator.validatePartitionData(partitionFields), \
                       rbfdialog.BoardTemplateCreator.LOGICAL_PARTITION_EXCEEDS)

        #successfully validating a partition
        partitionFields = ['500M', 'primary', 'ext4', '/var']
        self.creator.setTemplate("test_templates/good.xml")
        self.assertEqual(self.creator.readXml(), 0)
        self.assertEqual(self.creator.readImageData(), 0)
        self.assertEqual(self.creator.readPartitions(), 0)
        self.assertEqual(self.creator.validatePartitionData(partitionFields), 0)

    def test_getTagValue(self):
        """Tests getTagValue function"""
        self.creator.setTemplate("test_templates/good.xml")
        self.assertEqual(self.creator.readXml(), 0)
        self.assertEqual(self.creator.getTagValue(\
                                  self.creator.boardDom, "board"), "cubietruck")

    def test_getFilename(self):
        """Teste getFilename function"""
        self.assertEqual(self.creator.getFilename("name"), "name")
        self.assertEqual(\
                    self.creator.getFilename("/path/to/some/file/name"), "name")

if __name__ == '__main__':
    if os.getuid() != 0:
        print("You need to be root to use RootFS Build Factory")
        sys.exit(1)
    unittest.main(verbosity=2, buffer=True, exit=False)
