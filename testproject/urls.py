from django.conf.urls.defaults import *

#handler500 = 'djangotoolbox.errorviews.server_error'

urlpatterns = patterns('',

    ('', include('testapp.urls')),


)
