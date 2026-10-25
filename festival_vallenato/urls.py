from django.contrib import admin
from django.urls import include, path

from votaciones.urls import panel_patterns, public_patterns


urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include(public_patterns)),
    path("panel/", include(panel_patterns)),
]
