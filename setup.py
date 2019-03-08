#!/usr/bin/env python
import os

from setuptools import setup


base_dir = os.path.dirname(__file__)
about = {}
with open(os.path.join(base_dir, 'bravado_asyncio', '__init__.py')) as f:
    exec(f.read(), about)


setup(
    name='bravado-asyncio',
    version=about['version'],
    license='BSD 3-Clause License',
    description='asyncio powered HTTP client for bravado',
    long_description=open(os.path.join(os.path.dirname(__file__), 'README.rst')).read(),
    author='Stephan Jaensch',
    author_email='sj@sjaensch.org',
    url='https://github.com/sjaensch/bravado-asyncio',
    packages=['bravado_asyncio'],
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'License :: OSI Approved :: BSD License',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
    ],
    install_requires=[
        'aiohttp>=3.3',
        'bravado>=10.3.0',
        'yelp-bytes',
    ],
    extras_require={
        # as recommended by aiohttp, see http://aiohttp.readthedocs.io/en/stable/#library-installation
        'aiohttp_extras': ['aiodns', 'cchardet'],
        'aiobravado': ['aiobravado'],
    },
)
