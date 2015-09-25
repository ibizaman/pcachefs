from mockito import when, mock, verify, any

from pcachefs import Cacher
import os


def test_shouldCreateCacheDirectoryOnInitIfNoneExists():
    # Given
    ufs = mock()

    when(os.path).exists(any()).thenReturn(False)
    when(os).makedirs('/cachedir').thenReturn(True)

    # When
    cacher = Cacher('/cachedir', ufs)

    # Then
    assert cacher.underlying_fs == ufs
    assert cacher.cachedir == '/cachedir'

    # TODO this may get changed
    assert cacher.cache_only_mode == False

    verify(os).makedirs('/cachedir')

