from django.conf.urls.defaults import *


urlpatterns = patterns('',


url(r'^add_post/$', 'testapp.views.add_post', {},name = 'testapp_add_post'),

url(r'^add_answer/(?P<post_id>\d+)/$', 'testapp.views.add_answer', {},name = 'testapp_add_answer'),

url(r'^posts/$', 'testapp.views.posts', {},name = 'testapp_posts'),

)
