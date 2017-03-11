import os
import signal
import shutil
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


def write_to_file(dirname, basename, content):
    with open(os.path.join(dirname, basename), 'w') as f:
        f.write(content)
    # Needed to let pcachefs propagate changes
    time.sleep(.1)


def read_from_file(dirname, basename):
    try:
        with open(os.path.join(dirname, basename), 'r') as f:
            return f.read()
    except IOError as e:
        print('Could not open', os.path.join(dirname, basename), e)
        return None


def test_create_file(pcachefs, sourcedir, mountdir):
    assert 'a' not in os.listdir(sourcedir)
    assert 'a' not in os.listdir(mountdir)
    assert read_from_file(sourcedir, 'a') == None
    assert read_from_file(mountdir, 'a') == None

    write_to_file(sourcedir, 'a', '1')
    assert 'a' in os.listdir(sourcedir)
    assert 'a' in os.listdir(mountdir)
    assert read_from_file(sourcedir, 'a') == '1'
    assert read_from_file(mountdir, 'a') == '1'


def test_cache_not_updated(pcachefs, sourcedir, mountdir):
    write_to_file(sourcedir, 'a', '1')
    # load in cache
    read_from_file(mountdir, 'a')
    write_to_file(sourcedir, 'a', '2')
    assert 'a' in os.listdir(sourcedir)
    assert 'a' in os.listdir(mountdir)
    assert read_from_file(sourcedir, 'a') == '2'
    assert read_from_file(mountdir, 'a') == '1'


def test_only_cached_at_read(pcachefs, sourcedir, mountdir):
    write_to_file(sourcedir, 'a', '1')
    write_to_file(sourcedir, 'a', '2')
    assert 'a' in os.listdir(sourcedir)
    assert 'a' in os.listdir(mountdir)
    assert read_from_file(sourcedir, 'a') == '2'
    assert read_from_file(mountdir, 'a') == '2'
