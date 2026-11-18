from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import Usuario, Ingrediente


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
