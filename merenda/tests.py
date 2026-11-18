from decimal import Decimal
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.db.models import ProtectedError
from django.test import TestCase

from .models import (
    BaseCalculo,
    Cardapio,
    Ingrediente,
    ItemReceita,
    PerfilUsuario,
    ReceitaFichaTecnica,
    TipoRefeicao,
    UnidadeMedida,
    Usuario,
)


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
            ing.full_clean()


class CardapioReceitaItemTest(TestCase):
    def setUp(self):
        self.cardapio = Cardapio.objects.create(
            nome='Almoço Segunda-Feira',
            refeicao=TipoRefeicao.ALMOCO,
            descricao='Refeição balanceada da segunda'
        )
        self.receita = ReceitaFichaTecnica.objects.create(
            cardapio=self.cardapio,
            nome='Arroz Branco Soltinho',
            fator_rendimento=Decimal('1.000')
        )
        self.arroz = Ingrediente.objects.create(
            nome='Arroz Agulhinha Tipo 1',
            unidade_padrao=UnidadeMedida.QUILOGRAMA
        )
        self.oleo = Ingrediente.objects.create(
            nome='Óleo de Soja',
            unidade_padrao=UnidadeMedida.LITRO
        )

    def test_criar_cardapio_valido(self):
        self.assertEqual(self.cardapio.nome, 'Almoço Segunda-Feira')
        self.assertEqual(self.cardapio.refeicao, TipoRefeicao.ALMOCO)
        self.assertTrue(self.cardapio.ativo)
        self.assertIn('Almoço Segunda-Feira', str(self.cardapio))

    def test_criar_receita_ficha_tecnica(self):
        self.assertEqual(self.receita.cardapio, self.cardapio)
        self.assertEqual(self.receita.nome, 'Arroz Branco Soltinho')
        self.assertEqual(self.receita.fator_rendimento, Decimal('1.000'))
        self.assertIn('Arroz Branco Soltinho', str(self.receita))

    def test_fator_rendimento_invalido_dispara_erro(self):
        receita_invalida = ReceitaFichaTecnica(
            cardapio=self.cardapio,
            nome='Receita com rendimento zero',
            fator_rendimento=Decimal('0.000')
        )
        with self.assertRaises(ValidationError):
            receita_invalida.full_clean()

    def test_criar_item_receita(self):
        item = ItemReceita.objects.create(
            receita=self.receita,
            ingrediente=self.arroz,
            quantidade_padrao=Decimal('0.0800'),
            unidade_medida=UnidadeMedida.QUILOGRAMA,
            base_calculo=BaseCalculo.POR_ALUNO
        )
        self.assertEqual(item.receita, self.receita)
        self.assertEqual(item.ingrediente, self.arroz)
        self.assertEqual(item.quantidade_padrao, Decimal('0.0800'))
        self.assertEqual(item.base_calculo, BaseCalculo.POR_ALUNO)
        self.assertIn('Arroz Agulhinha Tipo 1', str(item))

    def test_quantidade_padrao_negativa_ou_zero_dispara_erro(self):
        item_invalido = ItemReceita(
            receita=self.receita,
            ingrediente=self.oleo,
            quantidade_padrao=Decimal('0.0000'),
            unidade_medida=UnidadeMedida.LITRO,
            base_calculo=BaseCalculo.POR_ALUNO
        )
        with self.assertRaises(ValidationError):
            item_invalido.full_clean()

    def test_ingrediente_duplicado_na_mesma_receita_bloqueado(self):
        ItemReceita.objects.create(
            receita=self.receita,
            ingrediente=self.arroz,
            quantidade_padrao=Decimal('0.0800'),
            unidade_medida=UnidadeMedida.QUILOGRAMA,
            base_calculo=BaseCalculo.POR_ALUNO
        )
        with self.assertRaises(IntegrityError):
            ItemReceita.objects.create(
                receita=self.receita,
                ingrediente=self.arroz,
                quantidade_padrao=Decimal('0.0500'),
                unidade_medida=UnidadeMedida.QUILOGRAMA,
                base_calculo=BaseCalculo.POR_ALUNO
            )

    def test_delecao_protegida_de_ingrediente_em_uso(self):
        ItemReceita.objects.create(
            receita=self.receita,
            ingrediente=self.arroz,
            quantidade_padrao=Decimal('0.0800'),
            unidade_medida=UnidadeMedida.QUILOGRAMA
        )
        with self.assertRaises(ProtectedError):
            self.arroz.delete()
