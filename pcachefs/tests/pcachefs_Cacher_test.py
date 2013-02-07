import unittest
from mock import (Mock, MagicMock)

import os
import pcachefs

class CacherTest(unittest.TestCase):
	def test_init(self):
		# Given
		ufs = Mock()
		os.path.exists = Mock(return_value=False)
		os.makedirs = Mock()

		# When
		cacher = pcachefs.Cacher('/cachedir', ufs)

		# Then
		self.assertEquals(cacher.underlying_fs, ufs)
		self.assertEquals(cacher.cachedir, '/cachedir')

		# TODO this may get changed
		self.assertEquals(cacher.cache_only_mode, False)

		os.makedirs.assert_called_with('/cachedir')

	def test_readShouldUseUfsIfNoCacheDataExists(self):
		import __builtin__
		import pickle

		# Given
		ufs = Mock()
		cacher = pcachefs.Cacher('/cachedir', ufs)

		pickle.load = Mock()

		# Configure __builtin__.open to return a different
		# file handle for each filename it could be called with
		file_handle_mocks = {
			('/cachedir/myfile/cache.data.range', 'rb'): Mock(),
			('/cachedir/myfile/cache.data', 'wb'): Mock(),
		}
		__builtin__.open = Mock()
		__builtin__.open.side_effect = lambda file, flags: file_handle_mocks[file, flags]

		# When
		result = cacher.read('/myfile', 400, 3)
		
		# Then
		self.assertTrue(False) ## TODO
