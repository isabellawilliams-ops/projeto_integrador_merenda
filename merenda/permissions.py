"""
Módulo de Permissões e Controle de Acesso Baseado em Papéis (RBAC) - SPAE
RF01: Autenticação de usuários por login e senha com perfis diferenciados.
"""

from functools import wraps
from django.contrib import messages
from django.shortcuts import redirect
from .models import PerfilUsuario, Usuario


def tem_perfil(user: Usuario, *perfis) -> bool:
    """Verifica se o usuário está autenticado e possui ao menos um dos perfis informados."""
    if not user.is_authenticated:
        return False
    if user.is_superuser:
        return True
    return user.perfil in perfis


def pode_gerenciar_usuarios(user: Usuario) -> bool:
    """Apenas Administradores e Superusuários podem gerenciar contas de usuários e senhas."""
    return tem_perfil(user, PerfilUsuario.ADMIN)


def pode_gerenciar_cadastros(user: Usuario) -> bool:
    """Equipe de Gestão (Nutricionista/Direção) e Administradores gerenciam cardápios e ingredientes."""
    return tem_perfil(user, PerfilUsuario.GESTAO, PerfilUsuario.ADMIN)


def pode_lancar_frequencia(user: Usuario) -> bool:
    """Equipe da Secretaria/Portaria, Gestão e Administradores podem registrar presença diária."""
    return tem_perfil(user, PerfilUsuario.FREQUENCIA, PerfilUsuario.GESTAO, PerfilUsuario.ADMIN)


def pode_conferir_calculo(user: Usuario) -> bool:
    """Merendeiras (Refeitório), Gestão e Administradores podem validar e registrar ajustes no cálculo."""
    return tem_perfil(user, PerfilUsuario.REFEITORIO, PerfilUsuario.GESTAO, PerfilUsuario.ADMIN)


def perfil_requerido(*perfis_permitidos, redirect_url='home'):
    """
    Decorator para views que restringe o acesso a um ou mais perfis de usuário específicos.
    Superusuários sempre têm acesso total garantido.
    Caso o usuário não possua autorização, emite mensagem amigável e redireciona.
    """
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return redirect('login')

            if request.user.is_superuser or request.user.perfil in perfis_permitidos:
                return view_func(request, *args, **kwargs)

            perfis_nomes = ", ".join([dict(PerfilUsuario.choices).get(p, p) for p in perfis_permitidos])
            messages.error(
                request,
                f"Acesso não autorizado: seu perfil atual ({request.user.get_perfil_display()}) "
                f"não possui permissão para esta funcionalidade. Perfil necessário: {perfis_nomes}."
            )
            return redirect(redirect_url)
        return _wrapped_view
    return decorator


def admin_requerido(view_func):
    """Decorator atalho: restringe a view exclusivamente para perfil Administrador."""
    return perfil_requerido(PerfilUsuario.ADMIN)(view_func)


def gestao_requerida(view_func):
    """Decorator atalho: restringe a view para Gestão ou Administrador."""
    return perfil_requerido(PerfilUsuario.GESTAO, PerfilUsuario.ADMIN)(view_func)


def frequencia_requerida(view_func):
    """Decorator atalho: restringe a view para Secretaria/Frequência, Gestão ou Administrador."""
    return perfil_requerido(PerfilUsuario.FREQUENCIA, PerfilUsuario.GESTAO, PerfilUsuario.ADMIN)(view_func)


def refeitorio_requerido(view_func):
    """Decorator atalho: restringe a view para Refeitório, Gestão ou Administrador."""
    return perfil_requerido(PerfilUsuario.REFEITORIO, PerfilUsuario.GESTAO, PerfilUsuario.ADMIN)(view_func)
