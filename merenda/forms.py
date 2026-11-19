from django import forms
from django.contrib.auth.forms import AuthenticationForm


class LoginForm(AuthenticationForm):
    username = forms.CharField(
        label="Usuário de Acesso",
        widget=forms.TextInput(
            attrs={
                'class': 'form-control form-control-lg',
                'placeholder': 'Digite seu usuário...',
                'autocomplete': 'username',
                'autocapitalize': 'none',
                'autofocus': True,
                'id': 'id_username',
            }
        ),
    )
    password = forms.CharField(
        label="Senha",
        widget=forms.PasswordInput(
            attrs={
                'class': 'form-control form-control-lg',
                'placeholder': 'Digite sua senha...',
                'autocomplete': 'current-password',
                'id': 'id_password',
            }
        ),
    )

    error_messages = {
        'invalid_login': (
            "Usuário ou senha incorretos. Por favor, verifique seus dados e tente novamente."
        ),
        'inactive': (
            "Esta conta de usuário está desativada. Entre em contato com a gestão escolar ou coordenação."
        ),
    }
