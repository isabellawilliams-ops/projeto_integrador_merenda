from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import (
    Cardapio,
    Ingrediente,
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
