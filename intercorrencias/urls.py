from django.urls import path, include
from rest_framework.routers import DefaultRouter

from intercorrencias.api.views.envolvidos_viewset import EnvolvidoViewSet
from intercorrencias.api.views.declarante_viewset import DeclaranteViewSet
from intercorrencias.api.views.tipo_ocorrencia import TipoOcorrenciaViewSet
from intercorrencias.api.views.intercorrencias_viewset import IntercorrenciaDiretorViewSet
from intercorrencias.api.views.verify_intercorrencia_viewset import VerifyIntercorrenciaViewSet
from intercorrencias.api.views.intercorrencias_dre_viewset import IntercorrenciaDreViewSet
from intercorrencias.api.views.intercorrencias_gipe_viewset import IntercorrenciaGipeViewSet


router = DefaultRouter()
# Use um basename válido para os names do reverse():
router.register(r'diretor', IntercorrenciaDiretorViewSet, basename='intercorrencia-diretor')
router.register(r"tipos-ocorrencia", TipoOcorrenciaViewSet, basename="tipo-ocorrencia")
router.register(r"declarante", DeclaranteViewSet, basename="intercorrencia-declarante")
router.register(r"envolvidos", EnvolvidoViewSet, basename="envolvido")
router.register(r"verify-intercorrencia", VerifyIntercorrenciaViewSet, basename="verify-intercorrencia")
router.register(r'dre', IntercorrenciaDreViewSet, basename='intercorrencia-dre')
router.register(r'gipe', IntercorrenciaGipeViewSet, basename='intercorrencia-gipe')

urlpatterns = [path("", include(router.urls))]