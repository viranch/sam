#!/usr/bin/env python

from distutils.core import setup
import sys, shutil

def do(cmd):
	if len(sys.argv)<2: sys.argv.append(cmd)
	else: sys.argv[1]=cmd
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


do('build')
do('install')
shutil.rmtree('build')

