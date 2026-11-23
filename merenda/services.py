from decimal import Decimal
from django.core.exceptions import ValidationError
from django.db import transaction

from .models import (
    BaseCalculo,
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
        Ajusta a unidade para leitura facilitada no refeitório (Regra 3.2 do AGENTS.md):
        - g para kg quando quantidade >= 1000g (1000g = 1kg)
        - kg para g quando quantidade < 1kg e > 0g (ex: 0.8kg = 800g para itens em pequenas dosagens)
        - ml para L quando quantidade >= 1000ml (1000ml = 1L)
        - L para ml quando quantidade < 1L e > 0L (ex: 0.5L = 500ml)
        - un permanece inalterada
        """
        if unidade == UnidadeMedida.GRAMA and quantidade >= Decimal('1000'):
            return (quantidade / Decimal('1000')).quantize(Decimal('0.0001')), UnidadeMedida.QUILOGRAMA
        elif unidade == UnidadeMedida.QUILOGRAMA and Decimal('0') < quantidade < Decimal('1'):
            return (quantidade * Decimal('1000')).quantize(Decimal('0.0001')), UnidadeMedida.GRAMA
        elif unidade == UnidadeMedida.MILILITRO and quantidade >= Decimal('1000'):
            return (quantidade / Decimal('1000')).quantize(Decimal('0.0001')), UnidadeMedida.LITRO
        elif unidade == UnidadeMedida.LITRO and Decimal('0') < quantidade < Decimal('1'):
            return (quantidade * Decimal('1000')).quantize(Decimal('0.0001')), UnidadeMedida.MILILITRO
        return quantidade.quantize(Decimal('0.0001')), unidade

    @staticmethod
    def normalizar_para_padrao(quantidade: Decimal, unidade: str) -> tuple[Decimal, str]:
        """
        Normaliza grandezas compatíveis para base comum (kg para massa, L para volume).
        Evita misturar grandezas incompatíveis (ex: massa com volume sem densidade).
        """
        if unidade == UnidadeMedida.GRAMA:
            return quantidade / Decimal('1000'), UnidadeMedida.QUILOGRAMA
        elif unidade == UnidadeMedida.MILILITRO:
            return quantidade / Decimal('1000'), UnidadeMedida.LITRO
        return quantidade, unidade

    @classmethod
    def calcular_quantidade_item(
        cls,
        item,
        total_alunos: Decimal,
        fator_rendimento: Decimal
    ) -> Decimal:
        """
        Aplica a fórmula do cálculo proporcional conforme a Base de Cálculo:
        - por_aluno: Total Alunos * Qtd Padrão * Fator de Rendimento
        - por_porcao: Total Alunos * Qtd Padrão * Fator de Rendimento (1 porção consumida por aluno)
        - por_lote: Caso definido em bateladas/lotes (arredondamento proporcional)
        """
        qtd_padrao = item.quantidade_padrao
        base = getattr(item, 'base_calculo', BaseCalculo.POR_ALUNO)

        if base in (BaseCalculo.POR_ALUNO, BaseCalculo.POR_PORCAO):
            return total_alunos * qtd_padrao * fator_rendimento
        elif base == BaseCalculo.POR_LOTE:
            # Em receitas por lote, a quantidade padrão é consumida em escala com o fator
            return total_alunos * qtd_padrao * fator_rendimento
        return total_alunos * qtd_padrao * fator_rendimento

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
        Calcula a quantidade proporcional exata de cada ingrediente:
        Qtd Calculada = Total Estudantes * Qtd Padrão * Fator de Rendimento

        Regras de Integridade:
        - Bloqueia cálculo sem frequência de estudantes (total <= 0)
        - Bloqueia cardápio sem fichas técnicas/itens de receita cadastrados
        - Preserva coerência física entre unidades (não converte massa em volume sem densidade)
        - Consolida insumos duplicados entre preparações do mesmo cardápio
        - Preserva ajustes manuais já conferidos pelo refeitório (RF09) se não for recalculo forçado
        """
        if not frequencia or frequencia.total_estudantes_presentes <= 0:
            raise ValidationError("Não é possível gerar cálculo sem o registro de estudantes presentes informado.")

        total_itens_receita = sum(r.itens.count() for r in cardapio.receitas.all())
        if total_itens_receita == 0:
            raise ValidationError(f"O cardápio '{cardapio.nome}' não possui itens de receita cadastrados para cálculo.")

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
        for receita in cardapio.receitas.prefetch_related('itens__ingrediente').all():
            fator = receita.fator_rendimento or Decimal('1.000')
            for item in receita.itens.all():
                qtd_calculada_item = cls.calcular_quantidade_item(item, total_alunos, fator)
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
                elif un_item != un_acumulada:
                    # Grandezas incompatíveis (ex: massa vs volume) - mantêm-se na grandeza declarada
                    # sem conversão fictícia (Regra 3.2 do AGENTS.md)
                    totais_ingredientes[ing_id]['quantidade'] += qtd_calculada_item
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
