from setuptools import setup, find_packages
import codecs
import django_redis_engine as distmeta


CLASSIFIERS = [
    'Intended Audience :: Developers',
    'License :: OSI Approved :: BSD License',
    'Programming Language :: Python',
    'Topic :: Internet',
    'Topic :: Database',
    'Topic :: Software Development :: Libraries :: Python Modules',
    'Operating System :: OS Independent',
]

for ver in ['2', '2.4', '2.5', '2.6', '2.7']:
    CLASSIFIERS.append('Programming Language :: Python :: %s' % ver)


setup(
    name='django-redis-engine',
    version='.'.join(map(str, distmeta.__version__)),
    author=distmeta.__author__,
    author_email=distmeta.__contact__,
    license='2-clause BSD',
    description= "A Redis backend.",
    long_description=codecs.open('README.rst', 'r', 'utf-8').read(),

    platforms=['any'],
    install_requires=['django>=1.2', 'djangotoolbox'],

    packages=find_packages(exclude=['testproject']),
    include_package_data=True,
    classifiers=CLASSIFIERS,
)
