from django.contrib import admin
from django.urls import include, path
from django.conf import settings
from django.conf.urls import url
from django.views.generic import RedirectView
# from django_registration.backends.one_step import RegistrationView
from django.conf.urls.static import static

urlpatterns = [
	path('steelsensor/', include('steelsensor.urls')),
	path('admin/', admin.site.urls),
	url(r'^accounts/', include('django_registration.backends.one_step.urls')),
	url(r'^accounts/', include('django.contrib.auth.urls')),
	path('accounts/', include('django_registration.backends.activation.urls')),
	url(r'^favicon\.ico$', RedirectView.as_view(url=settings.STATIC_URL + 'images/favicon.ico'))
]

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

