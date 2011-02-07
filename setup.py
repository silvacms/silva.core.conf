# -*- coding: utf-8 -*-
# Copyright (c) 2002-2010 Infrae. All rights reserved.
# See also LICENSE.txt
# $Id$

from setuptools import setup, find_packages
import os

version = '2.3.3'

setup(name='silva.core.conf',
      version=version,
      description="Configuration machinery for Silva",
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
      url='http://infrae.com/products/silva',
      include_package_data=True,
      zip_safe=False,
      install_requires=[
        'Products.FileSystemSite',
        'five.grok',
        'grokcore.component',
        'grokcore.view',
        'grokcore.viewlet',
        'martian >= 0.11',
        'setuptools',
        'silva.core.interfaces',
        'silva.core.services',
        'silva.translations',
        'zope.cachedescriptors',
        'zope.component',
        'zope.configuration',
        'zope.event',
        'zope.interface',
        'zope.lifecycleevent',
        'zope.location',
        'zope.schema',
        'zope.testing',
        ],
      )
