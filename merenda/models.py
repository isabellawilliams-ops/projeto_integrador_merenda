from django.contrib.auth.models import AbstractUser
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
