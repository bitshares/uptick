#!/usr/bin/env python
# -*- coding: utf-8 -*-

from setuptools import setup
import sys

__version__ = "0.2.4"

assert sys.version_info[0] == 3, "Uptick requires Python > 3"

setup(
    name="uptick",
    version=__version__,
    description="Command line tool to interface with the BitShares network",
    long_description=open("README.md").read(),
    download_url="https://github.com/xeroc/uptick/tarball/" + __version__,
    author="Fabian Schuh",
    author_email="Fabian@chainsquad.com",
    maintainer="Fabian Schuh",
    maintainer_email="Fabian@chainsquad.com",
    url="http://uptick.rocks",
    keywords=["bitshares", "library", "api", "rpc", "cli"],
    packages=["uptick", "uptick.apis"],
    classifiers=[
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
    ],
    entry_points={"console_scripts": ["uptick = uptick.cli:main"]},
    install_requires=open("requirements.txt").readlines(),
    setup_requires=["pytest-runner"],
    tests_require=["pytest"],
    include_package_data=True,
)
