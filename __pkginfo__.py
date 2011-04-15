#!/usr/bin/env python
# -*- coding: utf-8 -*-
import codecs
import django_redis_engine as distmeta

distname = 'django_redis_engine'
numversion = distmeta.__version__
version = '.'.join(map(str, numversion))
license = '2-clause BSD'
author = distmeta.__author__
author_email = distmeta.__contact__

short_desc = "A Redis django db backend."
long_desc = codecs.open('README.rst', 'r', 'utf-8').read()

install_requires = [ 'django>=1.2', 'djangotoolbox']
pyversions = ['2', '2.4', '2.5', '2.6', '2.7']
docformat = distmeta.__docformat__
include_dirs = []
