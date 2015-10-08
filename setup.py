# -*- coding: utf-8 -*-
"""
Created on Fri Aug 21 09:32:31 2015

@author: Bas des Tombe, bdestombe@gmail.com
"""

try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

config = {
    'description': 'Flopy script generator',
    'author': 'Bas des Tombe',
    'url': 'URL to get it at.',
    'download_url': 'Where to download it.',
    'author_email': 'bdestombe@gmail.com',
    'version': '0.1',
    'install_requires': ['datetime'],
    'packages': ['scriptgenerator', 'delnam', 'readstresslrc', 'timetools', 'readdiver'],
    'scripts': [],
    'name': 'flopy_test_scripts'
}

setup(**config)
