import unittest
from mock import (Mock, MagicMock)

import pcachefs
from pcachefs import factory
import os

class UnderlyingFsTest(unittest.TestCase):
	def test_init(self):
		ufs = pcachefs.UnderlyingFs('/path/to')

		self.assertEqual('/path/to', ufs.real_path)

	def test_getattr(self):
		# Given
		ufs = pcachefs.UnderlyingFs('/path/to')
		stat = Mock()
		os.stat = MagicMock(return_value=stat)

		fuse_stat = Mock()
		factory.create = MagicMock(return_value=fuse_stat)

		# When
		result = ufs.getattr('/my_file')

		# Then
		os.stat.assert_called_with('/path/to/my_file')
		factory.create.assert_called_with(pcachefs.FuseStat, stat)

		self.assertEqual(result, fuse_stat)

	def test_readdirShouldReturnGenerator(self):
		import types

		# Given
		ufs = pcachefs.UnderlyingFs('/path/to')
		
		os.path.isdir = MagicMock(return_value=True)

		entries = [ 'file1', 'file2', 'file3' ]
		os.listdir = MagicMock(return_value=entries)

		# When
		result = ufs.readdir('/test_dir', None)

		# Then
		os.path.isdir.assert_called_with('/path/to/test_dir')

		self.assertEquals(type(result), types.GeneratorType)
	
	def test_readdirShouldReturnDirentriesFromFileSystem(self):
		import fuse

		# Given
		ufs = pcachefs.UnderlyingFs('/path/to')
		
		os.path.isdir = MagicMock(return_value=True)

		entries = [ 'file1', 'file2', 'file3' ]
		os.listdir = MagicMock(return_value=entries)

		# When
		result = ufs.readdir('/test_dir', None)

		# Then
		os.path.isdir.assert_called_with('/path/to/test_dir')

		resultList = []
		for r in result:
			# extract 'path' attributes of the Direntry objects
			# contained in result
			resultList.append(r.name)

		for r in [ 'file1', 'file2', 'file3' ]:
			self.assertIn(r, resultList)

	def test_readdirShouldReturnParentAndCurDirDirentries(self):
		import fuse

		# Given
		ufs = pcachefs.UnderlyingFs('/path/to')
		
		os.path.isdir = MagicMock(return_value=True)

		entries = [ 'file1', 'file2', 'file3' ]
		os.listdir = MagicMock(return_value=entries)

		# When
		result = ufs.readdir('/test_dir', None)

		# Then
		os.path.isdir.assert_called_with('/path/to/test_dir')

		resultList = []
		for r in result:
			# extract 'path' attributes of the Direntry objects
			# contained in result
			resultList.append(r.name)

		for r in [ '.', '..' ]:
			self.assertIn(r, resultList)

	def test_readShouldReadDataFromFilesystemFiles(self):
		import __builtin__

		# Given
		ufs = pcachefs.UnderlyingFs('/path/to')

		# create mock for 'open()' builtin
		mock_open = MagicMock()
		__builtin__.open = mock_open

		mock_open.return_value = MagicMock(spec=file)
		
		# When
		ufs.read('/my/file', 400, 3)

		# Then
		mock_open.assert_called_with('/path/to/my/file', 'rb')
		file_handle = mock_open.return_value.__enter__.return_value
		file_handle.seek.assert_called_with(3)
		file_handle.read.assert_called_with(400)
