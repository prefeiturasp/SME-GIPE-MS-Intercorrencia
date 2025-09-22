import factory
from django.utils import timezone
from django.contrib.auth.models import User
from intercorrencias.models.intercorrencia import Intercorrencia


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
    sobre_furto_roubo_invasao_depredacao = factory.Faker('boolean')
    unidade_codigo_eol = factory.Faker('bothify', text='??????')
    dre_codigo_eol = factory.Faker('bothify', text='??????')
    user_username = factory.SubFactory(UserFactory)