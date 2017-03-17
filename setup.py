#!/usr/bin/env python

from setuptools import setup
import sys

__VERSION__ = '0.1.1'

assert sys.version_info[0] == 3, "Uptick requires Python > 3"

setup(
    name='uptick',
    version=__VERSION__,
    description='Command line tool to interface with the BitShares network',
    long_description=open('README.md').read(),
    download_url='https://github.com/xeroc/uptick/tarball/' + __VERSION__,
    author='Fabian Schuh',
    author_email='Fabian@chainsquad.com',
    maintainer='Fabian Schuh',
    maintainer_email='Fabian@chainsquad.com',
    url='http://www.github.com/xeroc/uptick',
    keywords=['bitshares', 'library', 'api', 'rpc', 'cli'],
    packages=["uptick"],
    classifiers=[
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 3',
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
    ],
    entry_points={
        'console_scripts': [
            'uptick = uptick.__main__:main',
        ],
    },
    install_requires=[
        "bitshares>=0.0.1",
        "prettytable==0.7.2",
        "click",
        "click-datetime",
    ],
    setup_requires=['pytest-runner'],
    tests_require=['pytest'],
    include_package_data=True,
)
