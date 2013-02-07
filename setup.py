#!/usr/bin/python 
from distutils.core import setup

from distutils.core import Command
from unittest import TextTestRunner, TestLoader

import fnmatch
import os
import os.path
import re

# Custom test command for distutils.
# TestCommand based on http://da44en.wordpress.com/2002/11/22/using-distutils/
# Filter code based on http://stackoverflow.com/a/5141829/1432488
class TestCommand(Command):
	user_options = [ ]

	def initialize_options(self):
		self._dir = os.getcwd()

	def finalize_options(self):
		pass

	def run(self):
		'''
		Finds all the tests modules in tests/, and runs them.
		'''
		testfiles = []

		includes = ['*_test.py', '*_tests.py'] # for files only
		excludes = ['__init__.py', 'setup.py'] # for dirs and files

		# transform glob patterns to regular expressions
		includes = r'|'.join([fnmatch.translate(x) for x in includes])
		excludes = r'|'.join([fnmatch.translate(x) for x in excludes]) or r'$.'

		for root, dirs, files in os.walk(self._dir):

			# exclude dirs
			dirs[:] = [d for d in dirs if not d == 'build']

			# exclude/include files
			#files = [os.path.join(root, f) for f in files]

			files = [f for f in files if not re.match(excludes, f)]
			files = [f for f in files if re.match(includes, f)]

			for fname in files:
				pypath = root[len(self._dir)+1:]

				if pypath != '':
					pyname = fname[0:-3] # convert filename ('file.py') to python mod name ('file')

					# convert path to python module ('path/to') to python package name ('path.to')
					pypackage = pypath.replace('/', '.')

					# join pypackage to pname ('path.to.file') and add to list of test modules
					testfiles.append('.'.join( [pypackage, pyname] ))

		tests = TestLoader().loadTestsFromNames(testfiles)
		t = TextTestRunner(verbosity = 2)
		t.run(tests)


setup(name='pCacheFS',
	version='0.2',
	description='Persistent Caching FUSE Filesystem',
	keywords=['fuse', 'cache'],
	author='Jonny Tyers',
	author_email='jonnyt886@gmail.com',
	url='http://code.google.com/p/pcachefs',
	license='Apache 2.0',

	scripts=['scripts/pcachefs'],
	packages=['pcachefs'],

	cmdclass = { 'test': TestCommand } #, 'clean': CleanCommand }
)

