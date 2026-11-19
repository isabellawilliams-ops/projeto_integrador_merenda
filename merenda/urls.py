from django.urls import path
from . import views

urlpatterns = [
    path('', views.home_view, name='home'),
    path('login/', views.SPALoginView.as_view(), name='login'),
    path('logout/', views.logout_view, name='logout'),

    # Frequência Diária
    path('frequencia/', views.frequencia_lista_view, name='frequencia_lista'),
    path('frequencia/registrar/', views.frequencia_registro_view, name='frequencia_registrar'),
    path('frequencia/<int:pk>/editar/', views.frequencia_editar_view, name='frequencia_editar'),
    path('frequencia/<int:pk>/excluir/', views.frequencia_excluir_view, name='frequencia_excluir'),
]
