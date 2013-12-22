from django.conf.urls import patterns, url

import views

urlpatterns = patterns('',
					   url(r'^$', views.index, name = 'index'),
					   url(r'^home/$', views.home, name = 'home'),
					   url(r'^home/boards/$', views.home_boards, name = 'home_boards'),
					   url(r'^home/streams/$', views.home_streams, name = 'home_streams'),
					   url(r'^home/logout/$', views.home_logout, name='home_logout'),
					   url(r'^signup/$', views.signup, name='signup'),
					   url(r'^upload/$', views.upload, name='upload'),
					   url(r'^addurl/$', views.addurl, name='addurl'),
					   url(r'^pin/(?P<pid>\d+)/$', views.pin, name='pin'),
					   url(r'^picture/$', views.picture, name='picture'),
					   url(r'^search/$', views.search, name='search'),
					   url(r'^result/$', views.result, name='result'),
					   url(r'^board/$', views.board, name='board'),
					   url(r'^user/$', views.user, name='user'),
					   url(r'^follow/$', views.follow, name='follow'),
					   url(r'^friend/$', views.friend, name='friend'),
					   url(r'^req/$', views.req, name='req'),
					   url(r'^profile/$', views.profile, name='profile'),
					   url(r'^setting/$', views.setting, name='setting'),
					   url(r'^about/$', views.about, name='about'),
)

