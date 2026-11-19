import csv
from decimal import Decimal
from django.contrib import messages
from django.contrib.auth import logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView
from django.db import models
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.utils import timezone
from django.utils.text import slugify

from .forms import (
    AlterarPropriaSenhaForm,
    CalculoGerarForm,
    CardapioForm,
    FrequenciaDiariaForm,
    IngredienteForm,
    ItemCalculoAjusteForm,
    ItemReceitaForm,
    LoginForm,
    MeuPerfilForm,
    ReceitaFichaTecnicaForm,
    UsuarioCriacaoForm,
    UsuarioEdicaoForm,
    UsuarioRedefinirSenhaForm,
)
from .models import (
    CalculoDiario,
    Cardapio,
    FrequenciaDiaria,
    Ingrediente,
    ItemCalculo,
    ItemReceita,
    PerfilUsuario,
    ReceitaFichaTecnica,
    TipoRefeicao,
    UnidadeMedida,
    Usuario,
)
from .permissions import (
    admin_requerido,
    frequencia_requerida,
    gestao_requerida,
    perfil_requerido,
    pode_conferir_calculo,
    pode_gerenciar_cadastros,
    pode_gerenciar_usuarios,
    pode_lancar_frequencia,
    refeitorio_requerido,
    tem_perfil,
)
from .services import CalculoService


# ========================================================
# AUTENTICAÇÃO E DASHBOARD
# ========================================================

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


# ========================================================
# AUTOATENDIMENTO DO USUÁRIO (PERFIL E ALTERAÇÃO DE SENHA)
# ========================================================

@login_required
def meu_perfil_view(request):
    """Exibe e permite a atualização das informações cadastrais do próprio usuário logado."""
    if request.method == 'POST':
        form = MeuPerfilForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, "Seus dados de perfil foram atualizados com sucesso!")
            return redirect('meu_perfil')
    else:
        form = MeuPerfilForm(instance=request.user)

    context = {
        'form': form,
        'usuario': request.user,
    }
    return render(request, 'usuarios/meu_perfil.html', context)


@login_required
def alterar_senha_view(request):
    """Permite ao próprio usuário logado alterar sua senha de acesso de forma segura."""
    if request.method == 'POST':
        form = AlterarPropriaSenhaForm(user=request.user, data=request.POST)
        if form.is_valid():
            user = form.save()
            # Mantém a sessão do usuário ativa após a troca de hash de senha
            update_session_auth_hash(request, user)
            messages.success(request, "Sua senha foi alterada com sucesso!")
            return redirect('meu_perfil')
    else:
        form = AlterarPropriaSenhaForm(user=request.user)

    context = {
        'form': form,
    }
    return render(request, 'usuarios/alterar_senha.html', context)


# ========================================================
# GESTÃO ADMINISTRATIVA DE USUÁRIOS E PERFIS RBAC (ADMIN)
# ========================================================

@admin_requerido
def usuario_lista_view(request):
    """Listagem completa de usuários com filtros por perfil e status (ativo/inativo)."""
    usuarios = Usuario.objects.all().order_by('nome_completo', 'username')

    q = request.GET.get('q', '').strip()
    if q:
        usuarios = usuarios.filter(
            models.Q(username__icontains=q)
            | models.Q(nome_completo__icontains=q)
            | models.Q(first_name__icontains=q)
            | models.Q(last_name__icontains=q)
        )

    perfil_filtro = request.GET.get('perfil', '').strip()
    if perfil_filtro:
        usuarios = usuarios.filter(perfil=perfil_filtro)

    status_filtro = request.GET.get('status', '').strip()
    if status_filtro == 'ativo':
        usuarios = usuarios.filter(ativo=True)
    elif status_filtro == 'inativo':
        usuarios = usuarios.filter(ativo=False)

    total_usuarios = Usuario.objects.count()
    total_ativos = Usuario.objects.filter(ativo=True).count()
    total_inativos = Usuario.objects.filter(ativo=False).count()

    context = {
        'usuarios': usuarios,
        'q': q,
        'perfil_filtro': perfil_filtro,
        'status_filtro': status_filtro,
        'perfis_choices': PerfilUsuario.choices,
        'total_usuarios': total_usuarios,
        'total_ativos': total_ativos,
        'total_inativos': total_inativos,
    }
    return render(request, 'usuarios/lista.html', context)


