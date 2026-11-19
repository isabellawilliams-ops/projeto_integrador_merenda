from decimal import Decimal
from django.db import transaction

from .models import (
    CalculoDiario,
    Cardapio,
    FrequenciaDiaria,
    ItemCalculo,
    UnidadeMedida,
)


class CalculoService:
    @staticmethod
    def converter_unidade_amigavel(quantidade: Decimal, unidade: str) -> tuple[Decimal, str]:
        """
        Ajusta a unidade para leitura facilitada no refeitório:
        - g para kg quando quantidade >= 1000g (1000g = 1kg)
        - ml para L quando quantidade >= 1000ml (1000ml = 1L)
        """
        if unidade == UnidadeMedida.GRAMA and quantidade >= Decimal('1000'):
            return (quantidade / Decimal('1000')).quantize(Decimal('0.0001')), UnidadeMedida.QUILOGRAMA
        elif unidade == UnidadeMedida.MILILITRO and quantidade >= Decimal('1000'):
            return (quantidade / Decimal('1000')).quantize(Decimal('0.0001')), UnidadeMedida.LITRO
        return quantidade.quantize(Decimal('0.0001')), unidade

    @classmethod
    @transaction.atomic
    def processar_calculo(
        cls,
        cardapio: Cardapio,
        frequencia: FrequenciaDiaria,
        usuario,
        data_calculo=None,
        forcar_recalculo=False
    ) -> CalculoDiario:
        """
        Calcula a quantidade proporcional de ingredientes:
        Qtd Calculada = Total Estudantes * Qtd Padrão * Fator de Rendimento
        Consolida insumos comuns entre preparações do mesmo cardápio.
        """
        if data_calculo is None:
            data_calculo = frequencia.data_refeicao

        calculo = CalculoDiario.objects.filter(
            cardapio=cardapio,
            frequencia=frequencia,
            data_calculo=data_calculo
        ).first()

        if not calculo:
            calculo = CalculoDiario.objects.create(
                cardapio=cardapio,
                frequencia=frequencia,
                usuario_responsavel=usuario,
                data_calculo=data_calculo,
                conferido=False
            )
        elif forcar_recalculo:
            calculo.usuario_responsavel = usuario
            calculo.save()

        total_alunos = Decimal(frequencia.total_estudantes_presentes)
        totais_ingredientes = {}

        # Itera por todas as preparações/fichas técnicas do cardápio
        for receita in cardapio.receitas.all():
            fator = receita.fator_rendimento or Decimal('1.000')
            for item in receita.itens.all():
                qtd_padrao = item.quantidade_padrao
                qtd_calculada_item = total_alunos * qtd_padrao * fator
                ing_id = item.ingrediente_id

                if ing_id not in totais_ingredientes:
                    totais_ingredientes[ing_id] = {
                        'ingrediente': item.ingrediente,
                        'quantidade': Decimal('0'),
                        'unidade': item.unidade_medida,
                    }

                # Coerência de unidades de mesma grandeza
                un_item = item.unidade_medida
                un_acumulada = totais_ingredientes[ing_id]['unidade']

                if un_item == UnidadeMedida.GRAMA and un_acumulada == UnidadeMedida.QUILOGRAMA:
                    totais_ingredientes[ing_id]['quantidade'] += (qtd_calculada_item / Decimal('1000'))
                elif un_item == UnidadeMedida.QUILOGRAMA and un_acumulada == UnidadeMedida.GRAMA:
                    totais_ingredientes[ing_id]['quantidade'] = (
                        totais_ingredientes[ing_id]['quantidade'] / Decimal('1000')
                    ) + qtd_calculada_item
                    totais_ingredientes[ing_id]['unidade'] = UnidadeMedida.QUILOGRAMA
                elif un_item == UnidadeMedida.MILILITRO and un_acumulada == UnidadeMedida.LITRO:
                    totais_ingredientes[ing_id]['quantidade'] += (qtd_calculada_item / Decimal('1000'))
                elif un_item == UnidadeMedida.LITRO and un_acumulada == UnidadeMedida.MILILITRO:
                    totais_ingredientes[ing_id]['quantidade'] = (
                        totais_ingredientes[ing_id]['quantidade'] / Decimal('1000')
                    ) + qtd_calculada_item
                    totais_ingredientes[ing_id]['unidade'] = UnidadeMedida.LITRO
                else:
                    totais_ingredientes[ing_id]['quantidade'] += qtd_calculada_item

        ingredientes_processados = set()
        for ing_id, info in totais_ingredientes.items():
            qtd_formatada, un_formatada = cls.converter_unidade_amigavel(info['quantidade'], info['unidade'])

            item_existente = ItemCalculo.objects.filter(calculo=calculo, ingrediente_id=ing_id).first()
            if item_existente:
                item_existente.quantidade_calculada = qtd_formatada
                item_existente.unidade_medida = un_formatada
                item_existente.save()
            else:
                ItemCalculo.objects.create(
                    calculo=calculo,
                    ingrediente_id=ing_id,
                    quantidade_calculada=qtd_formatada,
                    unidade_medida=un_formatada,
                )
            ingredientes_processados.add(ing_id)

        # Remove itens que eventualmente foram excluídos das fichas técnicas
        calculo.itens.exclude(ingrediente_id__in=ingredientes_processados).delete()
        return calculo
