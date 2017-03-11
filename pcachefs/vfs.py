from pcachefsutil import debug
from pcachefsutil import (E_NO_SUCH_FILE, E_PERM_DENIED)
import fuse
import stat
import time
import os

"""
A Virtual File that allows you to specify callback functions, called when the file is read
or changed.

This class is generally much simpler to use than using VirtualFile directly and hides much
of the implementation detail of FUSE.

Note that in order to track changes properly this class will cache the content returned by
'callback_on_read' when a file is opened. This cache is discarded when the file is closed
(via the FUSE release() function). This won't be a problem for you unless you intend to
return a large amount of data (e.g. hundreds of MB) from 'callback_on_read' in which case
you may see performance hits or run out of memory. To get around this subclass VirtualFile
instead of using SimpleVirtualFile.
"""
class SimpleVirtualFile:

    def __init__(self, name, callback_on_read, callback_on_change = None):
        self.name = name

        self.callback_on_read = callback_on_read
        self.callback_on_change = callback_on_change

        self.content = None
        debug('SVF init, name: ' + str(name) + ', cor: ' + str(callback_on_read) + ', coc: ' + str(callback_on_change))

    def _get_content(self):
        if self.content == None:
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
        return self.callback_on_change == None

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

    def flush(self):
        """Flush any outstanding data waiting to be written to this virtual file.

        If you override this function you MUST also override is_read_only()
        to return True, or it will never be used!
        """
        return None

    def atime(self):
        """Returns the access time of the file.

        For use in calls to getattr(). The default implementation
        returns the current system time.
        """
        return time.mktime(time.gmtime())

    def mtime(self):
        """Returns the modification time of the file.

        For use in calls to getattr(). The default implementation
        returns the current system time.
        """
        return time.mktime(time.gmtime())

    def ctime(self):
        """Returns the creation time of the file.

        For use in calls to getattr(). The default implementation
        returns the current system time.
        """
        return time.mktime(time.gmtime())

    def uid(self):
        """Returns the UID that owns the file.

        The default implementation returns None, in which case the
        VirtualFileFS instance will use the UID of the user currently
        accessing the file.
        """
        return None

    def gid(self):
        """Returns the GID that owns the file.

        The default implementation returns None, in which case the
        VirtualFileFS instance will use the GID of the user currently
        accessing the file.
        """
        return None

"""
A virtual file whose content is either '0' or '1'. You can specify function callbacks,
which will be called when the file's content is changed and which are used to read the
current value.

If the 'callback_on_true' and 'callback_on_false' properties are both None, then this
file is marked read-only and cannot be changed.
"""
class BooleanVirtualFile(SimpleVirtualFile):
    def __init__(self, name, callback_on_read = None, callback_on_true = None, callback_on_false = None):
        debug('BVF init, name: ' + str(name) + ', cor: ' + str(callback_on_read) + ', cot: ' + str(callback_on_true) + ', cof: ' + str(callback_on_false))
        # "2" so as not to override superclass method
        self.callback_on_read2 = callback_on_read

        self.callback_on_true = callback_on_true
        self.callback_on_false = callback_on_false

        coc = self._change
        if callback_on_true == None and callback_on_false == None:
            coc = None

        SimpleVirtualFile.__init__(self, name, self._read, callback_on_change=coc)

        self.value = False

    def _read(self):
        if self.callback_on_read2 != None:
            self.callback_on_read2(self.value)

        if self.value:
            return '1'
        else:
            return '0'

    def _change(self, value):
        debug('booleanVirtualFile: ' + value)
        if value == '0':
            self.value = False
        elif value.strip() == '':
            self.value = False
        else:
            self.value = True

        if self.value:
            if self.callback_on_true != None:
                self.callback_on_true()
        else:
            if self.callback_on_false != None:
                self.callback_on_false()


