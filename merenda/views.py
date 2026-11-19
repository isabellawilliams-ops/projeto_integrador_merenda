from django.contrib import messages
from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView
from django.db import models
from django.shortcuts import redirect, render
from django.urls import reverse_lazy
from django.utils import timezone

from .forms import LoginForm
from .models import (
    CalculoDiario,
    Cardapio,
    FrequenciaDiaria,
    Ingrediente,
    ReceitaFichaTecnica,
    Usuario,
)


class SPALoginView(LoginView):
    template_name = 'login.html'
    form_class = LoginForm
    redirect_authenticated_user = True
    next_page = reverse_lazy('home')

    def form_valid(self, form):
        messages.success(
            self.request,
            f"Bem-vindo(a), {form.get_user().nome_completo or form.get_user().username}!"
        )
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['ano_atual'] = timezone.now().year
        return context


def logout_view(request):
    """Realiza o logout do usuário e redireciona para a tela de autenticação."""
    if request.user.is_authenticated:
        messages.info(request, "Sessão encerrada com sucesso.")
        logout(request)
    return redirect('login')


@login_required
def home_view(request):
    """Dashboard principal dinâmico adaptado ao perfil do usuário (RBAC)."""
    hoje = timezone.localdate()

    # Cardápio e Cálculo do Dia de Hoje
    cardapio_hoje = Cardapio.objects.filter(
        ativo=True
    ).filter(
        models.Q(data_referencia=hoje) | models.Q(data_referencia__isnull=True)
    ).prefetch_related('receitas__itens__ingrediente').first()

    frequencia_hoje = FrequenciaDiaria.objects.filter(data_refeicao=hoje).first()

    calculo_hoje = CalculoDiario.objects.filter(
        data_calculo=hoje
    ).select_related('cardapio', 'frequencia', 'usuario_responsavel').prefetch_related('itens__ingrediente').first()

    # Métricas Globais do Sistema
    total_cardapios = Cardapio.objects.filter(ativo=True).count()
    total_ingredientes = Ingrediente.objects.count()
    total_receitas = ReceitaFichaTecnica.objects.count()
    total_usuarios = Usuario.objects.filter(ativo=True).count()
    calculos_conferidos_total = CalculoDiario.objects.filter(conferido=True).count()
    calculos_pendentes_total = CalculoDiario.objects.filter(conferido=False).count()

    # Histórico recente para acompanhamento
    frequencias_recentes = FrequenciaDiaria.objects.select_related(
        'usuario_registro'
    ).order_by('-data_refeicao', '-registrado_em')[:5]

    calculos_recentes = CalculoDiario.objects.select_related(
        'cardapio', 'frequencia', 'usuario_responsavel'
    ).order_by('-data_calculo', '-gerado_em')[:5]

    context = {
        'usuario': request.user,
        'hoje': hoje,
        'cardapio_hoje': cardapio_hoje,
        'frequencia_hoje': frequencia_hoje,
        'calculo_hoje': calculo_hoje,
        'total_cardapios': total_cardapios,
        'total_ingredientes': total_ingredientes,
        'total_receitas': total_receitas,
        'total_usuarios': total_usuarios,
        'calculos_conferidos_total': calculos_conferidos_total,
        'calculos_pendentes_total': calculos_pendentes_total,
        'frequencias_recentes': frequencias_recentes,
        'calculos_recentes': calculos_recentes,
    }
    return render(request, 'home.html', context)