@admin_requerido
def usuario_criar_view(request):
    """Cadastro de novo usuário com definição de perfil de acesso e senha inicial."""
    if request.method == 'POST':
        form = UsuarioCriacaoForm(request.POST)
        if form.is_valid():
            novo_usuario = form.save()
            messages.success(
                request,
                f"Usuário '{novo_usuario.username}' ({novo_usuario.get_perfil_display()}) cadastrado com sucesso!"
            )
            return redirect('usuario_lista')
    else:
        form = UsuarioCriacaoForm()

    context = {
        'form': form,
        'titulo': 'Novo Usuário do Sistema',
        'subtitulo': 'Cadastre um novo profissional definindo suas permissões de acesso (RBAC).',
        'modo_edicao': False,
    }
    return render(request, 'usuarios/form.html', context)


@admin_requerido
def usuario_editar_view(request, pk):
    """Edição de dados cadastrais, perfil de acesso e status de usuário existente."""
    usuario_alvo = get_object_or_404(Usuario, pk=pk)

    if request.method == 'POST':
        form = UsuarioEdicaoForm(request.POST, instance=usuario_alvo)
        if form.is_valid():
            usuario_editado = form.save()
            messages.success(
                request,
                f"Cadastro do usuário '{usuario_editado.username}' atualizado com sucesso!"
            )
            return redirect('usuario_lista')
    else:
        form = UsuarioEdicaoForm(instance=usuario_alvo)

    context = {
        'form': form,
        'usuario_alvo': usuario_alvo,
        'titulo': f'Editar Usuário: {usuario_alvo.username}',
        'subtitulo': 'Altere o nome completo, o perfil de permissões ou o status da conta.',
        'modo_edicao': True,
    }
    return render(request, 'usuarios/form.html', context)


@admin_requerido
def usuario_redefinir_senha_view(request, pk):
    """Redefinição direta de senha de usuário pela equipe administradora."""
    usuario_alvo = get_object_or_404(Usuario, pk=pk)

    if request.method == 'POST':
        form = UsuarioRedefinirSenhaForm(request.POST)
        if form.is_valid():
            nova_senha = form.cleaned_data['nova_senha']
            usuario_alvo.set_password(nova_senha)
            usuario_alvo.save()
            messages.success(
                request,
                f"Senha do usuário '{usuario_alvo.username}' redefinida com sucesso!"
            )
            return redirect('usuario_lista')
    else:
        form = UsuarioRedefinirSenhaForm()

    context = {
        'form': form,
        'usuario_alvo': usuario_alvo,
    }
    return render(request, 'usuarios/redefinir_senha.html', context)


@admin_requerido
def usuario_alternar_status_view(request, pk):
    """Ativa ou desativa a conta de um usuário via POST rápido."""
    if request.method == 'POST':
        usuario_alvo = get_object_or_404(Usuario, pk=pk)

        # Proteção: Impede o administrador de desativar a si próprio
        if usuario_alvo == request.user:
            messages.error(request, "Ação bloqueada: você não pode desativar sua própria conta de administrador.")
            return redirect('usuario_lista')

        usuario_alvo.ativo = not usuario_alvo.ativo
        usuario_alvo.save()

        status_str = "ativada" if usuario_alvo.ativo else "desativada"
        messages.success(
            request,
            f"A conta do usuário '{usuario_alvo.username}' foi {status_str} com sucesso."
        )
    return redirect('usuario_lista')



