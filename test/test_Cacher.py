import unittest
from mockito import (when, mock, verify, any)

import os, pcachefs
import pcachefs.pcachefs as pcachefsinternal

class CacherTest(unittest.TestCase):
    def test_shouldCreateCacheDirectoryOnInitIfNoneExists(self):
        # Given

        ufs = mock()
        pcachefsinternal.os = mock()
        pcachefsinternal.os.path = mock()
        pcachefsinternal.__builtin__ = mock()

        when(pcachefsinternal.os.path).exists(any()).thenReturn(False)

        # When
        cacher = pcachefs.Cacher('/cachedir', ufs)

        # Then
        self.assertEquals(cacher.underlying_fs, ufs)
        self.assertEquals(cacher.cachedir, '/cachedir')

        # TODO this may get changed
        self.assertEquals(cacher.cache_only_mode, False)

        verify(pcachefsinternal.os).makedirs('/cachedir')

    def test_readShouldUseUfsIfNoCacheDataExists(self):
        import __builtin__
        #import pickle

        # Given
        ufs = mock()
        pcachefsinternal.os = mock()
        pcachefsinternal.os.path = mock()
        pcachefsinternal.__builtin__ = mock()

        when(pcachefsinternal.os.path).exists(any()).thenReturn(False)

        cacher = pcachefs.Cacher('/cachedir', ufs)

        pcachefsinternal.pickle = mock()

        # Configure __builtin__.open to return a different
        # file handle for each filename it could be called with
        data_range_handle = mock()
        data_handle = mock()

        when(__builtin__).open('/cachedir/myfile/cache.data.range', 'rb').thenReturn(data_range_handle)
        when(__builtin__).open('/cachedir/myfile/cache.data', 'wb').thenReturn(data_handle)

        # When
        result = cacher.read('/myfile', 400, 3)

        # Then
        self.assertTrue(False) ## TODO

        data_range = file_handle_mocks()

