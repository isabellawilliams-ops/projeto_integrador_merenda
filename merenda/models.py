from decimal import Decimal
from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ValidationError
from django.db import models


class PerfilUsuario(models.TextChoices):
    REFEITORIO = 'refeitorio', 'Refeitório (Merendeira)'
    FREQUENCIA = 'frequencia', 'Frequência (Secretaria/Portaria)'
    GESTAO = 'gestao', 'Gestão / Cardápio (Nutricionista/Direção)'
    ADMIN = 'admin', 'Administrador'


class Usuario(AbstractUser):
    nome_completo = models.CharField(
        max_length=255,
        blank=True,
        verbose_name="Nome Completo",
        help_text="Nome completo do usuário para identificação nas rotinas do refeitório."
    )
    perfil = models.CharField(
        max_length=20,
        choices=PerfilUsuario.choices,
        default=PerfilUsuario.REFEITORIO,
        verbose_name="Perfil de Acesso",
        help_text="Define as permissões e o escopo de atuação no sistema."
    )
    ativo = models.BooleanField(
        default=True,
        verbose_name="Ativo",
        help_text="Indica se o usuário possui acesso ativo ao sistema."
    )

    class Meta:
        verbose_name = "Usuário"
        verbose_name_plural = "Usuários"
        ordering = ['username']

    def save(self, *args, **kwargs):
        # Sincroniza o campo 'ativo' com o 'is_active' nativo do AbstractUser
        self.is_active = self.ativo
        if self.nome_completo and not (self.first_name or self.last_name):
            partes = self.nome_completo.strip().split(' ', 1)
            self.first_name = partes[0]
            if len(partes) > 1:
                self.last_name = partes[1]
        super().save(*args, **kwargs)

    def __str__(self):
        identificacao = self.nome_completo or self.get_full_name() or self.username
        return f"{identificacao} ({self.get_perfil_display()})"


class UnidadeMedida(models.TextChoices):
    GRAMA = 'g', 'Grama (g)'
    QUILOGRAMA = 'kg', 'Quilograma (kg)'
    MILILITRO = 'ml', 'Mililitro (ml)'
    LITRO = 'L', 'Litro (L)'
    UNIDADE = 'un', 'Unidade (un)'


class Ingrediente(models.Model):
    nome = models.CharField(
        max_length=150,
        unique=True,
        verbose_name="Nome do Ingrediente",
        help_text="Nome padronizado do insumo (ex: Arroz Branco tipo 1, Feijão Carioca, Óleo de Soja)."
    )
    unidade_padrao = models.CharField(
        max_length=10,
        choices=UnidadeMedida.choices,
        default=UnidadeMedida.QUILOGRAMA,
        verbose_name="Unidade Padrão",
        help_text="Unidade padrão de medida (g, kg, ml, L ou un)."
    )
    observacoes = models.TextField(
        blank=True,
        verbose_name="Observações de Armazenamento/Uso",
        help_text="Orientações sobre armazenamento, acondicionamento e boas práticas de uso."
    )

    class Meta:
        verbose_name = "Ingrediente"
        verbose_name_plural = "Ingredientes"
        ordering = ['nome']

    def __str__(self):
        return f"{self.nome} ({self.get_unidade_padrao_display()})"


class TipoRefeicao(models.TextChoices):
    LANCHE_MANHA = 'lanche_manha', 'Lanche da Manhã'
    ALMOCO = 'almoco', 'Almoço'
    LANCHE_TARDE = 'lanche_tarde', 'Lanche da Tarde'


class BaseCalculo(models.TextChoices):
    POR_ALUNO = 'por_aluno', 'Por Aluno'
    POR_PORCAO = 'por_porcao', 'Por Porção'
    POR_LOTE = 'por_lote', 'Por Lote'


class Cardapio(models.Model):
    nome = models.CharField(
        max_length=150,
        verbose_name="Nome do Cardápio",
        help_text="Ex: Almoço de Segunda-feira, Lanche Especial."
    )
    descricao = models.TextField(
        blank=True,
        verbose_name="Descrição",
        help_text="Detalhamento opcional sobre o cardápio ou orientações nutricionais."
    )
    refeicao = models.CharField(
        max_length=30,
        choices=TipoRefeicao.choices,
        default=TipoRefeicao.ALMOCO,
        verbose_name="Tipo de Refeição",
        help_text="Lanche da Manhã, Almoço ou Lanche da Tarde."
    )
    data_referencia = models.DateField(
        null=True,
        blank=True,
        verbose_name="Data de Referência",
        help_text="Data prevista ou dia específico em que o cardápio será servido (opcional para cardápios recorrentes)."
    )
    ativo = models.BooleanField(
        default=True,
        verbose_name="Ativo",
        help_text="Indica se o cardápio está disponível para planejamento."
    )

    class Meta:
        verbose_name = "Cardápio"
        verbose_name_plural = "Cardápios"
        ordering = ['-data_referencia', 'nome']

    def __str__(self):
        ref = f" - {self.data_referencia.strftime('%d/%m/%Y')}" if self.data_referencia else ""
        return f"{self.nome} ({self.get_refeicao_display()}){ref}"