@login_required
def home_view(request):
    """Dashboard principal dinâmico adaptado ao perfil do usuário (RBAC)."""
    hoje = timezone.localdate()

    cardapio_hoje = Cardapio.objects.filter(
        ativo=True
    ).filter(
        models.Q(data_referencia=hoje) | models.Q(data_referencia__isnull=True)
    ).prefetch_related('receitas__itens__ingrediente').first()

    frequencia_hoje = FrequenciaDiaria.objects.filter(data_refeicao=hoje).first()

    calculo_hoje = CalculoDiario.objects.filter(
        data_calculo=hoje
    ).select_related('cardapio', 'frequencia', 'usuario_responsavel').prefetch_related('itens__ingrediente').first()

    total_cardapios = Cardapio.objects.filter(ativo=True).count()
    total_ingredientes = Ingrediente.objects.count()
    total_receitas = ReceitaFichaTecnica.objects.count()
    total_usuarios = Usuario.objects.filter(ativo=True).count()
    calculos_conferidos_total = CalculoDiario.objects.filter(conferido=True).count()
    calculos_pendentes_total = CalculoDiario.objects.filter(conferido=False).count()

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
        'pode_gerenciar': pode_gerenciar_cadastros(request.user),
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

    refeicao_filtro = request.GET.get('refeicao', '').strip()
    if refeicao_filtro:
        frequencias = frequencias.filter(refeicao_turno=refeicao_filtro)

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


@frequencia_requerida
def frequencia_registro_view(request):
    """Formulário ágil mobile-first para lançamento de presença."""
    hoje = timezone.localdate()

    if request.method == 'POST':
        data_post = request.POST.get('data_refeicao')
        turno_post = request.POST.get('refeicao_turno')

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


@frequencia_requerida
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


@frequencia_requerida
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


# ========================================================
# MÓDULO VISUAL DE CADASTROS ADMINISTRATIVOS
# ========================================================

@login_required
def cadastros_hub_view(request):
    """Central / Hub dos Cadastros Administrativos (Cardápios, Fichas Técnicas e Ingredientes)."""
    context = {
        'total_cardapios': Cardapio.objects.count(),
        'total_cardapios_ativos': Cardapio.objects.filter(ativo=True).count(),
        'total_receitas': ReceitaFichaTecnica.objects.count(),
        'total_ingredientes': Ingrediente.objects.count(),
        'ultimos_cardapios': Cardapio.objects.order_by('-id')[:5],
        'ultimos_ingredientes': Ingrediente.objects.order_by('-id')[:5],
        'pode_gerenciar': pode_gerenciar_cadastros(request.user),
    }
    return render(request, 'cadastros/hub.html', context)


# --- 1. Gestão de Ingredientes ---

@login_required
def ingrediente_lista_view(request):
    """Listagem visual completa de ingredientes com busca e filtros."""
    ingredientes = Ingrediente.objects.annotate(
        total_receitas=models.Count('itens_receita', distinct=True)
    ).order_by('nome')

    q = request.GET.get('q', '').strip()
    if q:
        ingredientes = ingredientes.filter(nome__icontains=q)

    unidade_filtro = request.GET.get('unidade', '').strip()
    if unidade_filtro:
        ingredientes = ingredientes.filter(unidade_padrao=unidade_filtro)

    context = {
        'ingredientes': ingredientes,
        'q': q,
        'unidade_filtro': unidade_filtro,
        'unidades_choices': UnidadeMedida.choices,
        'pode_gerenciar': pode_gerenciar_cadastros(request.user),
    }
    return render(request, 'cadastros/ingredientes_lista.html', context)


@login_required
def ingrediente_criar_view(request):
    """Cadastro visual de novo insumo/ingrediente."""
    if not pode_gerenciar_cadastros(request.user):
        messages.error(request, "Permissão negada: somente a equipe de gestão ou administradores podem cadastrar ingredientes.")
        return redirect('ingrediente_lista')

    if request.method == 'POST':
        form = IngredienteForm(request.POST)
        if form.is_valid():
            ing = form.save()
            messages.success(request, f"Ingrediente '{ing.nome}' cadastrado com sucesso!")
            return redirect('ingrediente_lista')
    else:
        form = IngredienteForm()

    context = {
        'form': form,
        'titulo': 'Novo Ingrediente',
        'modo_edicao': False,
    }
    return render(request, 'cadastros/ingrediente_form.html', context)


