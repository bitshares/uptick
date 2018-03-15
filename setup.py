#!/usr/bin/env python

from setuptools import setup
import sys

__VERSION__ = '0.1.7'

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
    url='http://uptick.rocks',
    keywords=['bitshares', 'library', 'api', 'rpc', 'cli'],
    packages=["uptick", "uptick.apis"],
    classifiers=[
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 3',
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
    ],
    entry_points={
        'console_scripts': [
            'uptick = uptick.cli:main'
        ],
    },
    install_requires=[
        "bitshares>=0.1.12",
        "prettytable",
        "click",
        "click-datetime",
        "colorama",
        "tqdm",
        "pyyaml"
    ],
    setup_requires=['pytest-runner'],
    tests_require=['pytest'],
    include_package_data=True,
)
