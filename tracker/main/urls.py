from django.conf.urls import url

from . import views

urlpatterns = [
    url(r'^user/$', views.UserAdd.as_view(), name = 'useradd'),
    url(r'^file/(?P<name>[-\w]+)/$', views.FileAdd.as_view(), name = 'detail'),
    url(ur'^userdelete/(?P<ipd>.*)/$', views.UserDelete.as_view(), name='delete_user'),
]
