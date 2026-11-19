from django import forms
from django.contrib.auth.forms import AuthenticationForm

from .models import Cardapio, FrequenciaDiaria, ItemCalculo, TipoRefeicao


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
