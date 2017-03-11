Introduction
============
pCacheFS provides a simple caching layer for other filesystems.
This makes slow, remote filesystems seem very fast to access.
Moreover, the cache does not disappear when you start or stop pCacheFS or if you reboot your computer - it is **persistent**.

It is designed for caching large amounts of data on remote filesystems that don't change very much,
such as movie or music libraries.

Disclaimer
==========
The code originates from http://code.google.com/p/pcachefs/. The original copyright notice is:
```
Copyright 2012 Jonny Tyers
pCacheFS is license under Apache License 2.0 - see the LICENSE file for details.
```

Key features
============
* You can choose where to store your persistent cache - local harddisk, ramdisk filesystem, etc.
* Cache contents of any other filesystem, whether local or remote (even other FUSE filesystems such as [sshfs](http://fuse.sourceforge.net/sshfs.html)).
* pCacheFS caches data as it is read, and only the bits that are read.

Currently, pCacheFS mounts are **read-only** - writes are not (yet) supported.

Example
=======
Suppose I have a slow network filesystem mounted at `/remote`.

```sh
$ ls /remote
hugefile1 hugefile2 dir3
```

If I want to use another local directory as a persistent cache for this filesystem, I can use a pCacheFS mount:

```sh
$ pcachefs.py -c /cache -t /remote /remote-cached
```

I will now have a mirror of `/remote` at `/remote-cached`.

```sh
$ ls /remote-cached
hugefile1 hugefile2 dir3
```

This is our caching filesystem. We can read files from this filesystem and their contents will be cached in files in `/cache`. (As well as file contents, metadata and directory listings are also cached.)

So, the first time I access hugefile1 it will be as slow as it would have been via `/remote`:

```sh
$ cat /remote-cached/hugefile1
```

But, access `hugefile1` again and you'll notice a big speed improvement.
This is because the data isn't actually being read from the slow filesystem at `/remote`,
it is being read from `/cache`.

Note that in order to get the benefit of the cache you must access files via your
pCacheFS mountpoint (`/remote-cached` above, but this can be anything you like).
Accessing the target filesystem directly (via `/remote` above) will not see any speed gains
as you are bypassing pCacheFS.

Install
=======
pCacheFS requires FUSE and the FUSE Python bindings to be installed on your system.

Ubuntu users should be able to use this command to install:
```
$ sudo apt-get install fuse python-fuse
```

Then you can use pip and virtualenv to install dependencies.
```
$ virtualenv .venv2.7 -p python2.7
$ source .venv2.7/bin/activate
$ pip install -e '.[dev,test]'
```
