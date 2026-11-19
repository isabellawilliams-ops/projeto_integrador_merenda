from django.urls import path
from . import views

urlpatterns = [
    # Painel Principal e Autenticação
    path('', views.home_view, name='home'),
    path('login/', views.SPALoginView.as_view(), name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('meu-perfil/', views.meu_perfil_view, name='meu_perfil'),
    path('alterar-senha/', views.alterar_senha_view, name='alterar_senha'),

    # Gestão Administrativa de Usuários e Perfis (RF01 - RBAC)
    path('usuarios/', views.usuario_lista_view, name='usuario_lista'),
    path('usuarios/novo/', views.usuario_criar_view, name='usuario_criar'),
    path('usuarios/<int:pk>/editar/', views.usuario_editar_view, name='usuario_editar'),
    path('usuarios/<int:pk>/redefinir-senha/', views.usuario_redefinir_senha_view, name='usuario_redefinir_senha'),
    path('usuarios/<int:pk>/alternar-status/', views.usuario_alternar_status_view, name='usuario_alternar_status'),

    # Frequência Diária
    path('frequencia/', views.frequencia_lista_view, name='frequencia_lista'),
    path('frequencia/registrar/', views.frequencia_registro_view, name='frequencia_registrar'),
    path('frequencia/<int:pk>/editar/', views.frequencia_editar_view, name='frequencia_editar'),
    path('frequencia/<int:pk>/excluir/', views.frequencia_excluir_view, name='frequencia_excluir'),

    # Módulo Visual de Cadastros Administrativos (Central)
    path('cadastros/', views.cadastros_hub_view, name='cadastros_hub'),

    # Cadastros: Ingredientes
    path('cadastros/ingredientes/', views.ingrediente_lista_view, name='ingrediente_lista'),
    path('cadastros/ingredientes/novo/', views.ingrediente_criar_view, name='ingrediente_criar'),
    path('cadastros/ingredientes/<int:pk>/editar/', views.ingrediente_editar_view, name='ingrediente_editar'),
    path('cadastros/ingredientes/<int:pk>/excluir/', views.ingrediente_excluir_view, name='ingrediente_excluir'),

    # Cadastros: Cardápios & Fichas Técnicas
    path('cadastros/cardapios/', views.cardapio_lista_view, name='cardapio_lista'),
    path('cadastros/cardapios/novo/', views.cardapio_criar_view, name='cardapio_criar'),
    path('cadastros/cardapios/<int:pk>/', views.cardapio_detalhe_view, name='cardapio_detalhe'),
    path('cadastros/cardapios/<int:pk>/editar/', views.cardapio_editar_view, name='cardapio_editar'),
    path('cadastros/cardapios/<int:pk>/excluir/', views.cardapio_excluir_view, name='cardapio_excluir'),

    # Fichas Técnicas: Preparações (Receitas) e Insumos (Itens)
    path('cadastros/cardapios/<int:cardapio_pk>/receitas/nova/', views.receita_criar_view, name='receita_criar'),
    path('cadastros/receitas/<int:pk>/editar/', views.receita_editar_view, name='receita_editar'),
    path('cadastros/receitas/<int:pk>/excluir/', views.receita_excluir_view, name='receita_excluir'),
    path('cadastros/receitas/<int:receita_pk>/itens/novo/', views.item_receita_adicionar_view, name='item_receita_adicionar'),
    path('cadastros/itens-receita/<int:pk>/excluir/', views.item_receita_excluir_view, name='item_receita_excluir'),

    # Cálculo e Conferência de Ingredientes
    path('calculo/', views.calculo_detalhe_view, name='calculo_hoje'),
    path('calculo/<int:pk>/', views.calculo_detalhe_view, name='calculo_detalhe'),
    path('calculo/gerar/', views.calculo_gerar_view, name='calculo_gerar'),
    path('calculo/historico/', views.calculo_lista_view, name='calculo_lista'),
    path('calculo/<int:pk>/conferir/', views.calculo_conferir_view, name='calculo_conferir'),
    path('calculo/itens/<int:pk>/ajustar/', views.calculo_ajustar_item_view, name='calculo_ajustar_item'),

    # Exportação e Impressão do Resumo Diário (RF11)
    path('calculo/<int:pk>/imprimir/', views.calculo_imprimir_view, name='calculo_imprimir'),
    path('calculo/<int:pk>/exportar-csv/', views.calculo_exportar_csv_view, name='calculo_exportar_csv'),
]