class ReceitaFichaTecnica(models.Model):
    cardapio = models.ForeignKey(
        Cardapio,
        on_delete=models.CASCADE,
        related_name='receitas',
        verbose_name="Cardápio"
    )
    nome = models.CharField(
        max_length=150,
        verbose_name="Nome da Preparação",
        help_text="Ex: Arroz Branco com Legumes, Frango Ensopado, Salada de Frutas."
    )
    modo_preparo = models.TextField(
        blank=True,
        verbose_name="Modo de Preparo",
        help_text="Instruções e etapas de cocção para a equipe do refeitório."
    )
    fator_rendimento = models.DecimalField(
        max_digits=6,
        decimal_places=3,
        default=Decimal('1.000'),
        verbose_name="Fator de Rendimento/Perda",
        help_text="Ajuste validado de rendimento ou perda (padrão 1.000)."
    )

    class Meta:
        verbose_name = "Receita / Ficha Técnica"
        verbose_name_plural = "Receitas / Fichas Técnicas"
        ordering = ['cardapio', 'nome']

    def clean(self):
        super().clean()
        if self.fator_rendimento is not None and self.fator_rendimento <= Decimal('0'):
            raise ValidationError({'fator_rendimento': 'O fator de rendimento deve ser maior que zero.'})

    def __str__(self):
        return f"{self.nome} ({self.cardapio.nome})"


# Alias de conveniência
Receita = ReceitaFichaTecnica


class ItemReceita(models.Model):
    receita = models.ForeignKey(
        ReceitaFichaTecnica,
        on_delete=models.CASCADE,
        related_name='itens',
        verbose_name="Receita / Ficha Técnica"
    )
    ingrediente = models.ForeignKey(
        Ingrediente,
        on_delete=models.PROTECT,
        related_name='itens_receita',
        verbose_name="Ingrediente"
    )
    quantidade_padrao = models.DecimalField(
        max_digits=10,
        decimal_places=4,
        verbose_name="Quantidade Padrão",
        help_text="Quantidade definida na ficha técnica conforme a base de cálculo."
    )
    unidade_medida = models.CharField(
        max_length=10,
        choices=UnidadeMedida.choices,
        verbose_name="Unidade de Medida",
        help_text="Unidade usada na receita (g, kg, ml, L ou un)."
    )
    base_calculo = models.CharField(
        max_length=20,
        choices=BaseCalculo.choices,
        default=BaseCalculo.POR_ALUNO,
        verbose_name="Base de Cálculo",
        help_text="Base de aplicação (por aluno, por porção ou por lote)."
    )

    class Meta:
        verbose_name = "Item da Receita"
        verbose_name_plural = "Itens da Receita"
        ordering = ['receita', 'ingrediente']
        constraints = [
            models.UniqueConstraint(
                fields=['receita', 'ingrediente'],
                name='unique_ingrediente_por_receita'
            )
        ]

    def clean(self):
        super().clean()
        if self.quantidade_padrao is not None and self.quantidade_padrao <= Decimal('0'):
            raise ValidationError({'quantidade_padrao': 'A quantidade padrão deve ser maior que zero.'})

    def __str__(self):
        return f"{self.ingrediente.nome}: {self.quantidade_padrao} {self.get_unidade_medida_display()} ({self.get_base_calculo_display()})"


class FrequenciaDiaria(models.Model):
    usuario_registro = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='frequencias_registradas',
        verbose_name="Usuário Responsável",
        help_text="Profissional que inseriu a contagem de frequência no sistema."
    )
    data_refeicao = models.DateField(
        verbose_name="Data da Refeição",
        help_text="Data para a qual a contagem de alunos é válida."
    )
    refeicao_turno = models.CharField(
        max_length=30,
        choices=TipoRefeicao.choices,
        default=TipoRefeicao.ALMOCO,
        verbose_name="Turno / Refeição",
        help_text="Refeição ou turno escolar correspondente à contagem."
    )
    total_estudantes_presentes = models.PositiveIntegerField(
        verbose_name="Total de Estudantes Presentes",
        help_text="Quantidade de alunos confirmados presentes para esta refeição."
    )
    registrado_em = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Registrado em"
    )

    class Meta:
        verbose_name = "Frequência Diária"
        verbose_name_plural = "Frequências Diárias"
        ordering = ['-data_refeicao', 'refeicao_turno']
        constraints = [
            models.UniqueConstraint(
                fields=['data_refeicao', 'refeicao_turno'],
                name='unique_frequencia_por_data_refeicao'
            )
        ]

    def __str__(self):
        return f"{self.data_refeicao.strftime('%d/%m/%Y')} - {self.get_refeicao_turno_display()}: {self.total_estudantes_presentes} alunos"


