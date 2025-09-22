from django.urls import path, include
from rest_framework.routers import DefaultRouter
from intercorrencias.api.views.intercorrencias_viewset import IntercorrenciaViewSet

router = DefaultRouter()
# Use um basename válido para os names do reverse():
router.register(r"intercorrencias", IntercorrenciaViewSet, basename="intercorrencia")

urlpatterns = [path("", include(router.urls))]
