#!/usr/bin/python
# -*- coding: iso-8859-15 -*-
#
# termiteOS
# Copyright (c) July 2018 Nacho Mas
from codecs import open as codecs_open
from setuptools import setup, find_packages

# Get the long description from the relevant file
with codecs_open('README.rst', encoding='utf-8') as f:
    long_description = f.read()

setup(
    name='termiteOS',
    version='0.0.1',
    description=u"Telescope Operating System",
    long_description=long_description,
    classifiers=[],
    keywords=['robotic','telescope'],
    author=u"Nacho Mas",
    author_email='mas.ignacio@gmail.com',
    url='https://github.com/nachoplus/termiteOS',
    license='GPL3',
    packages=find_packages(exclude=['tests']),
    include_package_data=True,
    zip_safe=False,
    install_requires=['click', 'ephem', 'pigpio', 'pyyaml'],
    extras_require={
        'test': ['pytest'],
    },
    package_data={
        '': ['config.ini', 'config.ini.spec'],
    },
    entry_points="""
      [console_scripts]
      miteLaunch=termiteOS.scripts.cli:launch
      miteConsole=termiteOS.scripts.cli:console
      miteJoy=termiteOS.scripts.cli:joystick
      mitetcpproxy=termiteOS.scripts.cli:tcpproxy
      miteHUB=termiteOS.scripts.cli:hub
      miteTelescope=termiteOS.scripts.cli:telescope
      """)
