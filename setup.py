#!/usr/bin/env python
from setuptools import setup, find_packages
from os import path
import sys

setup(
    name='princeton-u19-data-viewer',
    version='0.0.0',
    description="Data Viewer for Princeton Data pipeline",
    author='Shan Shen',
    author_email='shanshen@vathes.com',
    license="GNU LGPL",
    keywords='database viewer',
    packages=find_packages(exclude=['contrib', 'docs', 'tests*']),
    install_requires=['datajoint >= 0.12', 'bokeh']
)
