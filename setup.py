#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from setuptools import setup
from setuptools import find_packages

setup(name='pubscope',
      version='0.0',
      description='text mining of scientific publications',
      author='Alexandros Goulas',
      author_email='agoulas227@gmail.com',
      classifiers=[
          'Intended Audience :: Science/Research/Any',
          'Programming Language :: Python :: 3.7.3',
      ],
      packages=find_packages()
      )