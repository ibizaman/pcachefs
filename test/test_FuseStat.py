import unittest
from mock import (Mock, MagicMock)

# FuseStat class tests
class FuseStatTest(unittest.TestCase):

    def setUp(self):
        pass

    def test_init(self):
        from pcachefs import FuseStat

        st_mode = 0775
        st_nlink = 2
        st_size = 3
        st_atime = 45.3
        st_mtime = 46.3
        st_ctime = 41.3

        st_dev = 123
        st_ino = 456

        st_gid = 345
        st_uid = 567

        # create stat object
        TestStat = type("TestStat", (object,), {
            "st_mode": st_mode,
            "st_nlink" : st_nlink,
            "st_size" : st_size,
            "st_atime" : st_atime,
            "st_mtime" : st_mtime,
            "st_ctime" : st_ctime,
            "st_dev" : st_dev,
            "st_ino" : st_ino,
            "st_uid" : st_uid,
            "st_gid" : st_gid
        })

        result = FuseStat(TestStat())

        self.assertEqual(st_mode, result.st_mode)
        self.assertEqual(st_nlink, result.st_nlink)
        self.assertEqual(st_size, result.st_size)
        self.assertEqual(st_atime, result.st_atime)
        self.assertEqual(st_mtime, result.st_mtime)
        self.assertEqual(st_ctime, result.st_ctime)
        self.assertEqual(st_dev, result.st_dev)
        self.assertEqual(st_ino, result.st_ino)
        self.assertEqual(st_uid, result.st_uid)
        self.assertEqual(st_gid, result.st_gid)

