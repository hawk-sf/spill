"""A setuptools based setup module.
See:
https://packaging.python.org/en/latest/distributing.html
https://github.com/pypa/sampleproject
"""

# Always prefer setuptools over distutils
from setuptools import setup, find_packages
# To use a consistent encoding
from codecs import open
from os     import path

here = path.abspath(path.dirname(__file__))

# Get the long description from the README file
with open(path.join(here, 'README.rst'), encoding='utf-8') as f:
    long_description = f.read()

setup(
    name='spill',
    version='0.0.1a',
    description='A utility for generating Flask scaffolding and boilerplate.',
    long_description=long_description,

    url='https://github.com/hawk-sf/spill',
    author='James Hawkins',
    author_email='jameshawkins.sf@gmail.com',

    license='MIT',

    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'Framework :: Flask',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
    ],

    keywords='Flask web development',
    packages=find_packages(exclude=['contrib', 'docs', 'tests']),
    install_requires=['Jinja2'],

    # List additional groups of dependencies here (e.g. development
    # dependencies). You can install these using the following syntax,
    # for example:
    # $ pip install -e .[dev,test]
    # extras_require={
    #     'dev': ['check-manifest'],
    #     'test': ['coverage'],
    # },

    entry_points={
        'console_scripts': [
            'spill=spill:main',
        ],
    },
)
