import distribute_setup
distribute_setup.use_setuptools()

from setuptools import setup, find_packages

setup(
    name='django-cim-forms',
    version='0.6',
    author='Allyn Treshansky',
    author_email='allyn.treshansky@noaa.gov',
    packages=find_packages(),
    url='https://github.com/ES-DOC',
    license='NCSA Open Source License, see LICENSE.txt',
    description='CIM Metadata Entry Form',
    long_description=open('README.txt').read(),
    zip_safe=False,
    include_package_data=True,
    install_requires=[
        "Django == 1.4",
        "distribute",
        "south",
        "lxml",
    ],
)


