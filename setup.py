#!/usr/bin/env python

from distutils.core import setup

setup(name='eagle_database',
      version='2022.1',
      description='Package used to read EAGLE-like Subfind databases',
      author='Victor Forouhar Moreno',
      author_email='victor.j.forouhar@durham.ac.uk',
      url='https://github.com/VictorForouhar/eagle_database',
      packages=['eagle_database'],
      install_requires=[
            'astropy>=4.1',
            'h5py==3.1.0',
            'matplotlib>=3.3.4',
            'numpy>=1.19.5'
      ],
     )