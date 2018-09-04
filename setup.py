#!/usr/bin/env python
# -*- coding: latin-1 -*-
import codecs
import re
import os
from setuptools import setup


def open_local(paths, mode='r', encoding='utf8'):
    path = os.path.join(
        os.path.abspath(os.path.dirname(__file__)),
        *paths
    )
    return codecs.open(path, mode, encoding)


with open_local(['pyshacl', '__init__.py'], encoding='latin1') as fp:
    try:
        version = re.findall(r"^__version__ = '([^']+)'\r?$",
                             fp.read(), re.M)[0]
    except IndexError:
        raise RuntimeError('Unable to determine version.')

with open_local(['README.md']) as readme:
    long_description = readme.read()

with open_local(['requirements.txt']) as req:
    install_requires = req.read().split("\n")

setup(
    name='pyshacl',
    packages=['pyshacl'],
    version=version,
    description='Python SHACL Validator',
    author='Nicholas Car',
    author_email='nicholas.car@csiro.au',
    url='https://github.com/CSIRO-enviro-informatics/pyshacl',
    download_url='https://github.com/CSIRO-enviro-informatics/'
                    'pyshacl/archive/v{:s}.tar.gz'.format(version),
    license='LICENSE.txt',
    keywords=['Linked Data', 'Semantic Web', 'Flask', 'Python', 'SHACL', 'Schema', 'Validate'],
    long_description=long_description,
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Topic :: Utilities',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: Apache Software License',
        'Natural Language :: English',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: Implementation :: PyPy',
        'Topic :: Software Development :: Libraries :: Python Modules',
    ],
    project_urls={
        'Bug Reports':
            'https://github.com/CSIRO-enviro-informatics/pyshacl/issues',
        'Source': 'https://github.com/CSIRO-enviro-informatics/pyshacl/',
    },
    install_requires=install_requires,
)

