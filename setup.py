# -*- encoding: utf-8 -*-
# This is <setup.py>
# ----------------------------------------------------------------------------
#
# Copyright (c) 2018 by Swiss Seismological Service (SED, ETHZ)
#
# setup.py
#
# REVISIONS and CHANGES
#    2018/01/24   V1.0   Daniel Armbruster (damb)
#
# ============================================================================
"""
setup.py for ramsis.datamodel

.. note:

    Packaging is performed by means of `Python namespace packages
    <https://packaging.python.org/guides/packaging-namespace-packages/>`_
"""

import sys
from setuptools import setup, find_packages


if sys.version_info[:2] < (3, 6):
    raise RuntimeError("Python version >= 3.6 required.")

_authors = [
    'Lukas Heiniger',
    'Walsh Alexander',
    'Daniel Armbruster']
_authors_email = [
    'lukas.heiniger@sed.ethz.ch',
    'daniel.armbruster@sed.ethz.ch']

_install_requires= [
    "sqlalchemy>=1.2",
    "geoalchemy2>=0.5",]

_extras_require = {'doc': [
    "sphinx==1.4.1",
    "sphinx-rtd-theme==0.1.9", ]}

_tests_require = [
    'pytest>=3.4',]



setup(
    name='ramsis.datamodel',
    # TODO(damb): Provide version string globally
    version='0.1',
    author=' (SED, ETHZ),'.join(_authors),
    author_email=', '.join(_authors_email),
    description=('Real Time Risk Assessment and Mitigation for Induced'
                 'Seismicity. '),
    license='AGPL',
    keywords=[
        'induced seismicity',
        'risk',
        'risk assessment',
        'risk mitigation',
        'realtime',
        'seismology'],
    url='https://gitlab.seismo.ethz.ch/indu/ramsis.datamodel.git',
    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'Environment :: Console',
        'Environment :: X11 Applications :: Qt',
        'Intended Audience :: Science/Research',
        ('License :: OSI Approved :: GNU Affero '
            'General Public License v3 or later (AGPLv3+)'),
        'Operating System :: POSIX :: Linux',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: Implementation :: CPython',
        'Topic :: Scientific/Engineering', ],
    platforms=['Linux', ],
    packages=['ramsis.' + pkg for pkg in find_packages(where='ramsis')],
    install_requires=_install_requires,
    extras_require=_extras_require,
    tests_require=_tests_require,
    include_package_data=True,
    zip_safe=False,
    # TODO(damb): test_suite=unittest.TestCase
    # TODO(damb): ramsis does not necessarily depend on doc extras flag
)

# ----- END OF setup.py -----
