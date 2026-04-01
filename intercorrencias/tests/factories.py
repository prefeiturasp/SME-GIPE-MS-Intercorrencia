import factory
from django.utils import timezone
from django.contrib.auth.models import User

from intercorrencias.models.declarante import Declarante
from intercorrencias.models.intercorrencia import Intercorrencia
from intercorrencias.models.tipos_ocorrencia import TipoOcorrencia
from intercorrencias.models.pessoa_agressora import PessoaAgressora



class UserFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = User
        django_get_or_create = ('username',)

    username = factory.Faker('user_name')
    email = factory.Faker('email')
    password = factory.Faker('password')
    is_active = True


class IntercorrenciaFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Intercorrencia
        django_get_or_create = ('uuid',)

    uuid = factory.Faker('uuid4')
    data_ocorrencia = factory.LazyFunction(timezone.now)
    fora_horario_funcionamento_ue = False
    sobre_furto_roubo_invasao_depredacao = factory.Faker('boolean')
    unidade_codigo_eol = factory.Faker('bothify', text='??????')
    dre_codigo_eol = factory.Faker('bothify', text='??????')
    user_username = factory.Faker("user_name")
    comunicacao_seguranca_publica = ""
    protocolo_acionado = ""


class TipoOcorrenciaFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = TipoOcorrencia
        django_get_or_create = ("nome",)

    nome = factory.Faker("word")
    ativo = True


class DeclaranteFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Declarante
        django_get_or_create = ("declarante",)

    declarante = factory.Faker("word")
    
    
class PessoaAgressoraFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = PessoaAgressora
        django_get_or_create = ("uuid",)
        
    uuid = factory.Faker('uuid4')
    nome = factory.Faker("name")
    idade = factory.Faker("random_int", min=1, max=100)
    intercorrencia = factory.SubFactory(IntercorrenciaFactory)        