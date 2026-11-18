from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.test import TestCase

from .models import Ingrediente, PerfilUsuario, UnidadeMedida, Usuario


class UsuarioModelTest(TestCase):
    def test_criar_usuario_refeitorio_padrao(self):
        user = Usuario.objects.create_user(
            username='merendeira1',
            password='senha_segura_123',
            nome_completo='Maria da Silva'
        )
        self.assertEqual(user.perfil, PerfilUsuario.REFEITORIO)
        self.assertTrue(user.ativo)
        self.assertTrue(user.is_active)
        self.assertEqual(user.first_name, 'Maria')
        self.assertEqual(user.last_name, 'da Silva')
        self.assertIn('Maria da Silva', str(user))
        self.assertIn('Refeitório', str(user))

    def test_perfis_disponiveis(self):
        perfis = [
            (PerfilUsuario.REFEITORIO, 'refeitorio'),
            (PerfilUsuario.FREQUENCIA, 'frequencia'),
            (PerfilUsuario.GESTAO, 'gestao'),
            (PerfilUsuario.ADMIN, 'admin'),
        ]
        for enum_val, expected_str in perfis:
            self.assertEqual(enum_val, expected_str)

    def test_sincronizacao_usuario_inativo(self):
        user = Usuario.objects.create_user(
            username='usuario_inativo',
            password='senha_segura_123',
            ativo=False
        )
        self.assertFalse(user.ativo)
        self.assertFalse(user.is_active)


class IngredienteModelTest(TestCase):
    def test_criar_ingrediente_valido(self):
        ingrediente = Ingrediente.objects.create(
            nome='Arroz Branco Tipo 1',
            unidade_padrao=UnidadeMedida.QUILOGRAMA,
            observacoes='Guardar em local seco e arejado.'
        )
        self.assertEqual(ingrediente.nome, 'Arroz Branco Tipo 1')
        self.assertEqual(ingrediente.unidade_padrao, 'kg')
        self.assertIn('Arroz Branco Tipo 1', str(ingrediente))
        self.assertIn('kg', str(ingrediente))

    def test_nome_ingrediente_unico(self):
        Ingrediente.objects.create(
            nome='Feijão Carioca',
            unidade_padrao=UnidadeMedida.QUILOGRAMA
        )
        with self.assertRaises(IntegrityError):
            Ingrediente.objects.create(
                nome='Feijão Carioca',
                unidade_padrao=UnidadeMedida.GRAMA
            )

    def test_todas_unidades_medida_previstas(self):
        unidades = ['g', 'kg', 'ml', 'L', 'un']
        for un in unidades:
            ing = Ingrediente(nome=f'Ingrediente {un}', unidade_padrao=un)
            ing.full_clean()  # não deve levantar ValidationError