@login_required
def ingrediente_editar_view(request, pk):
    """Edição visual de ingrediente cadastrado."""
    if not pode_gerenciar_cadastros(request.user):
        messages.error(request, "Permissão negada: somente a equipe de gestão ou administradores podem editar ingredientes.")
        return redirect('ingrediente_lista')

    ingrediente = get_object_or_404(Ingrediente, pk=pk)

    if request.method == 'POST':
        form = IngredienteForm(request.POST, instance=ingrediente)
        if form.is_valid():
            ing = form.save()
            messages.success(request, f"Ingrediente '{ing.nome}' atualizado com sucesso!")
            return redirect('ingrediente_lista')
    else:
        form = IngredienteForm(instance=ingrediente)

    context = {
        'form': form,
        'ingrediente': ingrediente,
        'titulo': f'Editar: {ingrediente.nome}',
        'modo_edicao': True,
    }
    return render(request, 'cadastros/ingrediente_form.html', context)


@login_required
def ingrediente_excluir_view(request, pk):
    """Exclusão protegida de ingrediente com checagem de integridade."""
    if not pode_gerenciar_cadastros(request.user):
        messages.error(request, "Permissão negada: somente a equipe de gestão ou administradores podem excluir ingredientes.")
        return redirect('ingrediente_lista')

    ingrediente = get_object_or_404(Ingrediente, pk=pk)

    if request.method == 'POST':
        if ingrediente.itens_receita.exists():
            messages.error(
                request,
                f"O ingrediente '{ingrediente.nome}' não pode ser excluído pois está em uso nas receitas do cardápio."
            )
        elif ingrediente.itens_calculados.exists():
            messages.error(
                request,
                f"O ingrediente '{ingrediente.nome}' não pode ser excluído pois está registrado em cálculos históricos."
            )
        else:
            nome = ingrediente.nome
            ingrediente.delete()
            messages.success(request, f"Ingrediente '{nome}' excluído com sucesso.")
        return redirect('ingrediente_lista')

    context = {
        'ingrediente': ingrediente,
        'em_uso': ingrediente.itens_receita.exists() or ingrediente.itens_calculados.exists(),
    }
    return render(request, 'cadastros/ingrediente_confirmar_exclusao.html', context)


# --- 2. Gestão de Cardápios & Fichas Técnicas ---

@login_required
def cardapio_lista_view(request):
    """Listagem visual dos cardápios escolares com filtros por refeição e status."""
    cardapios = Cardapio.objects.prefetch_related(
        'receitas__itens__ingrediente'
    ).order_by('-data_referencia', 'nome')

    refeicao_filtro = request.GET.get('refeicao', '').strip()
    if refeicao_filtro:
        cardapios = cardapios.filter(refeicao=refeicao_filtro)

    status_filtro = request.GET.get('status', '').strip()
    if status_filtro == 'ativo':
        cardapios = cardapios.filter(ativo=True)
    elif status_filtro == 'inativo':
        cardapios = cardapios.filter(ativo=False)

    context = {
        'cardapios': cardapios,
        'refeicao_filtro': refeicao_filtro,
        'status_filtro': status_filtro,
        'tipos_refeicao': TipoRefeicao.choices,
        'pode_gerenciar': pode_gerenciar_cadastros(request.user),
    }
    return render(request, 'cadastros/cardapios_lista.html', context)


