#!/usr/bin/env python
"""ESMValTool installation script."""
# This script only installs dependencies available on PyPI
#
# Dependencies that need to be installed some other way (e.g. conda):
# - ncl
# - iris
# - python-stratify

import os
import re
import sys
from pathlib import Path

from setuptools import Command, setup

from esmvalcore._version import __version__

PACKAGES = [
    'esmvalcore',
]

REQUIREMENTS = {
    # Installation script (this file) dependencies
    'setup': [
        'pytest-runner',
        'setuptools_scm',
    ],
    # Installation dependencies
    # Use with pip install . to install from source
    'install': [
        'cf-units',
        'dask[array]',
        'fiona',
        'fire',
        'nc-time-axis',  # needed by iris.plot
        'netCDF4',
        'numba',
        'numpy',
        'prov[dot]',
        'psutil',
        'pyyaml',
        'scitools-iris>=2.2',
        'shapely[vectorized]',
        'stratify',
        'yamale',
    ],
    # Test dependencies
    # Execute 'python setup.py test' to run tests
    'test': [
        'pytest>=3.9',
        'pytest-cov',
        'pytest-env',
        'pytest-flake8',
        'pytest-html!=2.1.0',
        'pytest-metadata>=1.5.1',
        'pytest-mock',
    ],
    # Development dependencies
    # Use pip install -e .[develop] to install in development mode
    'develop': [
        'autodocsumm',
        'codespell',
        'isort',
        'prospector[with_pyroma]!=1.1.6.3,!=1.1.6.4',
        'sphinx>2',
        'sphinx_rtd_theme',
        'vmprof',
        'yamllint',
        'yapf',
    ],
}


def read_authors(citation_file):
    """Read the list of authors from .cff file."""
    authors = re.findall(
        r'family-names: (.*)$\s*given-names: (.*)',
        Path(citation_file).read_text(),
        re.MULTILINE,
    )
    return ', '.join(' '.join(author[::-1]) for author in authors)


def discover_python_files(paths, ignore):
    """Discover Python files."""
    def _ignore(path):
        """Return True if `path` should be ignored, False otherwise."""
        return any(re.match(pattern, path) for pattern in ignore)

    for path in sorted(set(paths)):
        for root, _, files in os.walk(path):
            if _ignore(path):
                continue
            for filename in files:
                filename = os.path.join(root, filename)
                if (filename.lower().endswith('.py')
                        and not _ignore(filename)):
                    yield filename


class CustomCommand(Command):
    """Custom Command class."""

    def install_deps_temp(self):
        """Try to temporarily install packages needed to run the command."""
        if self.distribution.install_requires:
            self.distribution.fetch_build_eggs(
                self.distribution.install_requires)
        if self.distribution.tests_require:
            self.distribution.fetch_build_eggs(self.distribution.tests_require)


class RunLinter(CustomCommand):
    """Class to run a linter and generate reports."""

    user_options = []

    def initialize_options(self):
        """Do nothing."""

    def finalize_options(self):
        """Do nothing."""

    def run(self):
        """Run prospector and generate a report."""
        check_paths = PACKAGES + [
            'setup.py',
            'tests',
        ]
        ignore = [
            'doc/',
        ]

        # try to install missing dependencies and import prospector
        try:
            from prospector.run import main
        except ImportError:
            # try to install and then import
            self.distribution.fetch_build_eggs(['prospector[with_pyroma]'])
            from prospector.run import main

        self.install_deps_temp()

        # run linter

        # change working directory to package root
        package_root = os.path.abspath(os.path.dirname(__file__))
        os.chdir(package_root)

        # write command line
        files = discover_python_files(check_paths, ignore)
        sys.argv = ['prospector']
        sys.argv.extend(files)

        # run prospector
        errno = main()

        sys.exit(errno)


setup(
    name='ESMValCore',
    version=__version__,
    author=read_authors('CITATION.cff'),
    description='Earth System Models eValuation Tool Core',
    long_description=Path('README.md').read_text(),
    long_description_content_type='text/markdown',
    url='https://www.esmvaltool.org',
    download_url='https://github.com/ESMValGroup/ESMValCore',
    license='Apache License, Version 2.0',
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Environment :: Console',
        'Intended Audience :: Developers',
        'Intended Audience :: Science/Research',
        'License :: OSI Approved :: Apache Software License',
        'Natural Language :: English',
        'Operating System :: POSIX :: Linux',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Topic :: Scientific/Engineering',
        'Topic :: Scientific/Engineering :: Atmospheric Science',
        'Topic :: Scientific/Engineering :: GIS',
        'Topic :: Scientific/Engineering :: Hydrology',
        'Topic :: Scientific/Engineering :: Physics',
    ],
    packages=PACKAGES,
    # Include all version controlled files
    include_package_data=True,
    setup_requires=REQUIREMENTS['setup'],
    install_requires=REQUIREMENTS['install'],
    tests_require=REQUIREMENTS['test'],
    extras_require={
        'develop': REQUIREMENTS['develop'] + REQUIREMENTS['test'],
    },
    entry_points={
        'console_scripts': [
            'esmvaltool = esmvalcore._main:run',
        ],
    },
    cmdclass={
        #         'test': RunTests,
        'lint': RunLinter,
    },
    zip_safe=False,
)
