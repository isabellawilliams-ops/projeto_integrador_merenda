from django.contrib import messages
from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView
from django.db import models
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.utils import timezone

from .forms import FrequenciaDiariaForm, LoginForm
from .models import (
    CalculoDiario,
    Cardapio,
    FrequenciaDiaria,
    Ingrediente,
    ReceitaFichaTecnica,
    TipoRefeicao,
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


# ========================================================
# MÓDULO DE FREQUÊNCIA DIÁRIA
# ========================================================

@login_required
def frequencia_lista_view(request):
    """Lista o histórico completo de frequências diárias com filtros rápidos."""
    frequencias = FrequenciaDiaria.objects.select_related(
        'usuario_registro'
    ).order_by('-data_refeicao', '-registrado_em')

    # Filtro opcional por refeição
    refeicao_filtro = request.GET.get('refeicao', '').strip()
    if refeicao_filtro:
        frequencias = frequencias.filter(refeicao_turno=refeicao_filtro)

    # Filtro opcional por data
    data_filtro = request.GET.get('data', '').strip()
    if data_filtro:
        frequencias = frequencias.filter(data_refeicao=data_filtro)

    hoje = timezone.localdate()
    total_hoje = FrequenciaDiaria.objects.filter(data_refeicao=hoje).first()
    media_alunos = FrequenciaDiaria.objects.aggregate(
        models.Avg('total_estudantes_presentes')
    )['total_estudantes_presentes__avg']

    context = {
        'frequencias': frequencias,
        'refeicao_filtro': refeicao_filtro,
        'data_filtro': data_filtro,
        'tipos_refeicao': TipoRefeicao.choices,
        'total_hoje': total_hoje,
        'media_alunos': round(media_alunos, 1) if media_alunos else 0,
        'hoje': hoje,
    }
    return render(request, 'frequencia/lista.html', context)


@login_required
def frequencia_registro_view(request):
    """Formulário ágil mobile-first para lançamento de presença."""
    hoje = timezone.localdate()

    if request.method == 'POST':
        data_post = request.POST.get('data_refeicao')
        turno_post = request.POST.get('refeicao_turno')

        # Se já existe contagem para a mesma data e refeição, carrega como instância para permitir atualização suave
        registro_existente = None
        if data_post and turno_post:
            registro_existente = FrequenciaDiaria.objects.filter(
                data_refeicao=data_post,
                refeicao_turno=turno_post
            ).first()

        form = FrequenciaDiariaForm(request.POST, instance=registro_existente)
        if form.is_valid():
            frequencia = form.save(commit=False)
            frequencia.usuario_registro = request.user
            frequencia.save()
            acao = "atualizada" if registro_existente else "registrada"
            messages.success(
                request,
                f"Frequência {acao} com sucesso: {frequencia.total_estudantes_presentes} estudantes para {frequencia.get_refeicao_turno_display()} em {frequencia.data_refeicao.strftime('%d/%m/%Y')}!"
            )
            return redirect('frequencia_lista')
    else:
        form = FrequenciaDiariaForm(initial={
            'data_refeicao': hoje,
            'refeicao_turno': TipoRefeicao.ALMOCO,
        })

    frequencia_hoje = FrequenciaDiaria.objects.filter(data_refeicao=hoje).first()

    context = {
        'form': form,
        'hoje': hoje,
        'frequencia_hoje': frequencia_hoje,
        'titulo': 'Lançar Frequência Diária',
        'modo_edicao': False,
    }
    return render(request, 'frequencia/form.html', context)


@login_required
def frequencia_editar_view(request, pk):
    """Edição de uma contagem de frequência existente."""
    frequencia = get_object_or_404(FrequenciaDiaria, pk=pk)

    if request.method == 'POST':
        form = FrequenciaDiariaForm(request.POST, instance=frequencia)
        if form.is_valid():
            freq = form.save(commit=False)
            freq.usuario_registro = request.user
            freq.save()
            messages.success(
                request,
                f"Frequência de {freq.data_refeicao.strftime('%d/%m/%Y')} atualizada para {freq.total_estudantes_presentes} alunos."
            )
            return redirect('frequencia_lista')
    else:
        form = FrequenciaDiariaForm(instance=frequencia)

    context = {
        'form': form,
        'frequencia': frequencia,
        'titulo': f'Editar Frequência — {frequencia.data_refeicao.strftime("%d/%m/%Y")}',
        'modo_edicao': True,
    }
    return render(request, 'frequencia/form.html', context)


@login_required
def frequencia_excluir_view(request, pk):
    """Exclusão segura de registro de frequência com validação de dependências."""
    frequencia = get_object_or_404(FrequenciaDiaria, pk=pk)

    if request.method == 'POST':
        if frequencia.calculos.exists():
            messages.error(
                request,
                "Não é possível excluir esta frequência porque ela está vinculada a cálculos diários de ingredientes."
            )
        else:
            data_str = frequencia.data_refeicao.strftime('%d/%m/%Y')
            refeicao_str = frequencia.get_refeicao_turno_display()
            frequencia.delete()
            messages.success(
                request,
                f"Frequência de {refeicao_str} em {data_str} removida com sucesso."
            )
        return redirect('frequencia_lista')

    context = {
        'frequencia': frequencia,
    }
    return render(request, 'frequencia/confirmar_exclusao.html', context)