@login_required
def cardapio_criar_view(request):
    """Cadastro visual de novo cardápio escolar."""
    if not pode_gerenciar_cadastros(request.user):
        messages.error(request, "Permissão negada: somente a equipe de gestão ou administradores podem criar cardápios.")
        return redirect('cardapio_lista')

    if request.method == 'POST':
        form = CardapioForm(request.POST)
        if form.is_valid():
            cardapio = form.save()
            messages.success(
                request,
                f"Cardápio '{cardapio.nome}' criado com sucesso! Agora você pode cadastrar as preparações e fichas técnicas."
            )
            return redirect('cardapio_detalhe', pk=cardapio.pk)
    else:
        form = CardapioForm(initial={'ativo': True})

    context = {
        'form': form,
        'titulo': 'Novo Cardápio Escolar',
        'modo_edicao': False,
    }
    return render(request, 'cadastros/cardapio_form.html', context)


@login_required
def cardapio_editar_view(request, pk):
    """Edição das informações do cardápio."""
    if not pode_gerenciar_cadastros(request.user):
        messages.error(request, "Permissão negada: somente a equipe de gestão ou administradores podem editar cardápios.")
        return redirect('cardapio_lista')

    cardapio = get_object_or_404(Cardapio, pk=pk)

    if request.method == 'POST':
        form = CardapioForm(request.POST, instance=cardapio)
        if form.is_valid():
            c = form.save()
            messages.success(request, f"Cardápio '{c.nome}' atualizado com sucesso!")
            return redirect('cardapio_detalhe', pk=c.pk)
    else:
        form = CardapioForm(instance=cardapio)

    context = {
        'form': form,
        'cardapio': cardapio,
        'titulo': f'Editar Cardápio: {cardapio.nome}',
        'modo_edicao': True,
    }
    return render(request, 'cadastros/cardapio_form.html', context)


@login_required
def cardapio_detalhe_view(request, pk):
    """Ficha Técnica Visual Completa do Cardápio: Preparações, Modos de Preparo e Ingredientes."""
    cardapio = get_object_or_404(
        Cardapio.objects.prefetch_related(
            'receitas__itens__ingrediente'
        ),
        pk=pk
    )

    context = {
        'cardapio': cardapio,
        'receita_form': ReceitaFichaTecnicaForm(),
        'item_form': ItemReceitaForm(),
        'pode_gerenciar': pode_gerenciar_cadastros(request.user),
    }
    return render(request, 'cadastros/cardapio_detalhe.html', context)


@login_required
def cardapio_excluir_view(request, pk):
    """Exclusão segura de cardápio com validação de dependências em cálculos diários."""
    if not pode_gerenciar_cadastros(request.user):
        messages.error(request, "Permissão negada: somente a equipe de gestão ou administradores podem excluir cardápios.")
        return redirect('cardapio_lista')

    cardapio = get_object_or_404(Cardapio, pk=pk)

    if request.method == 'POST':
        if cardapio.calculos.exists():
            messages.error(
                request,
                f"O cardápio '{cardapio.nome}' não pode ser excluído pois possui cálculos diários históricos vinculados."
            )
        else:
            nome = cardapio.nome
            cardapio.delete()
            messages.success(request, f"Cardápio '{nome}' excluído com sucesso.")
        return redirect('cardapio_lista')

    context = {
        'cardapio': cardapio,
        'em_uso': cardapio.calculos.exists(),
    }
    return render(request, 'cadastros/cardapio_confirmar_exclusao.html', context)


# --- 3. Preparações e Itens da Ficha Técnica ---

@login_required
def receita_criar_view(request, cardapio_pk):
    """Adiciona uma preparação (ReceitaFichaTecnica) ao cardápio."""
    if not pode_gerenciar_cadastros(request.user):
        messages.error(request, "Permissão negada para adicionar preparações.")
        return redirect('cardapio_detalhe', pk=cardapio_pk)

    cardapio = get_object_or_404(Cardapio, pk=cardapio_pk)

    if request.method == 'POST':
        form = ReceitaFichaTecnicaForm(request.POST)
        if form.is_valid():
            receita = form.save(commit=False)
            receita.cardapio = cardapio
            receita.save()
            messages.success(request, f"Preparação '{receita.nome}' adicionada ao cardápio!")
        else:
            for erro in form.errors.values():
                messages.error(request, erro)
    return redirect('cardapio_detalhe', pk=cardapio.pk)


