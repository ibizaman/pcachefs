from mockito import when, mock, verify, any
from .utils import WithWrapper

from pcachefs import UnderlyingFs, FuseStat, factory
import os
import __builtin__


def test_init():
    ufs = UnderlyingFs('/path/to')

    assert '/path/to' == ufs.real_path


def test_getattr():
    # Given
    ufs = UnderlyingFs('/path/to')

    stat = mock()
    when(os).stat('/path/to/my_file').thenReturn(stat)

    fuse_stat = mock()
    when(factory).create(FuseStat, stat).thenReturn(fuse_stat)

    # When
    result = ufs.getattr('/my_file')

    # Then
    assert result == fuse_stat


def test_readdirShouldReturnGenerator():
    # Given
    ufs = UnderlyingFs('/path/to')

    when(os.path).isdir('/path/to/test_dir').thenReturn(True)

    entries = [ 'file1', 'file2', 'file3' ]
    when(os).listdir('/path/to/test_dir').thenReturn(entries)

    # When
    result = ufs.readdir('/test_dir', None)

    # Then
    import types
    assert type(result) == types.GeneratorType


def test_readdirShouldReturnDirentriesFromFileSystem():
    # Given
    ufs = UnderlyingFs('/path/to')

    when(os.path).isdir('/path/to/test_dir').thenReturn(True)

    entries = [ 'file1', 'file2', 'file3' ]
    when(os).listdir('/path/to/test_dir').thenReturn(entries)

    # When
    result = ufs.readdir('/test_dir', None)

    # Then
    resultList = []
    for r in result:
        # extract 'path' attributes of the Direntry objects
        # contained in result
        resultList.append(r.name)

    for r in [ 'file1', 'file2', 'file3' ]:
        assert r in resultList


def test_readdirShouldReturnParentAndCurDirDirentries():
    # Given
    ufs = UnderlyingFs('/path/to')

    when(os.path).isdir('/path/to/test_dir').thenReturn(True)

    entries = [ 'file1', 'file2', 'file3' ]
    when(os).listdir('/path/to/test_dir').thenReturn(entries)

    # When
    result = ufs.readdir('/test_dir', None)

    # Then
    resultList = []
    for r in result:
        # extract 'path' attributes of the Direntry objects
        # contained in result
        resultList.append(r.name)

    for r in [ '.', '..' ]:
        assert r in resultList


def test_readShouldReadDataFromFilesystemFiles():
    # Given
    ufs = UnderlyingFs('/path/to')

    mockFile = mock()
    when(mockFile).seek(3).thenReturn(True)
    when(mockFile).read(400).thenReturn('x'*400)

    when(__builtin__).open('/path/to/my/file', 'rb').thenReturn(WithWrapper(mockFile))

    # When
    result = ufs.read('/my/file', 400, 3)

    # Then
    verify(mockFile).seek(3)
    verify(mockFile).read(400)

    assert result == 'x'*400

