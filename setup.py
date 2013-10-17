#!/usr/bin/env python

#import distribute_setup
#distribute_setup.use_setuptools()

from setuptools import setup, find_packages

setup(
    name='django-cim-forms',
    version='0.9.9.6',
    author='Allyn Treshansky',
    author_email='allyn.treshansky@noaa.gov',
    packages=find_packages(),
    url='https://github.com/ES-DOC',
    license='NCSA Open Source License, see LICENSE.txt',
    description='CIM Questionnaire',
    long_description=open('README.txt').read(),
    zip_safe=False,
    include_package_data=True,
    install_requires=[
        "Django",
        "distribute",
        "south", 
        "lxml",
    ],
)
