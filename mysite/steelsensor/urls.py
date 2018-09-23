from django.urls import path
from . import views

urlpatterns = [
	path("", views.index, name='index'),
	path("results", views.results, name='results'),
	path("admintools", views.admintools, name='admintools'),
	path('list', views.list, name='list')
]