# Provides a fuse interface to 'virtual' files. This class deliberately
# mimics the FUSE interface, so you can delegate to it from a real FUSE
# filesystem, or use it in some other context.
#
# Virtual files are represented by instances of VirtualFile stored in a dict.
# Virtual files can be made read-only or writeable.
class VirtualFileFS(object):
    # Initialise a new VirtualFileFS.
    # prefix the prefix that the names of all virtual files will have (virtual files always reside in the root directory, /)
    # files an optional list of VirtualFile instances to initalise with
    def __init__(self, prefix, files = []):

        # ensure prefix always starts with '/'
        if prefix.startswith('/'):
            self.prefix = prefix
        else:
            self.prefix = '/' + prefix

        self.files = {}
        for f in files:
            self.files[f.name] = f

    # Add a new VirtualFile to this VirtualFileFS. Any VirtualFile with the
    # same name will be automatically removed before virtual_file is added.
    def add_file(self, virtual_file):
        self.files[virtual_file.name] = virtual_file

    # Remove the virtual file with the given path (or name).
    def remove_file(self, path):
        for n in [ path, self._get_filename(path) ]:
            if self.files.contains(n):
                del self.files[n]
                return

        raise ValueError('path not found: ' + str(path))

    """Returns true if the given path begins with the prefix this VirtualFileFS was created with. (Whether the virtual path exists or not is ignored.)"""
    def is_virtual(self, path):
        return path.startswith(self.prefix)

    """Returns true if the given path exists as a virtual file."""
    def contains(self, path):
        return self.get_file(path) != None

    # Extract the name of a VirtualFile from the given path
    def _get_filename(self, path):
        # self.prefix contains full prefix, including root path element '/'
        debug('get_filename', self.prefix, path)
        if path.startswith(self.prefix):
            return path[len(self.prefix):]
        return None

    # Get the VirtualFile present at path, if there is any
    def    get_file(self, path):
        name = self._get_filename(path)
        debug('get_file', path, name)
        if name != None and name in self.files:
            return self.files[name]

        return None

    # Retrieve attributes of a path in the VirtualFS
    def getattr(self, path):
        debug('vfs getattr', path)
        virtual_file = self.get_file(path)
        debug('vfs getattr', virtual_file)

        if virtual_file == None:
            return E_NO_SUCH_FILE

        result = fuse.Stat()

        if virtual_file.is_read_only():
            result.st_mode = stat.S_IFREG | 0444
        else:
            result.st_mode = stat.S_IFREG | 0644

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
        if virtual_file.uid() == None:
            result.st_uid = context['uid']
        else:
            result.st_uid = virtual_file.uid()

        if virtual_file.gid() == None:
            result.st_gid = context['gid']
        else:
            result.st_gid = virtual_file.gid()

        return result

    def readdir(self, path, offset):
        dirents = []

        # Only add files if we're in the root directory
        if path == '/':
            for k in self.files.keys():
                # strip leading '/' from self.prefix before building filename
                dirents.append(self.prefix[1:] + k)

        # return a generator over the entries in the directory
        debug('vfs readdir', dirents)
        return (fuse.Direntry(r) for r in dirents)

    def open(self, path, flags):
        file = self.get_file(path)

        if file == None:
            return E_NO_SUCH_FILE

        elif file.is_read_only():
            # Only support for 'READ ONLY' flag
            access_flags = os.O_RDONLY | os.O_WRONLY | os.O_RDWR
            if flags & access_flags != os.O_RDONLY:
                return E_PERM_DENIED
            else:
                return 0

        else:
            return 0 # Always succeed

    def read(self, path, size, offset):
        f = self.get_file(path)

        debug('vfs read', path, str(size), str(offset))
        return f.read(size, offset)

    def mknod(self, path, mode, dev):
        # Don't allow creation of new files
        return E_PERM_DENIED

    def unlink(self, path):
        # Don't allow removal of files
        return E_PERM_DENIED

    def write(self, path, buf, offset):
        f = self.get_file(path)
        return f.write(buf, offset)

    def truncate(self, path, size):
        f = self.get_file(path)
        return f.truncate(size)

    def flush(self, path, fh=None):
        f = self.get_file(path)
        return f.flush()

    def release(self, path, fh=None):
        f = self.get_file(path)
        return f.release()

