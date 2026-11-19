from decimal import Decimal
from django import forms
from django.contrib.auth.forms import AuthenticationForm

from .models import (
    BaseCalculo,
    Cardapio,
    FrequenciaDiaria,
    Ingrediente,
    ItemCalculo,
    ItemReceita,
    ReceitaFichaTecnica,
    TipoRefeicao,
    UnidadeMedida,
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
