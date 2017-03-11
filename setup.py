#!/usr/bin/python
from setuptools import setup
from setuptools.command.test import test as TestCommand

from distutils.core import Command

import os
import re
import sys


class CleanCommand(Command):
    user_options = [ ]

    def initialize_options(self):
        self._clean_me = [ ]
        for root, dirs, files in os.walk('.'):
            for f in files:
                if f.endswith('.pyc'):
                    self._clean_me.append(os.path.join(root, f))

    def finalize_options(self):
        pass

    def run(self):
        for clean_me in self._clean_me:
            try:
                os.unlink(clean_me)
            except:
                pass


class PyTest(TestCommand):
    user_options = [('pytest-args=', 'a', "Arguments to pass to py.test")]

    def initialize_options(self):
        TestCommand.initialize_options(self)
        self.pytest_args = []

    def finalize_options(self):
        TestCommand.finalize_options(self)
        self.test_args = []
        self.test_suite = True

    def run_tests(self):
        #import here, cause outside the eggs aren't loaded
        import pytest
        errno = pytest.main(self.pytest_args)
        sys.exit(errno)


setup(name='pCacheFS',
    version='0.2',
    description='Persistent Caching FUSE Filesystem',
    keywords=['fuse', 'cache'],
    author='Jonny Tyers',
    author_email='jonnyt886@gmail.com',
    url='http://code.google.com/p/pcachefs',
    license='Apache 2.0',

    entry_points={
        'console_scripts': 'pcachefs=pcachefs.pcachefs:main',
    },
    packages=['pcachefs'],

    install_requires=['fuse-python'],
    extras_require={
        'test': ['mockito', 'pytest']
    },

    cmdclass = { 'test': PyTest, 'clean': CleanCommand }
)

