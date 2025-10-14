from rest_framework import serializers

from intercorrencias.services import unidades_service
from intercorrencias.models.intercorrencia import Intercorrencia


class IntercorrenciaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Intercorrencia
        # user_username será preenchido a partir do JWT; não exponha no input
        read_only_fields = ("user_username", "uuid", "criado_em", "atualizado_em")
        fields = (
            "id", "uuid", "data_ocorrencia",
            "unidade_codigo_eol", "dre_codigo_eol",
            "sobre_furto_roubo_invasao_depredacao",
            "user_username", "criado_em", "atualizado_em"
        )

    def validate(self, attrs):
        """
        Validação cruzada opcional chamando o serviço de Unidades:
        - unidade existe?
        - dre existe?
        - a DRE informada corresponde à DRE da unidade?
        """
        codigo_unidade = attrs.get("unidade_codigo_eol")
        codigo_dre = attrs.get("dre_codigo_eol")
        request = self.context.get("request")
        token_header = request.META.get("HTTP_AUTHORIZATION", "")
        token = token_header.split("Bearer ")[1].strip() if "Bearer " in token_header else ""

        # Se preferir tornar opcional (para não acoplar tanto), guarde só os códigos.
        # Aqui mostro validação real via HTTP com timeout curto.
        try:
            u = unidades_service.get_unidade(codigo_unidade)  # { "codigo_eol": "...", "dre_codigo_eol": "..." }
        except unidades_service.ExternalServiceError as e:
            raise serializers.ValidationError({"detail": str(e)})

        if not u or u.get("codigo_eol") != codigo_unidade:
            raise serializers.ValidationError({"detail": "Unidade não encontrada."})

        dre_da_unidade = u.get("dre_codigo_eol") or u.get("dre", {}).get("codigo_eol")
        if codigo_dre and dre_da_unidade and (codigo_dre != dre_da_unidade):
            raise serializers.ValidationError({"detail": "DRE informada não corresponde à DRE da unidade."})

        try:
            r = unidades_service.validar_unidade_usuario(codigo_unidade, token)
            if not r or r.get("detail") != "A unidade pertence ao usuário.":
                raise serializers.ValidationError({"detail": "A unidade não pertence ao usuário autenticado."})
        except unidades_service.ExternalServiceError as e:
            raise serializers.ValidationError({"detail": str(e)})

        return attrs