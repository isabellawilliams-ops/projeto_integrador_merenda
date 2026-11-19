from datetime import date
from decimal import Decimal
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.db.models import ProtectedError
from django.test import TestCase

from .models import (
    BaseCalculo,
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


class FrequenciaECalculoDiarioTest(TestCase):
    def setUp(self):
        self.usuario_portaria = Usuario.objects.create_user(
            username='portaria1',
            password='senha_segura_123',
            nome_completo='João Secretário',
            perfil=PerfilUsuario.FREQUENCIA
        )
        self.usuario_merendeira = Usuario.objects.create_user(
            username='merendeira_chefe',
            password='senha_segura_123',
            nome_completo='Dona Benta',
            perfil=PerfilUsuario.REFEITORIO
        )
        self.cardapio = Cardapio.objects.create(
            nome='Almoço Terça',
            refeicao=TipoRefeicao.ALMOCO
        )
        self.feijao = Ingrediente.objects.create(
            nome='Feijão Preto',
            unidade_padrao=UnidadeMedida.QUILOGRAMA
        )
        self.frequencia = FrequenciaDiaria.objects.create(
            usuario_registro=self.usuario_portaria,
            data_refeicao=date(2026, 11, 18),
            refeicao_turno=TipoRefeicao.ALMOCO,
            total_estudantes_presentes=150
        )

    def test_criar_frequencia_diaria(self):
        self.assertEqual(self.frequencia.total_estudantes_presentes, 150)
        self.assertEqual(self.frequencia.usuario_registro, self.usuario_portaria)
        self.assertIn('150 alunos', str(self.frequencia))

    def test_unicidade_frequencia_mesma_data_e_refeicao(self):
        with self.assertRaises(IntegrityError):
            FrequenciaDiaria.objects.create(
                usuario_registro=self.usuario_portaria,
                data_refeicao=date(2026, 11, 18),
                refeicao_turno=TipoRefeicao.ALMOCO,
                total_estudantes_presentes=160
            )

    def test_criar_calculo_diario(self):
        calc = CalculoDiario.objects.create(
            cardapio=self.cardapio,
            frequencia=self.frequencia,
            usuario_responsavel=self.usuario_merendeira,
            data_calculo=date(2026, 11, 18),
            conferido=False
        )
        self.assertFalse(calc.conferido)
        self.assertEqual(calc.frequencia.total_estudantes_presentes, 150)
        self.assertIn('Pendente de Conferência', str(calc))

    def test_item_calculo_sem_ajuste(self):
        calc = CalculoDiario.objects.create(
            cardapio=self.cardapio,
            frequencia=self.frequencia,
            usuario_responsavel=self.usuario_merendeira,
            data_calculo=date(2026, 11, 18)
        )
        item = ItemCalculo.objects.create(
            calculo=calc,
            ingrediente=self.feijao,
            quantidade_calculada=Decimal('9.0000'),
            unidade_medida=UnidadeMedida.QUILOGRAMA
        )
        self.assertEqual(item.quantidade_final, Decimal('9.0000'))
        self.assertIn('Feijão Preto', str(item))

    def test_rf09_ajuste_com_justificativa_sucesso(self):
        calc = CalculoDiario.objects.create(
            cardapio=self.cardapio,
            frequencia=self.frequencia,
            usuario_responsavel=self.usuario_merendeira,
            data_calculo=date(2026, 11, 18)
        )
        item = ItemCalculo(
            calculo=calc,
            ingrediente=self.feijao,
            quantidade_calculada=Decimal('9.0000'),
            quantidade_ajustada=Decimal('10.5000'),
            justificativa_ajuste='Acréscimo autorizado devido à visita pedagógica de outra escola.',
            unidade_medida=UnidadeMedida.QUILOGRAMA
        )
        item.full_clean()
        item.save()
        self.assertEqual(item.quantidade_final, Decimal('10.5000'))

    def test_rf09_ajuste_sem_justificativa_falha(self):
        calc = CalculoDiario.objects.create(
            cardapio=self.cardapio,
            frequencia=self.frequencia,
            usuario_responsavel=self.usuario_merendeira,
            data_calculo=date(2026, 11, 18)
        )
        item = ItemCalculo(
            calculo=calc,
            ingrediente=self.feijao,
            quantidade_calculada=Decimal('9.0000'),
            quantidade_ajustada=Decimal('10.5000'),
            justificativa_ajuste='',  # Sem justificativa obrigatória
            unidade_medida=UnidadeMedida.QUILOGRAMA
        )
        with self.assertRaises(ValidationError) as ctx:
            item.full_clean()
        self.assertIn('justificativa_ajuste', ctx.exception.message_dict)

    def test_ajuste_negativo_falha(self):
        calc = CalculoDiario.objects.create(
            cardapio=self.cardapio,
            frequencia=self.frequencia,
            usuario_responsavel=self.usuario_merendeira,
            data_calculo=date(2026, 11, 18)
        )
        item = ItemCalculo(
            calculo=calc,
            ingrediente=self.feijao,
            quantidade_calculada=Decimal('9.0000'),
            quantidade_ajustada=Decimal('-1.0000'),
            justificativa_ajuste='Teste',
            unidade_medida=UnidadeMedida.QUILOGRAMA
        )
        with self.assertRaises(ValidationError):
            item.full_clean()

    def test_protecao_frequencia_referenciada_por_calculo(self):
        CalculoDiario.objects.create(
            cardapio=self.cardapio,
            frequencia=self.frequencia,
            usuario_responsavel=self.usuario_merendeira,
            data_calculo=date(2026, 11, 18)
        )
        with self.assertRaises(ProtectedError):
            self.frequencia.delete()


class AutenticacaoViewsTest(TestCase):
    def setUp(self):
        self.user = Usuario.objects.create_user(
            username='merendeira_teste',
            password='senha_correta_123',
            nome_completo='Dona Lurdes',
            perfil=PerfilUsuario.REFEITORIO
        )
        self.user_inativo = Usuario.objects.create_user(
            username='usuario_desativado',
            password='senha_correta_123',
            ativo=False
        )

    def test_tela_login_carrega_sucesso(self):
        response = self.client.get('/login/')
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'login.html')
        self.assertContains(response, 'SPAE')
        self.assertContains(response, 'Entrar no Sistema')

    def test_pagina_protegida_redireciona_para_login(self):
        response = self.client.get('/')
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.startswith('/login/'))

    def test_login_sucesso(self):
        response = self.client.post('/login/', {
            'username': 'merendeira_teste',
            'password': 'senha_correta_123',
        }, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context['user'].is_authenticated)
        self.assertContains(response, 'Dona Lurdes')
        self.assertContains(response, 'Refeitório (Merendeira)')

    def test_login_senha_incorreta(self):
        response = self.client.post('/login/', {
            'username': 'merendeira_teste',
            'password': 'senha_errada_xyz',
        })
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.context['user'].is_authenticated)
        self.assertContains(response, 'Usuário ou senha incorretos')

    def test_login_usuario_inativo_bloqueado(self):
        response = self.client.post('/login/', {
            'username': 'usuario_desativado',
            'password': 'senha_correta_123',
        })
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.context['user'].is_authenticated)

    def test_logout_sucesso(self):
        self.client.login(username='merendeira_teste', password='senha_correta_123')
        response = self.client.get('/logout/', follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.context['user'].is_authenticated)
        self.assertTemplateUsed(response, 'login.html')

    def test_usuario_autenticado_acessando_login_redirecionado(self):
        self.client.login(username='merendeira_teste', password='senha_correta_123')
        response = self.client.get('/login/')
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, '/')

