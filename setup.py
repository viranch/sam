#!/usr/bin/env python

from distutils.core import setup

def do():
	setup(
		name='SAM',
		version='1.0',
		description='Cyberoam Account Manager',
		author='Viranch Mehta / Mohit Kothari',
		author_email='viranch.mehta@gmail.com / mohitrajkothari@gmail.com',
		url='http://www.butbucket.org/viranch/sam',
		packages=['sam'],
		scripts=['scripts/sam'],
	)

import sys

sys.argv.append ('build')
do()
sys.argv[1] = 'install'
do()

