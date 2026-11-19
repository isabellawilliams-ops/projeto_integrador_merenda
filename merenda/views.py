from django.contrib import messages
from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView
from django.shortcuts import redirect, render
from django.urls import reverse_lazy
from django.utils import timezone

from .forms import LoginForm
from .models import CalculoDiario, Cardapio, FrequenciaDiaria


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
    """Página inicial pós-login exibindo o perfil do usuário e atalhos operacionais."""
    hoje = timezone.localdate()
    
    total_cardapios = Cardapio.objects.filter(ativo=True).count()
    frequencia_hoje = FrequenciaDiaria.objects.filter(data_refeicao=hoje).first()
    calculos_hoje = CalculoDiario.objects.filter(data_calculo=hoje).count()

    context = {
        'usuario': request.user,
        'hoje': hoje,
        'total_cardapios': total_cardapios,
        'frequencia_hoje': frequencia_hoje,
        'calculos_hoje': calculos_hoje,
    }
    return render(request, 'home.html', context)
