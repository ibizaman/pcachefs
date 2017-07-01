#!/usr/bin/python
from setuptools import setup

setup(
    name='pCacheFS',
    version='0.3',
    description='Persistent Caching FUSE Filesystem',
    keywords=['fuse', 'cache'],
    author='Pierre Penninckx',
    author_email='ibizapeanut@gmail.com',
    url='http://code.google.com/p/pcachefs',
    license='Apache 2.0',

    entry_points={
        'console_scripts': 'pcachefs=pcachefs.pcachefs:main',
    },
    packages=['pcachefs'],

    install_requires=['fuse-python'],
    extras_require={
        'dev': ['ipython'],
        'test': ['mockito', 'pytest', 'pylint']
    },
)