@login_required
def receita_editar_view(request, pk):
    """Edição visual dos dados da preparação (rendimento e modo de preparo)."""
    if not pode_gerenciar_cadastros(request.user):
        messages.error(request, "Permissão negada para editar preparações.")
        return redirect('cardapio_lista')

    receita = get_object_or_404(ReceitaFichaTecnica, pk=pk)

    if request.method == 'POST':
        form = ReceitaFichaTecnicaForm(request.POST, instance=receita)
        if form.is_valid():
            r = form.save()
            messages.success(request, f"Preparação '{r.nome}' atualizada!")
            return redirect('cardapio_detalhe', pk=r.cardapio_id)
    else:
        form = ReceitaFichaTecnicaForm(instance=receita)

    context = {
        'form': form,
        'receita': receita,
        'cardapio': receita.cardapio,
        'titulo': f'Editar Preparação: {receita.nome}',
    }
    return render(request, 'cadastros/receita_form.html', context)


@login_required
def receita_excluir_view(request, pk):
    """Exclui uma preparação da ficha técnica."""
    if not pode_gerenciar_cadastros(request.user):
        messages.error(request, "Permissão negada para excluir preparações.")
        return redirect('cardapio_lista')

    receita = get_object_or_404(ReceitaFichaTecnica, pk=pk)
    cardapio_id = receita.cardapio_id
    nome = receita.nome

    if request.method == 'POST':
        receita.delete()
        messages.success(request, f"Preparação '{nome}' removida do cardápio.")
    return redirect('cardapio_detalhe', pk=cardapio_id)


@login_required
def item_receita_adicionar_view(request, receita_pk):
    """Adiciona um insumo/ingrediente à ficha técnica de uma preparação."""
    if not pode_gerenciar_cadastros(request.user):
        messages.error(request, "Permissão negada para associar ingredientes.")
        return redirect('cardapio_lista')

    receita = get_object_or_404(ReceitaFichaTecnica, pk=receita_pk)

    if request.method == 'POST':
        form = ItemReceitaForm(request.POST)
        if form.is_valid():
            item = form.save(commit=False)
            item.receita = receita

            # Checa duplicidade do mesmo ingrediente na preparação
            if ItemReceita.objects.filter(receita=receita, ingrediente=item.ingrediente).exists():
                messages.warning(
                    request,
                    f"O ingrediente '{item.ingrediente.nome}' já faz parte desta preparação. Edite ou exclua o item existente."
                )
            else:
                item.save()
                messages.success(
                    request,
                    f"Ingrediente '{item.ingrediente.nome}' ({item.quantidade_padrao} {item.get_unidade_medida_display()}) adicionado a {receita.nome}!"
                )
        else:
            for erro in form.errors.values():
                messages.error(request, erro)
    return redirect('cardapio_detalhe', pk=receita.cardapio_id)


@login_required
def item_receita_excluir_view(request, pk):
    """Remove um ingrediente de uma preparação."""
    if not pode_gerenciar_cadastros(request.user):
        messages.error(request, "Permissão negada para remover ingredientes de receitas.")
        return redirect('cardapio_lista')

    item = get_object_or_404(ItemReceita, pk=pk)
    cardapio_id = item.receita.cardapio_id
    ing_nome = item.ingrediente.nome
    rec_nome = item.receita.nome

    if request.method == 'POST':
        item.delete()
        messages.success(request, f"Ingrediente '{ing_nome}' removido de '{rec_nome}'.")
    return redirect('cardapio_detalhe', pk=cardapio_id)


# ========================================================
# MÓDULO DE CÁLCULO E CONFERÊNCIA DE INGREDIENTES
# ========================================================

