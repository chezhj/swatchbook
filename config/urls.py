from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    # Path comes from settings.ADMIN_URL (env-configurable); default "admin/".
    path(settings.ADMIN_URL, admin.site.urls),
    path("api/", include("config.api_urls")),
    path("", include("web.urls")),
]

if settings.DEBUG:
    # Uploaded photos; in production the web server serves MEDIA_ROOT directly.
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
