from setuptools import setup
import os

setup(
    name = "phlawg",
    version = "0.1.0",
    author = "Ethan Rowe",
    author_email = "ethan@the-rowes.com",
    description = "python logging utilities for transmitting metrics via log streams",
    license = "MIT",
    keywords = "metrics logging configuration setup",
    url = "https://github.com/ethanrowe/python-phlawg",
    packages=['phlawg',
              'phlawg.test',
    ],
    long_description="python logging utilities for transmitting metrics via log streams",
    test_suite='phlawg.test',
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Intended Audience :: System Administrators",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 2.6",
        "Programming Language :: Python :: 2.7",
        "Topic :: Utilities",
    ],
    install_requires=[
        'logstash_formatter',
    ],
    tests_require=[
        'mock',
        'nose',
    ]
)

