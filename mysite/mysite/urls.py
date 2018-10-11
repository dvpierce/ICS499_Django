from django.contrib import admin
from django.urls import include, path
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
	path('steelsensor/', include('steelsensor.urls')),
	path('admin/', admin.site.urls),
	path('accounts/', include('django.contrib.auth.urls')),
	path('accounts/', include('django_registration.backends.activation.urls')),
]

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

