import os
import signal
import shutil
import stat
import tempfile
import time
from multiprocessing import Process

import pytest

from pcachefs import main


@pytest.fixture
def rootdir():
    dir = tempfile.mkdtemp(dir=os.path.join(os.path.dirname(__file__), 'testroot'))
    yield dir
    shutil.rmtree(dir)


@pytest.fixture
def sourcedir(rootdir):
    dir = os.path.join(rootdir, 'source')
    os.makedirs(dir)
    yield dir


@pytest.fixture
def cachedir(rootdir):
    dir = os.path.join(rootdir, 'cache')
    os.makedirs(dir)
    yield dir


@pytest.fixture
def mountdir(rootdir):
    dir = os.path.join(rootdir, 'mount')
    os.makedirs(dir)
    yield dir


@pytest.fixture
def pcachefs(sourcedir, cachedir, mountdir):
    signal.signal(signal.SIGINT, signal.SIG_DFL)
    p = Process(target=main, args=(['-d', '-s', '-c', cachedir, '-t', sourcedir, mountdir],))
    p.start()
    yield
    os.kill(p.pid, signal.SIGINT)
    p.join()


def write_to_file(dirname, path, content):
    with open(os.path.join(dirname, *path), 'w') as f:
        f.write(content)
    # Needed to let pcachefs propagate changes
    time.sleep(.1)


def create_directory(dirname, path):
    os.makedirs(os.path.join(dirname, *path))
    # Needed to let pcachefs propagate changes
    time.sleep(.1)


def read_from_file(dirname, path):
    try:
        with open(os.path.join(dirname, *path), 'r') as f:
            return f.read()
    except IOError as e:
        print('Could not open', os.path.join(dirname, *path), e)
        return None


class ListDir(object):
    def __init__(self, files, dirs):
        self.files = sorted(list(files))
        self.dirs = sorted(list(dirs))

    def __repr__(self):
        return '<ListDir files: {}, dirs: {}>'.format(self.files, self.dirs)

    def __eq__(self, other):
        return self.dirs == other.dirs and self.files == other.files

    def __contains__(self, what):
        return what in self.files or what in self.dirs


def list_dir(dirname, path=None):
    files = set()
    dirs = set()
    root = os.path.join(dirname, *(path or []))
    for object in os.listdir(root):
        is_dir = stat.S_ISDIR(os.stat(os.path.join(root, object)).st_mode)
        if is_dir:
            dirs.add(object)
        else:
            files.add(object)

    return ListDir(files, dirs)


def test_create_file(pcachefs, sourcedir, mountdir):
    assert 'a' not in list_dir(sourcedir)
    assert 'a' not in list_dir(mountdir)
    assert read_from_file(sourcedir, ['a']) == None
    assert read_from_file(mountdir, ['a']) == None

    write_to_file(sourcedir, ['a'], '1')
    assert 'a' in list_dir(sourcedir)
    assert 'a' in list_dir(mountdir)
    assert read_from_file(sourcedir, ['a']) == '1'
    assert read_from_file(mountdir, ['a']) == '1'


def test_cached_file_not_updated(pcachefs, sourcedir, mountdir):
    write_to_file(sourcedir, ['a'], '1')
    # load in cache
    read_from_file(mountdir, ['a'])
    write_to_file(sourcedir, ['a'], '2')
    assert 'a' in list_dir(sourcedir)
    assert 'a' in list_dir(mountdir)
    assert read_from_file(sourcedir, ['a']) == '2'
    assert read_from_file(mountdir, ['a']) == '1'


def test_only_cached_file_at_read(pcachefs, sourcedir, mountdir):
    write_to_file(sourcedir, ['a'], '1')
    write_to_file(sourcedir, ['a'], '2')
    assert 'a' in list_dir(sourcedir)
    assert 'a' in list_dir(mountdir)
    assert read_from_file(sourcedir, ['a']) == '2'
    assert read_from_file(mountdir, ['a']) == '2'


def test_create_directory(pcachefs, sourcedir, mountdir):
    assert 'a' not in list_dir(sourcedir)
    assert 'a' not in list_dir(mountdir)
    assert read_from_file(sourcedir, ['a']) == None
    assert read_from_file(mountdir, ['a']) == None

    create_directory(sourcedir, ['a'])
    assert 'a' in list_dir(sourcedir)
    assert 'a' in list_dir(mountdir)
    write_to_file(sourcedir, ['a', 'a'], '1')
    assert 'a' in list_dir(sourcedir)
    assert 'a' in list_dir(mountdir)
    assert read_from_file(sourcedir, ['a', 'a']) == '1'
    assert read_from_file(mountdir, ['a', 'a']) == '1'


def test_cached_directory_not_updated(pcachefs, sourcedir, mountdir):
    assert 'a' not in list_dir(sourcedir)
    assert 'a' not in list_dir(mountdir)
    assert read_from_file(sourcedir, ['a']) == None
    assert read_from_file(mountdir, ['a']) == None

    create_directory(sourcedir, ['a'])
    assert 'a' in list_dir(sourcedir)
    assert 'a' in list_dir(mountdir)
    write_to_file(sourcedir, ['a', 'a'], '1')
    assert 'a' in list_dir(sourcedir, ['a'])
    assert 'a' in list_dir(mountdir, ['a'])
    assert read_from_file(sourcedir, ['a', 'a']) == '1'
    assert read_from_file(mountdir, ['a', 'a']) == '1'

    # FIXME: not consistent behavior, b does not appear in listdir
    # although we can read the file.
    write_to_file(sourcedir, ['a', 'a'], '2')
    write_to_file(sourcedir, ['a', 'b'], '3')
    assert 'a' in list_dir(sourcedir, ['a'])
    assert 'a' in list_dir(mountdir, ['a'])
    assert 'b' in list_dir(sourcedir, ['a'])
    assert 'b' not in list_dir(mountdir, ['a'])
    assert read_from_file(sourcedir, ['a', 'a']) == '2'
    assert read_from_file(mountdir, ['a', 'a']) == '1'
    assert read_from_file(sourcedir, ['a', 'b']) == '3'
    assert read_from_file(mountdir, ['a', 'b']) == '3'
