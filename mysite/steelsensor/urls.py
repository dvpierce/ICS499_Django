from django.urls import path
from django.conf.urls import url
from django.conf import settings
from django.views.generic import RedirectView
from . import views

urlpatterns = [
	path("", views.index, name='index'),
	path("results", views.results, name='results'),
	path("browse", views.browse, name='browse'),
	path("dbmanage", views.dbmanage, name='dbmanage'),
	path("dbdelete", views.dbdelete, name='dbdelete'),
	path("deleteImages", views.deleteImages, name='deleteImages'),
	path("deleteImage", views.deleteImage, name='deleteImage'),
	path("browsematches", views.browsematches, name='browsematches'),
	path("admintools", views.admintools, name='admintools'),
]