@login_required
def calculo_detalhe_view(request, pk=None):
    """Visualização da tela de resultado do cálculo com lista legível à distância de um braço."""
    hoje = timezone.localdate()

    if pk:
        calculo = get_object_or_404(
            CalculoDiario.objects.select_related(
                'cardapio', 'frequencia', 'usuario_responsavel'
            ).prefetch_related('itens__ingrediente'),
            pk=pk
        )
    else:
        # Busca cálculo do dia de hoje
        calculo = CalculoDiario.objects.filter(
            data_calculo=hoje
        ).select_related(
            'cardapio', 'frequencia', 'usuario_responsavel'
        ).prefetch_related('itens__ingrediente').first()

    context = {
        'calculo': calculo,
        'hoje': hoje,
        'ajuste_form': ItemCalculoAjusteForm(),
        'pode_gerenciar': pode_gerenciar_cadastros(request.user),
    }
    return render(request, 'calculos/detalhe.html', context)


@login_required
def calculo_lista_view(request):
    """Histórico de todos os cálculos diários gerados."""
    calculos = CalculoDiario.objects.select_related(
        'cardapio', 'frequencia', 'usuario_responsavel'
    ).order_by('-data_calculo', '-gerado_em')

    context = {
        'calculos': calculos,
        'hoje': timezone.localdate(),
    }
    return render(request, 'calculos/lista.html', context)


@refeitorio_requerido
def calculo_conferir_view(request, pk):
    """Marca ou desmarca um cálculo diário como conferido pelo refeitório."""
    calculo = get_object_or_404(CalculoDiario, pk=pk)

    if request.method == 'POST':
        calculo.conferido = not calculo.conferido
        calculo.usuario_responsavel = request.user
        calculo.save()

        status_str = "conferido e aprovado para preparo" if calculo.conferido else "marcado como pendente de conferência"
        messages.success(request, f"Cálculo diário {status_str} com sucesso!")
    return redirect('calculo_detalhe', pk=calculo.pk)


@refeitorio_requerido
def calculo_gerar_view(request):
    """Gera um novo cálculo proporcional cruzando cardápio e frequência selecionados."""
    hoje = timezone.localdate()

    if request.method == 'POST':
        form = CalculoGerarForm(request.POST)
        if form.is_valid():
            cardapio = form.cleaned_data['cardapio']
            frequencia = form.cleaned_data['frequencia']
            calculo = CalculoService.processar_calculo(
                cardapio=cardapio,
                frequencia=frequencia,
                usuario=request.user,
                forcar_recalculo=True
            )
            messages.success(
                request,
                f"Cálculo gerado com sucesso para {frequencia.total_estudantes_presentes} alunos ({cardapio.nome})!"
            )
            return redirect('calculo_detalhe', pk=calculo.pk)
    else:
        cardapio_sugerido = Cardapio.objects.filter(ativo=True).first()
        frequencia_sugerida = FrequenciaDiaria.objects.filter(data_refeicao=hoje).first()
        form = CalculoGerarForm(initial={
            'cardapio': cardapio_sugerido,
            'frequencia': frequencia_sugerida,
        })

    context = {
        'form': form,
        'hoje': hoje,
    }
    return render(request, 'calculos/gerar.html', context)


@refeitorio_requerido
def calculo_ajustar_item_view(request, pk):
    """Ajuste manual com justificativa obrigatória (RF09) de um item calculado."""
    item = get_object_or_404(ItemCalculo, pk=pk)

    if request.method == 'POST':
        form = ItemCalculoAjusteForm(request.POST, instance=item)
        if form.is_valid():
            item_ajustado = form.save()
            messages.success(
                request,
                f"Ajuste registrado para {item_ajustado.ingrediente.nome}: {item_ajustado.quantidade_ajustada} {item_ajustado.get_unidade_medida_display()}."
            )
        else:
            for erro in form.errors.values():
                messages.error(request, erro)
    return redirect('calculo_detalhe', pk=item.calculo_id)


# ========================================================
# EXPORTAÇÃO E IMPRESSÃO DO RESUMO DIÁRIO (RF11)
# ========================================================

