#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os.path
import setuptools
 
def setup():
    with open(os.path.join('src', 'spschedule.py'), 'r') as f:
        for line in f.readlines():
            if 'version' in line:
                try:
                    exec(line)
                    assert(isinstance(version, basestring))
                    break
                except (SyntaxError, AssertionError, NameError):
                    pass
    try:
        assert(isinstance(version, basestring))
    except (AssertionError, NameError):
        version = 'unknown'
        
    setuptools.setup(
        name='spschedule',
        version=version,
        description='StylePage tools: Python Job Scheduling',
        author='mattbornski',
        url='http://github.com/stylepage/spschedule',
        package_dir={'': 'src'},
        py_modules=[
            'spschedule',
        ],
        install_requires=[
            'decorator',
            'python-dateutil==1.5',
#            'spmongo',
        ],
#        dependency_links=[
#            'http://github.com/stylepage/spmongo/tarball/master#egg=spmongo',
#        ],
    )

if __name__ == '__main__':
    setup()