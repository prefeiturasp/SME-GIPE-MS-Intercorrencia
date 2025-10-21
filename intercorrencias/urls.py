from django.urls import path, include
from rest_framework.routers import DefaultRouter
from intercorrencias.api.views.intercorrencias_viewset import IntercorrenciaViewSet
from intercorrencias.api.views.tipo_ocorrencia import TipoOcorrenciaViewSet


router = DefaultRouter()
# Use um basename válido para os names do reverse():
router.register(r"intercorrencias", IntercorrenciaViewSet, basename="intercorrencia")
router.register(r"tipos-ocorrencia", TipoOcorrenciaViewSet, basename="tipo-ocorrencia")


urlpatterns = [path("", include(router.urls))]
