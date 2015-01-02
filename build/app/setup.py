#!/usr/bin/env python
# -*- coding: utf-8 -*-
""" Setup file for app package """

from distutils.core import setup
from os import listdir
from os.path import abspath, dirname, isdir, isfile, join


dir=dirname(abspath(__file__))
description = open(join(dir,'description')).read()
readme = open(join(dir,'README.rst')).read()

def find_packages(where='.', exclude=["tests"]):
    out = []
    stack = [(where, '')]
    while stack:
        where, prefix = stack.pop(0)
        for name in listdir(where):
            fn = join(where, name)
            if ('.' not in name and isdir(fn) and
                isfile(join(fn,'__init__.py'))):
                out.append(prefix+name)
                stack.append((fn,prefix+name+'.'))
    for pat in (exclude)+['ez_setup', 'distribute_setup']:
        from fnmatch import fnmatchcase
        out = [item for item in out if not fnmatchcase(item, pat)]
    return out

setup(name='app',
      version='0.0.2',
      description=description,
      long_description=readme,
      author='cancerhermit',
      author_email='cancerhermit@gmail.com',
      url='http://github.com/cancerhermit/PyApp/',
      packages = find_packages("."),
      install_requires=[
        "appscript",
        "envoy",
        "osascript",
      ],
      platforms = ["MacOS X"],
      keywords="Mac OS Application AppleScript appscript",
      classifiers=(
          'License :: OSI Approved :: GNU General Public License (GPL)',
          'Environment :: Console',
          'Environment :: MacOS X',

          'Natural Language :: English',

          'Operating System :: MacOS',

          'Programming Language :: Python',

          'Topic :: Software Development :: Libraries :: Python Modules',
          'Topic :: Utilities'
        ),
      license="GPL"
     )