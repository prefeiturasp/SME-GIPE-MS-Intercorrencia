
from django.contrib import admin
from django.urls import path, include
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView, SpectacularRedocView

BASE = "api-intercorrencias/v1/"  # ou "intercorrencias/api/v1/"

urlpatterns = [
    path(f"{BASE}admin/", admin.site.urls),

    # OpenAPI JSON
    path(f"{BASE}schema/", SpectacularAPIView.as_view(), name="schema"),

    # Swagger / Redoc
    path(f"{BASE}docs/", SpectacularSwaggerView.as_view(url_name="schema"), name="swagger-ui"),
    path(f"{BASE}redoc/", SpectacularRedocView.as_view(url_name="schema"), name="redoc"),

    # App
    path(f"{BASE}", include("intercorrencias.urls")),
]