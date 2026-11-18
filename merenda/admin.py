from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import (
    CalculoDiario,
    Cardapio,
    FrequenciaDiaria,
    Ingrediente,
    ItemCalculo,
    ItemReceita,
    ReceitaFichaTecnica,
    Usuario,
)


@admin.register(Usuario)
class UsuarioAdmin(UserAdmin):
    list_display = ('username', 'nome_completo', 'perfil', 'ativo', 'is_staff')
    list_filter = ('perfil', 'ativo', 'is_staff', 'is_superuser')
    search_fields = ('username', 'nome_completo', 'email')
    ordering = ('username',)

    fieldsets = UserAdmin.fieldsets + (
        ('Informações SPAE', {
            'fields': ('nome_completo', 'perfil', 'ativo'),
        }),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        ('Informações SPAE', {
            'fields': ('nome_completo', 'perfil', 'ativo'),
        }),
    )


@admin.register(Ingrediente)
class IngredienteAdmin(admin.ModelAdmin):
    list_display = ('nome', 'unidade_padrao', 'observacoes')
    list_filter = ('unidade_padrao',)
    search_fields = ('nome', 'observacoes')
    ordering = ('nome',)


class ItemReceitaInline(admin.TabularInline):
    model = ItemReceita
    extra = 1
    autocomplete_fields = ['ingrediente']


class ReceitaFichaTecnicaInline(admin.StackedInline):
    model = ReceitaFichaTecnica
    extra = 1
    show_change_link = True


@admin.register(Cardapio)
class CardapioAdmin(admin.ModelAdmin):
    list_display = ('nome', 'refeicao', 'data_referencia', 'ativo', 'total_receitas')
    list_filter = ('refeicao', 'ativo', 'data_referencia')
    search_fields = ('nome', 'descricao')
    date_hierarchy = 'data_referencia'
    inlines = [ReceitaFichaTecnicaInline]

    @admin.display(description='Total de Preparações')
    def total_receitas(self, obj):
        return obj.receitas.count()


@admin.register(ReceitaFichaTecnica)
class ReceitaFichaTecnicaAdmin(admin.ModelAdmin):
    list_display = ('nome', 'cardapio', 'fator_rendimento', 'total_ingredientes')
    list_filter = ('cardapio__refeicao', 'cardapio')
    search_fields = ('nome', 'modo_preparo', 'cardapio__nome')
    inlines = [ItemReceitaInline]

    @admin.display(description='Qtd Ingredientes')
    def total_ingredientes(self, obj):
        return obj.itens.count()


@admin.register(ItemReceita)
class ItemReceitaAdmin(admin.ModelAdmin):
    list_display = ('receita', 'ingrediente', 'quantidade_padrao', 'unidade_medida', 'base_calculo')
    list_filter = ('unidade_medida', 'base_calculo', 'receita__cardapio')
    search_fields = ('receita__nome', 'ingrediente__nome')
    autocomplete_fields = ['ingrediente', 'receita']


@admin.register(FrequenciaDiaria)
class FrequenciaDiariaAdmin(admin.ModelAdmin):
    list_display = ('data_refeicao', 'refeicao_turno', 'total_estudantes_presentes', 'usuario_registro', 'registrado_em')
    list_filter = ('refeicao_turno', 'data_refeicao')
    search_fields = ('usuario_registro__username', 'usuario_registro__nome_completo')
    date_hierarchy = 'data_refeicao'


class ItemCalculoInline(admin.TabularInline):
    model = ItemCalculo
    extra = 0
    autocomplete_fields = ['ingrediente']
    fields = ('ingrediente', 'quantidade_calculada', 'unidade_medida', 'quantidade_ajustada', 'justificativa_ajuste')


@admin.register(CalculoDiario)
class CalculoDiarioAdmin(admin.ModelAdmin):
    list_display = ('data_calculo', 'cardapio', 'frequencia', 'usuario_responsavel', 'conferido', 'gerado_em')
    list_filter = ('conferido', 'data_calculo', 'cardapio__refeicao')
    search_fields = ('cardapio__nome', 'usuario_responsavel__username', 'usuario_responsavel__nome_completo')
    date_hierarchy = 'data_calculo'
    inlines = [ItemCalculoInline]


@admin.register(ItemCalculo)
class ItemCalculoAdmin(admin.ModelAdmin):
    list_display = ('calculo', 'ingrediente', 'quantidade_calculada', 'unidade_medida', 'quantidade_ajustada')
    list_filter = ('unidade_medida', 'calculo__conferido')
    search_fields = ('ingrediente__nome', 'calculo__cardapio__nome', 'justificativa_ajuste')
    autocomplete_fields = ['calculo', 'ingrediente']
