# -*- coding: utf-8 -*-
# Copyright (c) 2002-2013 Infrae. All rights reserved.
# See also LICENSE.txt

from setuptools import setup, find_packages
import os

version = '3.0.4dev'

setup(name='silva.core.conf',
      version=version,
      description="Configuration machinery for Silva CMS",
      long_description=open("README.txt").read() + "\n" +
                       open(os.path.join("docs", "HISTORY.txt")).read(),
      classifiers=[
              "Framework :: Zope2",
              "License :: OSI Approved :: BSD License",
              "Programming Language :: Python",
              "Topic :: Software Development :: Libraries :: Python Modules",
              ],
      keywords='silva core configuration',
      author='Infrae',
      author_email='info@infrae.com',
      license='BSD',
      package_dir={'': 'src'},
      packages=find_packages('src'),
      namespace_packages=['silva', 'silva.core'],
      url='https://github.com/silvacms/silva.core.conf',
      include_package_data=True,
      zip_safe=False,
      install_requires=[
        'five.grok',
        'grokcore.component',
        'grokcore.view',
        'grokcore.viewlet',
        'martian >= 0.11',
        'setuptools',
        'silva.core.interfaces',
        'silva.core.services',
        'silva.translations',
        'zope.container',
        'zope.cachedescriptors',
        'zope.component',
        'zope.configuration',
        'zope.event',
        'zope.interface',
        'zope.lifecycleevent',
        'zope.location',
        'zope.publisher',
        'zope.schema',
        ],
      )
