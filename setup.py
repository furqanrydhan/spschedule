#!/usr/bin/env python
# -*- coding: utf-8 -*-

import setuptools
 
def setup():
    setuptools.setup(
        name='spschedule',
        version='0.1',
        description='StylePage tools: Python Job Scheduling',
        author='mattbornski',
        url='http://github.com/stylepage/spschedule',
        package_dir={'': 'src'},
        py_modules=[
            'spschedule',
        ],
        install_requires=[
            'decorator',
            'python-dateutil',
            'spmongo',
        ],
        dependency_links=[
            'http://github.com/stylepage/spmongo/tarball/master#egg=stylepage-spmongo',
        ],
    )

if __name__ == '__main__':
    setup()