class CalculoDiario(models.Model):
    cardapio = models.ForeignKey(
        Cardapio,
        on_delete=models.PROTECT,
        related_name='calculos',
        verbose_name="Cardápio Utilizado"
    )
    frequencia = models.ForeignKey(
        FrequenciaDiaria,
        on_delete=models.PROTECT,
        related_name='calculos',
        verbose_name="Frequência Diária Utilizada"
    )
    usuario_responsavel = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='calculos_executados',
        verbose_name="Usuário Responsável",
        help_text="Profissional responsável pela geração ou conferência do cálculo."
    )
    data_calculo = models.DateField(
        verbose_name="Data do Planejamento",
        help_text="Data de execução ou aplicação do cálculo."
    )
    gerado_em = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Gerado em"
    )
    conferido = models.BooleanField(
        default=False,
        verbose_name="Conferido pelo Refeitório",
        help_text="Indica se a lista de ingredientes foi conferida e aprovada antes do preparo."
    )

    class Meta:
        verbose_name = "Cálculo Diário"
        verbose_name_plural = "Cálculos Diários"
        ordering = ['-data_calculo', '-gerado_em']

    def __str__(self):
        status = "Conferido" if self.conferido else "Pendente de Conferência"
        return f"Cálculo {self.data_calculo.strftime('%d/%m/%Y')} - {self.cardapio.nome} ({status})"


class ItemCalculo(models.Model):
    calculo = models.ForeignKey(
        CalculoDiario,
        on_delete=models.CASCADE,
        related_name='itens',
        verbose_name="Cálculo Diário"
    )
    ingrediente = models.ForeignKey(
        Ingrediente,
        on_delete=models.PROTECT,
        related_name='itens_calculados',
        verbose_name="Ingrediente"
    )
    quantidade_calculada = models.DecimalField(
        max_digits=12,
        decimal_places=4,
        verbose_name="Quantidade Calculada",
        help_text="Resultado do cálculo automático proporcional à frequência."
    )
    unidade_medida = models.CharField(
        max_length=10,
        choices=UnidadeMedida.choices,
        verbose_name="Unidade de Medida"
    )
    quantidade_ajustada = models.DecimalField(
        max_digits=12,
        decimal_places=4,
        null=True,
        blank=True,
        verbose_name="Quantidade Ajustada",
        help_text="Ajuste manual autorizado pela equipe do refeitório (opcional)."
    )
    justificativa_ajuste = models.TextField(
        blank=True,
        verbose_name="Justificativa do Ajuste",
        help_text="Obrigatório caso haja alteração manual da quantidade sugerida (RF09)."
    )

    class Meta:
        verbose_name = "Item do Cálculo"
        verbose_name_plural = "Itens do Cálculo"
        ordering = ['calculo', 'ingrediente']
        constraints = [
            models.UniqueConstraint(
                fields=['calculo', 'ingrediente'],
                name='unique_ingrediente_por_calculo'
            )
        ]

    def clean(self):
        super().clean()
        # RF09: Justificativa obrigatória se houver quantidade ajustada
        if self.quantidade_ajustada is not None:
            if not self.justificativa_ajuste or not self.justificativa_ajuste.strip():
                raise ValidationError({
                    'justificativa_ajuste': 'A justificativa do ajuste é obrigatória quando uma quantidade ajustada é informada (RF09).'
                })
            if self.quantidade_ajustada < Decimal('0'):
                raise ValidationError({
                    'quantidade_ajustada': 'A quantidade ajustada não pode ser negativa.'
                })

    @property
    def quantidade_final(self):
        """Retorna a quantidade ajustada (se informada) ou a calculada automaticamente."""
        if self.quantidade_ajustada is not None:
            return self.quantidade_ajustada
        return self.quantidade_calculada

    def __str__(self):
        qtd = self.quantidade_final
        return f"{self.ingrediente.nome}: {qtd} {self.get_unidade_medida_display()}"
