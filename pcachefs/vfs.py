import os
import stat
import time

import fuse

from pcachefsutil import debug, is_read_only_flags
from pcachefsutil import (E_NO_SUCH_FILE, E_PERM_DENIED, E_NOT_IMPL)


class SimpleVirtualFile(object):
    """
    A Virtual File that allows you to specify callback functions, called
    when the file is read or changed.

    This class is generally much simpler to use than using VirtualFile
    directly and hides much of the implementation detail of FUSE.

    Note that in order to track changes properly this class will cache
    the content returned by 'callback_on_read' when a file is opened.
    This cache is discarded when the file is closed (via the FUSE
    release() function). This won't be a problem for you unless you
    intend to return a large amount of data (e.g. hundreds of MB) from
    'callback_on_read' in which case you may see performance hits or run
    out of memory. To get around this subclass VirtualFile instead of
    using SimpleVirtualFile.
    """
    def __init__(self, name, callback_on_read, callback_on_change = None):
        self.name = name

        self.callback_on_read = callback_on_read
        self.callback_on_change = callback_on_change

        self.content = None

    def _get_content(self):
        if self.content is None:
            result = self.callback_on_read()

            # store content as a list representation of a string, so that
            # we can modify it when write() is called
            self.content = list(result)

        return ''.join(self.content)

    def is_read_only(self):
        """Determines if this file is writeable or not.

        Read-only files will never have their write() functions called
        and their content cannot be changed by any users of the
        filesystem (including root).

        Returns true if no write_function is specified.
        """
        return self.callback_on_change is None

    def read(self, size, offset):
        """Read content of this virtual file."""
        return self._get_content()[offset:offset+size]

    def size(self):
        """Returns the size of the file, for use in calls to getattr().

        The default implementation always returns zero. You should
        override this to return an accurate value, otherwise apps will
        assume the file is empty.
        """
        return len(self._get_content())

    def write(self, buf, offset):
        """
        Write content of this virtual file.

        If you override this function you MUST also override is_read_only()
        to return True, or it will never be used!

        Should return the number of bytes successfully written.
        """
        # Ensure self.content is populated
        self._get_content()

        self.content[offset:offset+len(buf)] = buf
        return len(buf)

    def truncate(self, size):
        """Truncate this virtual file.

        If you override this function you MUST also override is_read_only()
        to return True, or it will never be used!
        """
        # truncate the string
        self.content = list(self._get_content()[:size])

        return 0 # success

    def release(self):
        """Release handle to this file.

        If you override this function you MUST also override is_read_only()
        to return True, or it will never be used!
        """
        # convert list to string and return it
        self.callback_on_change(self._get_content())

        # clear cache
        self.content = None

    def flush(self):  # pylint: disable=no-self-use
        """Flush any outstanding data waiting to be written to this virtual file.

        If you override this function you MUST also override is_read_only()
        to return True, or it will never be used!
        """
        return None

    def atime(self):  # pylint: disable=no-self-use
        """Returns the access time of the file.

        For use in calls to getattr(). The default implementation
        returns the current system time.
        """
        return time.mktime(time.gmtime())

    def mtime(self):  # pylint: disable=no-self-use
        """Returns the modification time of the file.

        For use in calls to getattr(). The default implementation
        returns the current system time.
        """
        return time.mktime(time.gmtime())

    def ctime(self):  # pylint: disable=no-self-use
        """Returns the creation time of the file.

        For use in calls to getattr(). The default implementation
        returns the current system time.
        """
        return time.mktime(time.gmtime())

    def uid(self):  # pylint: disable=no-self-use
        """Returns the UID that owns the file.

        The default implementation returns None, in which case the
        VirtualFileFS instance will use the UID of the user currently
        accessing the file.
        """
        return None

    def gid(self):  # pylint: disable=no-self-use
        """Returns the GID that owns the file.

        The default implementation returns None, in which case the
        VirtualFileFS instance will use the GID of the user currently
        accessing the file.
        """
        return None


