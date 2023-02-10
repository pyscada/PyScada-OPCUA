# -*- coding: utf-8 -*-
from setuptools import setup, find_packages
import os
from pyscada import opcua


CLASSIFIERS = [
    'Development Status :: 4 - Beta',
    'Environment :: Web Environment',
    'Environment :: Console',
    'Framework :: Django',
    'Intended Audience :: Developers',
    'Intended Audience :: Science/Research',
    'License :: OSI Approved :: GNU General Public License v3 (GPLv3)',
    'Operating System :: POSIX',
    'Operating System :: MacOS :: MacOS X',
    'Programming Language :: Python',
    'Programming Language :: JavaScript',
    'Topic :: Internet :: WWW/HTTP :: Dynamic Content',
    'Topic :: Scientific/Engineering :: Visualization'
]
setup(
    author=opcua.__author__,
    author_email="clavayssiere@univ-pau.fr",
    name='pyscada-opcua',
    version=opcua.__version__,
    description='OPC-UA extension for PyScada a Python and Django based Open Source SCADA System',
    long_description=open(os.path.join(os.path.dirname(__file__), 'README.rst')).read(),
    url='http://www.github.com/clavay/PyScada-OPCUA',
    license='GPL version 3',
    platforms=['OS Independent'],
    classifiers=CLASSIFIERS,
    install_requires=[
        'pyscada>=0.7.1rc5',
        'asyncua',
        'django-nested-admin',
    ],
    packages=find_packages(exclude=["project", "project.*"]),
    include_package_data=True,
    zip_safe=False,
    test_suite='runtests.main',
    namespace_packages=['pyscada']
)
