from django.urls import path, include
from rest_framework.routers import DefaultRouter

from intercorrencias.api.views.declarante_viewset import DeclaranteViewSet
from intercorrencias.api.views.tipo_ocorrencia import TipoOcorrenciaViewSet
from intercorrencias.api.views.intercorrencias_viewset import IntercorrenciaDiretorViewSet


router = DefaultRouter()
# Use um basename válido para os names do reverse():
router.register(r'diretor', IntercorrenciaDiretorViewSet, basename='intercorrencia-diretor')
router.register(r"tipos-ocorrencia", TipoOcorrenciaViewSet, basename="tipo-ocorrencia")
router.register(r"declarante", DeclaranteViewSet, basename="intercorrencia-declarante")

urlpatterns = [path("", include(router.urls))]