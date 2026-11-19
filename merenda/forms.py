from decimal import Decimal
from django import forms
from django.contrib.auth import authenticate
from django.contrib.auth.forms import AuthenticationForm, PasswordChangeForm
from django.core.exceptions import ValidationError

from .models import (
    BaseCalculo,
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

    def clean(self):
        username = self.cleaned_data.get("username")
        password = self.cleaned_data.get("password")

        if username is not None and password:
            self.user_cache = authenticate(
                self.request, username=username, password=password
            )
            if self.user_cache is None:
                # Se falhar a autenticação, verifica se o usuário existe com credenciais corretas mas inativo
                try:
                    user_existente = Usuario.objects.get(username=username)
                    if user_existente.check_password(password) and (not user_existente.ativo or not user_existente.is_active):
                        self.confirm_login_allowed(user_existente)
                except Usuario.DoesNotExist:
                    pass
                raise self.get_invalid_login_error()
            else:
                self.confirm_login_allowed(self.user_cache)

        return self.cleaned_data


class FrequenciaDiariaForm(forms.ModelForm):
    class Meta:
        model = FrequenciaDiaria
        fields = ['data_refeicao', 'refeicao_turno', 'total_estudantes_presentes']
        widgets = {
            'data_refeicao': forms.DateInput(
                attrs={
                    'type': 'date',
                    'class': 'form-control form-control-lg',
                    'id': 'id_data_refeicao',
                }
            ),
            'refeicao_turno': forms.Select(
                attrs={
                    'class': 'form-select form-select-lg',
                    'id': 'id_refeicao_turno',
                }
            ),
            'total_estudantes_presentes': forms.NumberInput(
                attrs={
                    'class': 'form-control form-control-lg',
                    'inputmode': 'numeric',
                    'placeholder': 'Ex: 120',
                    'min': '1',
                    'id': 'id_total_estudantes',
                }
            ),
        }
        labels = {
            'data_refeicao': 'Data da Refeição',
            'refeicao_turno': 'Turno / Refeição',
            'total_estudantes_presentes': 'Total de Estudantes Presentes',
        }
        help_texts = {
            'total_estudantes_presentes': 'Informe o número exato de alunos que receberão esta refeição.',
        }

    def clean_total_estudantes_presentes(self):
        total = self.cleaned_data.get('total_estudantes_presentes')
        if total is None or total <= 0:
            raise forms.ValidationError("A quantidade de estudantes deve ser maior que zero.")
        return total


class CalculoGerarForm(forms.Form):
    cardapio = forms.ModelChoiceField(
        queryset=Cardapio.objects.filter(ativo=True),
        label="Cardápio Previsto",
        widget=forms.Select(attrs={'class': 'form-select form-select-lg'}),
        empty_label="Selecione o cardápio da refeição...",
    )
    frequencia = forms.ModelChoiceField(
        queryset=FrequenciaDiaria.objects.all().order_by('-data_refeicao'),
        label="Frequência de Estudantes",
        widget=forms.Select(attrs={'class': 'form-select form-select-lg'}),
        empty_label="Selecione a frequência do dia...",
    )


class ItemCalculoAjusteForm(forms.ModelForm):
    class Meta:
        model = ItemCalculo
        fields = ['quantidade_ajustada', 'justificativa_ajuste']
        widgets = {
            'quantidade_ajustada': forms.NumberInput(
                attrs={
                    'class': 'form-control form-control-lg',
                    'step': '0.001',
                    'min': '0',
                    'placeholder': 'Digite a quantidade corrigida...',
                }
            ),
            'justificativa_ajuste': forms.Textarea(
                attrs={
                    'class': 'form-control',
                    'rows': 3,
                    'placeholder': 'Motivo obrigatório do ajuste (ex: evento comemorativo, sobra anterior reaproveitada)...',
                }
            ),
        }
        labels = {
            'quantidade_ajustada': 'Quantidade Ajustada',
            'justificativa_ajuste': 'Justificativa do Ajuste (Obrigatória - RF09)',
        }


# ========================================================
# FORMULÁRIOS DO MÓDULO DE CADASTROS ADMINISTRATIVOS
# ========================================================

class IngredienteForm(forms.ModelForm):
    class Meta:
        model = Ingrediente
        fields = ['nome', 'unidade_padrao', 'observacoes']
        widgets = {
            'nome': forms.TextInput(
                attrs={
                    'class': 'form-control form-control-lg',
                    'placeholder': 'Ex: Arroz Branco Tipo 1, Feijão Preto...',
                    'autofocus': True,
                }
            ),
            'unidade_padrao': forms.Select(
                attrs={
                    'class': 'form-select form-select-lg',
                }
            ),
            'observacoes': forms.Textarea(
                attrs={
                    'class': 'form-control',
                    'rows': 3,
                    'placeholder': 'Orientações sobre acondicionamento, temperatura ou manuseio...',
                }
            ),
        }
        labels = {
            'nome': 'Nome do Ingrediente',
            'unidade_padrao': 'Unidade Padrão de Medida',
            'observacoes': 'Observações de Armazenamento e Uso',
        }


class CardapioForm(forms.ModelForm):
    class Meta:
        model = Cardapio
        fields = ['nome', 'refeicao', 'data_referencia', 'descricao', 'ativo']
        widgets = {
            'nome': forms.TextInput(
                attrs={
                    'class': 'form-control form-control-lg',
                    'placeholder': 'Ex: Almoço Terça-feira Especial, Lanche Matutino...',
                    'autofocus': True,
                }
            ),
            'refeicao': forms.Select(
                attrs={
                    'class': 'form-select form-select-lg',
                }
            ),
            'data_referencia': forms.DateInput(
                attrs={
                    'type': 'date',
                    'class': 'form-control form-control-lg',
                }
            ),
            'descricao': forms.Textarea(
                attrs={
                    'class': 'form-control',
                    'rows': 3,
                    'placeholder': 'Detalhamento do cardápio ou orientações nutricionais...',
                }
            ),
            'ativo': forms.CheckboxInput(
                attrs={
                    'class': 'form-check-input fs-5',
                }
            ),
        }
        labels = {
            'nome': 'Nome do Cardápio',
            'refeicao': 'Tipo de Refeição',
            'data_referencia': 'Data Prevista / Referência (Opcional)',
            'descricao': 'Descrição e Observações Nutricionais',
            'ativo': 'Cardápio Ativo para Planejamento',
        }


class ReceitaFichaTecnicaForm(forms.ModelForm):
    class Meta:
        model = ReceitaFichaTecnica
        fields = ['nome', 'fator_rendimento', 'modo_preparo']
        widgets = {
            'nome': forms.TextInput(
                attrs={
                    'class': 'form-control form-control-lg',
                    'placeholder': 'Ex: Arroz Branco Soltinho, Frango Ensopado...',
                    'autofocus': True,
                }
            ),
            'fator_rendimento': forms.NumberInput(
                attrs={
                    'class': 'form-control form-control-lg',
                    'step': '0.001',
                    'min': '0.001',
                    'placeholder': '1.000',
                }
            ),
            'modo_preparo': forms.Textarea(
                attrs={
                    'class': 'form-control',
                    'rows': 4,
                    'placeholder': 'Instruções de cocção, etapas de pré-preparo e boas práticas...',
                }
            ),
        }
        labels = {
            'nome': 'Nome da Preparação / Receita',
            'fator_rendimento': 'Fator de Rendimento / Perda',
            'modo_preparo': 'Modo de Preparo para o Refeitório',
        }
        help_texts = {
            'fator_rendimento': 'Multiplicador padrão 1.000 (ajustável para contração ou descarte validado).',
        }


class ItemReceitaForm(forms.ModelForm):
    class Meta:
        model = ItemReceita
        fields = ['ingrediente', 'quantidade_padrao', 'unidade_medida', 'base_calculo']
        widgets = {
            'ingrediente': forms.Select(
                attrs={
                    'class': 'form-select form-select-lg',
                }
            ),
            'quantidade_padrao': forms.NumberInput(
                attrs={
                    'class': 'form-control form-control-lg',
                    'step': '0.0001',
                    'min': '0.0001',
                    'placeholder': 'Ex: 0.0800',
                }
            ),
            'unidade_medida': forms.Select(
                attrs={
                    'class': 'form-select form-select-lg',
                }
            ),
            'base_calculo': forms.Select(
                attrs={
                    'class': 'form-select form-select-lg',
                }
            ),
        }
        labels = {
            'ingrediente': 'Ingrediente',
            'quantidade_padrao': 'Quantidade Padrão',
            'unidade_medida': 'Unidade de Medida',
            'base_calculo': 'Base de Cálculo',
        }


# ========================================================
# FORMULÁRIOS DE GESTÃO DE USUÁRIOS E PERFIS (RF01 - RBAC)
# ========================================================

class UsuarioCriacaoForm(forms.ModelForm):
    """Criação de novos usuários do SPAE com perfil e senha inicial pelo Administrador."""
    password = forms.CharField(
        label="Senha Inicial",
        widget=forms.PasswordInput(
            attrs={
                'class': 'form-control form-control-lg',
                'placeholder': 'Mínimo de 6 caracteres...',
                'autocomplete': 'new-password',
            }
        ),
        min_length=6,
        help_text="A senha deve ter pelo menos 6 caracteres."
    )
    password_confirm = forms.CharField(
        label="Confirmar Senha",
        widget=forms.PasswordInput(
            attrs={
                'class': 'form-control form-control-lg',
                'placeholder': 'Repita a senha inicial...',
                'autocomplete': 'new-password',
            }
        ),
        help_text="Repita exatamente a mesma senha digitada acima."
    )

    class Meta:
        model = Usuario
        fields = ['username', 'nome_completo', 'perfil', 'ativo']
        widgets = {
            'username': forms.TextInput(
                attrs={
                    'class': 'form-control form-control-lg',
                    'placeholder': 'Ex: maria.refeitorio, lucas.secretaria...',
                    'autocomplete': 'username',
                }
            ),
            'nome_completo': forms.TextInput(
                attrs={
                    'class': 'form-control form-control-lg',
                    'placeholder': 'Nome completo do profissional...',
                }
            ),
            'perfil': forms.Select(
                attrs={
                    'class': 'form-select form-select-lg',
                }
            ),
            'ativo': forms.CheckboxInput(
                attrs={
                    'class': 'form-check-input fs-5',
                    'role': 'switch',
                }
            ),
        }
        labels = {
            'username': 'Login de Acesso (Username)',
            'nome_completo': 'Nome Completo',
            'perfil': 'Perfil de Acesso (Papel RBAC)',
            'ativo': 'Conta Ativa para Acesso',
        }
        help_texts = {
            'username': 'Identificador único sem espaços ou caracteres especiais.',
            'perfil': 'Define as telas e ações autorizadas (Refeitório, Frequência, Gestão ou Administrador).',
        }

    def clean(self):
        cleaned_data = super().clean()
        pwd = cleaned_data.get('password')
        pwd_confirm = cleaned_data.get('password_confirm')
        if pwd and pwd_confirm and pwd != pwd_confirm:
            self.add_error('password_confirm', "As senhas informadas não conferem. Digite novamente.")
        return cleaned_data

    def save(self, commit=True):
        usuario = super().save(commit=False)
        usuario.set_password(self.cleaned_data['password'])
        if commit:
            usuario.save()
        return usuario


class UsuarioEdicaoForm(forms.ModelForm):
    """Edição dos dados cadastrais, perfil de acesso e status de usuário pelo Administrador."""
    class Meta:
        model = Usuario
        fields = ['nome_completo', 'perfil', 'ativo']
        widgets = {
            'nome_completo': forms.TextInput(
                attrs={
                    'class': 'form-control form-control-lg',
                    'placeholder': 'Nome completo do profissional...',
                }
            ),
            'perfil': forms.Select(
                attrs={
                    'class': 'form-select form-select-lg',
                }
            ),
            'ativo': forms.CheckboxInput(
                attrs={
                    'class': 'form-check-input fs-5',
                    'role': 'switch',
                }
            ),
        }
        labels = {
            'nome_completo': 'Nome Completo',
            'perfil': 'Perfil de Acesso (Papel RBAC)',
            'ativo': 'Conta Ativa para Acesso',
        }


class UsuarioRedefinirSenhaForm(forms.Form):
    """Redefinição direta de senha de usuário pelo Administrador."""
    nova_senha = forms.CharField(
        label="Nova Senha",
        widget=forms.PasswordInput(
            attrs={
                'class': 'form-control form-control-lg',
                'placeholder': 'Digite a nova senha (mínimo 6 caracteres)...',
                'autocomplete': 'new-password',
            }
        ),
        min_length=6,
        help_text="Defina uma nova senha com no mínimo 6 caracteres para o usuário."
    )
    confirmar_nova_senha = forms.CharField(
        label="Confirmar Nova Senha",
        widget=forms.PasswordInput(
            attrs={
                'class': 'form-control form-control-lg',
                'placeholder': 'Repita a nova senha...',
                'autocomplete': 'new-password',
            }
        )
    )

    def clean(self):
        cleaned_data = super().clean()
        s1 = cleaned_data.get('nova_senha')
        s2 = cleaned_data.get('confirmar_nova_senha')
        if s1 and s2 and s1 != s2:
            self.add_error('confirmar_nova_senha', "As senhas não conferem. Por favor, digite novamente.")
        return cleaned_data


class MeuPerfilForm(forms.ModelForm):
    """Permite ao próprio usuário logado atualizar suas informações básicas de identificação."""
    class Meta:
        model = Usuario
        fields = ['nome_completo']
        widgets = {
            'nome_completo': forms.TextInput(
                attrs={
                    'class': 'form-control form-control-lg',
                    'placeholder': 'Seu nome completo...',
                }
            ),
        }
        labels = {
            'nome_completo': 'Seu Nome Completo',
        }


class AlterarPropriaSenhaForm(PasswordChangeForm):
    """Formulário para o próprio usuário alterar sua senha com estilização Bootstrap 5."""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name in self.fields:
            self.fields[field_name].widget.attrs.update({
                'class': 'form-control form-control-lg',
            })

