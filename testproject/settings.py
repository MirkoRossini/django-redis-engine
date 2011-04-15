# Initialize App Engine and import the default settings (DB backend, etc.).
# If you want to use a different backend you have to remove all occurences
# of "djangoappengine" from this file.
#from djangoappengine.settings_base import *
import django.conf.global_settings as DEFAULT_SETTINGS
import os

SECRET_KEY = '=r-$b*8hglm+858&9t043hlm6-&6-3d3vfc4((7yd0dbrakhvi'

DATABASES = {
    'default': {
        'ENGINE': 'django_redis_engine',
        'NAME': '',
        'USER': '',
        'PASSWORD': '',
        'HOST': 'localhost',
        'PORT': 6379,
       
    }
}


DBINDEXER_SITECONF = 'dbindexes'

DBINDEXER_BACKENDS = (
    'dbindexer.backends.FKNullFix',
    'dbindexer.backends.BaseResolver',
    'dbindexer.backends.InMemoryJOINResolver',
)



INSTALLED_APPS = (
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'djangotoolbox',
    'testapp',

)

# This test runner captures stdout and associates tracebacks with their
# corresponding output. Helps a lot with print-debugging.
TEST_RUNNER = 'djangotoolbox.test.CapturingTestSuiteRunner'

TIME_ZONE = 'America/Chicago'

LANGUAGE_CODE = 'en-us'

ADMIN_MEDIA_PREFIX = '/media/admin/'


MEDIA_URL = '/media/'
TEMPLATE_DIRS = (
     os.path.join(os.path.dirname(__file__), 'templates'),
     os.path.join(os.path.dirname(__file__), 'unimia/templates'),

)


REDIS_SETTINGS_MODULES = ('testapp.redis_settings',)


ROOT_URLCONF = 'urls'

SITE_ID = 1

#GAE_SETTINGS_MODULES = (
#    'unimia.gae_settings',
#)

TEMPLATE_CONTEXT_PROCESSORS = DEFAULT_SETTINGS.TEMPLATE_CONTEXT_PROCESSORS + (
	'django.core.context_processors.request',
)

MIDDLEWARE_CLASSES = (
 'django.middleware.common.CommonMiddleware',
 'django.contrib.sessions.middleware.SessionMiddleware',
 'django.middleware.csrf.CsrfViewMiddleware',
 'django.contrib.auth.middleware.AuthenticationMiddleware',
 'dbindexer.middleware.DBIndexerMiddleware',
)   
#) + DEFAULT_SETTINGS.MIDDLEWARE_CLASSES


# Activate django-dbindexer if available
try:
	import dbindexer
	DATABASES['native'] = DATABASES['default']
	DATABASES['default'] = {'ENGINE': 'dbindexer', 'TARGET': 'native'}
	INSTALLED_APPS += ('dbindexer',)
except ImportError,e:
	import traceback
	traceback.print_exc(20)


DEBUG = True
