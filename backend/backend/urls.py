"""backend URL Configuration"""
from django.contrib import admin
from django.urls import path, include
from rest_framework.schemas import get_schema_view
from django.views.generic import TemplateView

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("simpleMusicService.urls")),

    path("openapi/", get_schema_view(title="Simple music service"), name="openapi_schema"),
    path("docs/", TemplateView.as_view(template_name="documentation.html",
                                       extra_context={"schema_url": "openapi_schema"}),
         name="swagger-ui"),
]