class VirtualFS(object):
    """Provides a fuse interface to 'virtual' files and directories.

    This class deliberately mimics the FUSE interface, so you can
    delegate to it from a real FUSE filesystem, or use it in some other
    context.

    Virtual files are represented by instances of VirtualFile stored in
    a dict. Virtual files can be made read-only or writeable.
    """
    def __init__(self, root, cacher):
        """Initialise a new VirtualFileFS.

        Root folder under which all virtual objects will reside.
        """
        self.root = root
        self.cacher = cacher

    def get_relative_path(self, path):
        """Returns path relative to the given root virtual folder."""
        path_xpl = path.split(os.sep)
        if path_xpl[0] == '' and path_xpl[1] == self.root:
            if len(path_xpl) > 2:
                return os.path.join(*path_xpl[2:])
            return ''
        return None

    def contains(self, path):
        """Returns true if the given path exists as a virtual file."""
        return self.get_relative_path(path) is not None


    def getattr(self, path):
        """Retrieve attributes of a path in the VirtualFS."""
        debug('VirtualFS.getattr', path)
        virtual_path = self.get_relative_path(path)
        if virtual_path is None:
            return E_NO_SUCH_FILE

        parent_path = os.sep + os.path.dirname(virtual_path)
        parent_is_file = stat.S_ISREG(self.cacher.getattr(parent_path).st_mode)
        if parent_is_file:
            if os.path.basename(virtual_path) not in ['cached']:
                return E_NO_SUCH_FILE
            return self.cacher.getattr(parent_path)
        else:
            a = self.cacher.getattr(os.sep + virtual_path)
            a.st_mode = stat.S_IFDIR | 0o777
            return a

    def readdir(self, path, offset):
        debug('VirtualFS.readdir', path, offset)
        virtual_path = self.get_relative_path(path)
        if virtual_path is not None:
            is_file = stat.S_ISREG(self.cacher.getattr(os.sep + virtual_path).st_mode)
            if is_file:
                yield fuse.Direntry('cached')
            else:
                for f in self.cacher.readdir(os.sep + virtual_path, offset):
                    yield fuse.Direntry(f.name)
            yield None

        if path == '/':
            yield fuse.Direntry(self.root)

    def open(self, path, flags):
        debug('VirtualFS.open', path, flags)
        virtual_path = self.get_relative_path(path)
        if virtual_path is None:
            return E_NO_SUCH_FILE

        if os.path.basename(virtual_path) in ['cached']:
            return 0

        if not is_read_only_flags(flags):
            return E_PERM_DENIED

        return 0

    def read(self, path, size, offset):
        debug('VirtualFS.read', path, size, offset)
        virtual_path = self.get_relative_path(path)
        if virtual_path is None:
            return E_NO_SUCH_FILE

        parent_path = os.sep + os.path.dirname(virtual_path)
        parent_is_file = stat.S_ISREG(self.cacher.getattr(parent_path).st_mode)
        if not parent_is_file:
            return E_NO_SUCH_FILE

        basename = os.path.basename(virtual_path)
        if basename != 'cached':
            return E_NO_SUCH_FILE

        attr = self.cacher.getattr(parent_path)
        return str(self.cacher.get_cached_blocks(parent_path).number() / float(attr.st_size * attr.st_blksize))

    def mknod(self, path, mode, dev):  # pylint: disable=no-self-use
        debug('VirtualFS.mknod', path, mode, dev)
        # Don't allow creation of new files
        return E_PERM_DENIED

    def unlink(self, path):  # pylint: disable=no-self-use
        debug('VirtualFS.unlink', path)
        # Don't allow removal of files
        return E_PERM_DENIED

    def write(self, path, buf, offset):
        debug('VirtualFS.write', path, buf, offset)
        virtual_path = self.get_relative_path(path)
        if virtual_path is None:
            return E_NO_SUCH_FILE

        basename = os.path.basename(virtual_path)
        if basename == 'cached':
            real_path = os.sep + os.path.dirname(virtual_path)
            if buf == '1':
                attr = self.cacher.underlying_fs.getattr(real_path)
                size = attr.st_size * attr.st_blksize
                self.cacher.read(real_path, size, 0, force_reload=True)
            elif buf == '0':
                self.cacher.remove_cached_data(real_path)
            else:
                return E_NOT_IMPL
            return len(buf)
        else:
            return E_NO_SUCH_FILE

    def truncate(self, path, size):  # pylint: disable=no-self-use
        debug('VirtualFS.truncate', path, size)
        return 0

    def flush(self, path, fh=None):  # pylint: disable=no-self-use, unused-argument
        debug('VirtualFS.flush', path)
        return 0

    def release(self, path, fh=None):  # pylint: disable=no-self-use, unused-argument
        debug('VirtualFS.release', path)
        return 0


def fake_stat(virtual_file):
    """Create fuse stat from file."""
    if virtual_file is None:
        return E_NO_SUCH_FILE

    result = fuse.Stat()

    if virtual_file.is_read_only():
        result.st_mode = stat.S_IFREG | 0o444
    else:
        result.st_mode = stat.S_IFREG | 0o644

    # Always 1 for now (seems to be safe for files and dirs)
    result.st_nlink = 1

    result.st_size = virtual_file.size()

    # Must return seconds-since-epoch timestamps
    result.st_atime = virtual_file.atime()
    result.st_mtime = virtual_file.mtime()
    result.st_ctime = virtual_file.ctime()

    # You can set these to anything, they're set by FUSE
    result.st_dev = 1
    result.st_ino = 1

    # GetContext() returns uid/gid of the process that
    # initiated the syscall currently being handled
    context = fuse.FuseGetContext()
    if virtual_file.uid() is None:
        result.st_uid = context['uid']
    else:
        result.st_uid = virtual_file.uid()

    if virtual_file.gid() is None:
        result.st_gid = context['gid']
    else:
        result.st_gid = virtual_file.gid()

    return result