@login_required
def calculo_imprimir_view(request, pk):
    """
    Exibe a Ficha de Produção e Controle Diário formatada para impressão (A4/prancheta).
    Inclui cabeçalho institucional, dados de presença, checklist de ingredientes [ ],
    instruções das preparações e campo para assinaturas das merendeiras e nutricionista.
    """
    calculo = get_object_or_404(
        CalculoDiario.objects.select_related('cardapio', 'frequencia', 'usuario_responsavel'),
        pk=pk
    )
    itens = calculo.itens.select_related('ingrediente').order_by('ingrediente__nome')
    receitas = calculo.cardapio.receitas.prefetch_related('itens__ingrediente').all()

    context = {
        'calculo': calculo,
        'itens': itens,
        'receitas': receitas,
        'data_emissao': timezone.now(),
        'emitido_por': request.user,
    }
    return render(request, 'calculos/imprimir.html', context)


@login_required
def calculo_exportar_csv_view(request, pk):
    """
    Exporta o resumo diário de cálculo de ingredientes em formato CSV tabular.
    Utiliza codificação UTF-8 com BOM (\ufeff) e separador ponto-e-vírgula (;)
    garantindo compatibilidade nativa com Microsoft Excel e LibreOffice Calc em português.
    """
    calculo = get_object_or_404(
        CalculoDiario.objects.select_related('cardapio', 'frequencia', 'usuario_responsavel'),
        pk=pk
    )
    itens = calculo.itens.select_related('ingrediente').order_by('ingrediente__nome')

    data_formatada = calculo.frequencia.data_refeicao.strftime('%d/%m/%Y')
    data_arquivo = calculo.frequencia.data_refeicao.strftime('%Y-%m-%d')
    turno_slug = slugify(calculo.frequencia.get_refeicao_turno_display())
    filename = f"SPAE_Resumo_Diario_{data_arquivo}_{turno_slug}.csv"

    response = HttpResponse(content_type='text/csv; charset=utf-8')
    response['Content-Disposition'] = f'attachment; filename="{filename}"'

    # Adiciona o BOM do UTF-8 para o Excel reconhecer automaticamente a acentuação
    response.write('\ufeff')

    writer = csv.writer(response, delimiter=';')

    # Cabeçalho Tabular
    writer.writerow([
        'Data da Refeição',
        'Turno / Refeição',
        'Cardápio',
        'Estudantes Presentes',
        'Ingrediente',
        'Quantidade Calculada',
        'Unidade de Medida',
        'Quantidade Ajustada',
        'Justificativa do Ajuste',
        'Status da Conferência',
        'Responsável pelo Registro',
        'Data/Hora de Geração',
    ])

    status_conferencia = 'Conferido' if calculo.conferido else 'Pendente'
    responsavel_nome = (
        calculo.usuario_responsavel.nome_completo
        if calculo.usuario_responsavel and calculo.usuario_responsavel.nome_completo
        else (calculo.usuario_responsavel.username if calculo.usuario_responsavel else 'Não informado')
    )
    gerado_em_str = calculo.gerado_em.strftime('%d/%m/%Y %H:%M:%S') if calculo.gerado_em else ''

    for item in itens:
        # Formata os valores decimais com vírgula para convenção brasileira de planilhas
        qtd_calculada_str = str(item.quantidade_calculada).replace('.', ',')
        qtd_ajustada_str = str(item.quantidade_ajustada).replace('.', ',') if item.quantidade_ajustada is not None else ''

        writer.writerow([
            data_formatada,
            calculo.frequencia.get_refeicao_turno_display(),
            calculo.cardapio.nome,
            calculo.frequencia.total_estudantes_presentes,
            item.ingrediente.nome,
            qtd_calculada_str,
            item.get_unidade_medida_display(),
            qtd_ajustada_str,
            item.justificativa_ajuste or '',
            status_conferencia,
            responsavel_nome,
            gerado_em_str,
        ])

    return response
