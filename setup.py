from setuptools import setup, find_packages
import os

version = '2.2'

setup(name='silva.core.conf',
      version=version,
      description="Configuration machinery for Silva",
      long_description=open("README.txt").read() + "\n" +
                       open(os.path.join("docs", "HISTORY.txt")).read(),
      classifiers=[
              "Framework :: Zope2",
              "Programming Language :: Python",
              "Topic :: Software Development :: Libraries :: Python Modules",
              ],
      keywords='silva core configuration',
      author='Infrae',
      author_email='info@infrae.com',
      url='',
      license='BSD',
      packages=find_packages(exclude=['ez_setup']),
      namespace_packages=['silva', 'silva.core'],
      include_package_data=True,
      zip_safe=False,
      install_requires=[
          'setuptools',
          'five.grok',
          'martian >= 0.11',
          'zope.interface',
          'zope.schema',
          'zope.configuration',
          'zope.testing',
          ],
      )
