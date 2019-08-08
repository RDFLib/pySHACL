#!/usr/bin/env python3
# -*- coding: latin-1 -*-
import re
import os
import io
from setuptools import setup


def open_local(paths, mode='r', encoding='utf8'):
    path = os.path.join(
        os.path.abspath(os.path.dirname(__file__)),
        *paths
    )
    return io.open(path, mode, encoding=encoding)


with open_local(['pyshacl', '__init__.py'], encoding='latin1') as fp:
    try:
        version = re.findall(r"^__version__ = '([^']+)'\r?$",
                             fp.read(), re.M)[0]
    except IndexError:
        raise RuntimeError('Unable to determine version.')

with open_local(['README.md']) as readme:
    long_description = readme.read()

with open_local(['requirements.txt']) as req:
    found_requirements = req.read().split("\n")
    dependency_links = []
    requirements = []
    for f in found_requirements:
        if 'git+' in f:
            pkg = f.split('#')[-1]
            dependency_links.append(f.strip() + '-9876543210')
            requirements.append(pkg.replace('egg=', '').rstrip())
        else:
            requirements.append(f.strip())

setup(
    name='pyshacl',
    packages=[
        'pyshacl',
        'pyshacl.constraints', 'pyshacl.constraints.core', 'pyshacl.constraints.sparql',
        'pyshacl.rules', 'pyshacl.rules.triple', 'pyshacl.rules.sparql',
        'pyshacl.inference', 'pyshacl.rdfutil', 'pyshacl.monkey'
    ],
    entry_points={'console_scripts': ['pyshacl = pyshacl.cli:main']},
    package_dir={'pyshacl': './pyshacl'},
    package_data={'pyshacl': ['*.pickle']},
    #data_files=[('pyshacl', ['pyshacl/shacl-shacl.pickle'])],
    version=version,
    description='Python SHACL Validator',
    author='Nicholas Car',
    author_email='nicholas.car@csiro.au',
    url='https://github.com/RDFLib/pySHACL/',
    download_url='https://github.com/RDFLib/pySHACL/'
                    'archive/v{:s}.tar.gz'.format(version),
    license='LICENSE.txt',
    keywords=['Linked Data', 'Semantic Web', 'Python',
              'SHACL', 'Shapes', 'Schema', 'Validate'],
    long_description=long_description,
    long_description_content_type='text/markdown',
    classifiers=[
        'Development Status :: 4 - Beta',
        'Topic :: Utilities',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: Apache Software License',
        'Natural Language :: English',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3 :: Only',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: Implementation :: CPython',
        'Programming Language :: Python :: Implementation :: PyPy',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'Operating System :: OS Independent'
    ],
    install_requires=requirements,
    dependency_links=dependency_links
)
