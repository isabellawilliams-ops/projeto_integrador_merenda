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
from .services import CalculoService


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

    def test_dashboard_home_exibe_contexto_e_metricas(self):
        self.client.login(username='merendeira_teste', password='senha_correta_123')
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'home.html')
        self.assertIn('cardapio_hoje', response.context)
        self.assertIn('total_cardapios', response.context)
        self.assertIn('total_ingredientes', response.context)
        self.assertContains(response, 'Planejamento e Refeição de Hoje')
        self.assertContains(response, 'Dona Lurdes')


class FrequenciaViewsTest(TestCase):
    def setUp(self):
        self.user_secretaria = Usuario.objects.create_user(
            username='secretaria_teste',
            password='senha_secretaria_123',
            nome_completo='Ana Secretaria',
            perfil=PerfilUsuario.FREQUENCIA
        )
        self.client.login(username='secretaria_teste', password='senha_secretaria_123')
        self.freq = FrequenciaDiaria.objects.create(
            usuario_registro=self.user_secretaria,
            data_refeicao=date(2026, 11, 20),
            refeicao_turno=TipoRefeicao.ALMOCO,
            total_estudantes_presentes=135
        )

    def test_frequencia_lista_carrega_sucesso(self):
        response = self.client.get('/frequencia/')
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'frequencia/lista.html')
        self.assertContains(response, '135')
        self.assertContains(response, 'Almoço')

    def test_frequencia_lista_filtros(self):
        response = self.client.get('/frequencia/?refeicao=almoco')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['frequencias']), 1)

        response_lanche = self.client.get('/frequencia/?refeicao=lanche_manha')
        self.assertEqual(response_lanche.status_code, 200)
        self.assertEqual(len(response_lanche.context['frequencias']), 0)

    def test_frequencia_registro_get(self):
        response = self.client.get('/frequencia/registrar/')
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'frequencia/form.html')
        self.assertContains(response, 'Confirmar Presença')

    def test_frequencia_registro_post_novo(self):
        response = self.client.post('/frequencia/registrar/', {
            'data_refeicao': '2026-11-21',
            'refeicao_turno': TipoRefeicao.LANCHE_MANHA,
            'total_estudantes_presentes': 140,
        }, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(FrequenciaDiaria.objects.filter(
            data_refeicao=date(2026, 11, 21),
            refeicao_turno=TipoRefeicao.LANCHE_MANHA,
            total_estudantes_presentes=140
        ).exists())

    def test_frequencia_registro_post_atualiza_existente(self):
        response = self.client.post('/frequencia/registrar/', {
            'data_refeicao': '2026-11-20',
            'refeicao_turno': TipoRefeicao.ALMOCO,
            'total_estudantes_presentes': 155,
        }, follow=True)
        self.assertEqual(response.status_code, 200)
        self.freq.refresh_from_db()
        self.assertEqual(self.freq.total_estudantes_presentes, 155)

    def test_frequencia_registro_post_invalido(self):
        response = self.client.post('/frequencia/registrar/', {
            'data_refeicao': '2026-11-20',
            'refeicao_turno': TipoRefeicao.ALMOCO,
            'total_estudantes_presentes': 0,
        })
        self.assertEqual(response.status_code, 200)
        self.assertFormError(response.context['form'], 'total_estudantes_presentes', 'A quantidade de estudantes deve ser maior que zero.')

    def test_frequencia_editar_view(self):
        response = self.client.post(f'/frequencia/{self.freq.id}/editar/', {
            'data_refeicao': '2026-11-20',
            'refeicao_turno': TipoRefeicao.ALMOCO,
            'total_estudantes_presentes': 160,
        }, follow=True)
        self.assertEqual(response.status_code, 200)
        self.freq.refresh_from_db()
        self.assertEqual(self.freq.total_estudantes_presentes, 160)

    def test_frequencia_excluir_view_sem_vinculo(self):
        freq_temp = FrequenciaDiaria.objects.create(
            usuario_registro=self.user_secretaria,
            data_refeicao=date(2026, 11, 22),
            refeicao_turno=TipoRefeicao.ALMOCO,
            total_estudantes_presentes=80
        )
        response = self.client.post(f'/frequencia/{freq_temp.id}/excluir/', follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertFalse(FrequenciaDiaria.objects.filter(id=freq_temp.id).exists())

    def test_frequencia_excluir_bloqueado_quando_vinculado_calculo(self):
        cardapio = Cardapio.objects.create(nome='Cardápio Teste', refeicao=TipoRefeicao.ALMOCO)
        CalculoDiario.objects.create(
            cardapio=cardapio,
            frequencia=self.freq,
            usuario_responsavel=self.user_secretaria,
            data_calculo=date(2026, 11, 20)
        )
        response = self.client.post(f'/frequencia/{self.freq.id}/excluir/', follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(FrequenciaDiaria.objects.filter(id=self.freq.id).exists())
        self.assertContains(response, 'Não é possível excluir esta frequência')


class CadastrosAdministrativosViewsTest(TestCase):
    def setUp(self):
        self.user_nutri = Usuario.objects.create_user(
            username='nutri_cadastros',
            password='senha_nutri_123',
            nome_completo='Dra. Camila Nutricionista',
            perfil=PerfilUsuario.GESTAO
        )
        self.user_merendeira = Usuario.objects.create_user(
            username='merendeira_cadastros',
            password='senha_merenda_123',
            nome_completo='Dona Neide',
            perfil=PerfilUsuario.REFEITORIO
        )
        self.client.login(username='nutri_cadastros', password='senha_nutri_123')
        self.ingrediente = Ingrediente.objects.create(
            nome='Batata Doce Roxa',
            unidade_padrao=UnidadeMedida.QUILOGRAMA,
            observacoes='Tubérculo lavado e seco.'
        )
        self.cardapio = Cardapio.objects.create(
            nome='Lanche Especial da Quarta',
            refeicao=TipoRefeicao.LANCHE_MANHA,
            descricao='Lanche especial saudável.'
        )
        self.receita = ReceitaFichaTecnica.objects.create(
            cardapio=self.cardapio,
            nome='Batata Doce Assada com Canela',
            fator_rendimento=Decimal('1.000'),
            modo_preparo='Cortar e assar em forno industrial a 180°C.'
        )

    def test_hub_cadastros_acesso(self):
        response = self.client.get('/cadastros/')
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'cadastros/hub.html')
        self.assertContains(response, 'Cadastros Administrativos')

    def test_ingredientes_lista_view(self):
        response = self.client.get('/cadastros/ingredientes/')
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'cadastros/ingredientes_lista.html')
        self.assertContains(response, 'Batata Doce Roxa')

    def test_ingrediente_criar_view(self):
        response = self.client.post('/cadastros/ingredientes/novo/', {
            'nome': 'Mandioca Aipim Fresca',
            'unidade_padrao': UnidadeMedida.QUILOGRAMA,
            'observacoes': 'Manter refrigerada.',
        }, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(Ingrediente.objects.filter(nome='Mandioca Aipim Fresca').exists())

    def test_ingrediente_editar_view(self):
        response = self.client.post(f'/cadastros/ingredientes/{self.ingrediente.id}/editar/', {
            'nome': 'Batata Doce Roxa Orgânica',
            'unidade_padrao': UnidadeMedida.QUILOGRAMA,
            'observacoes': 'Lavada.',
        }, follow=True)
        self.assertEqual(response.status_code, 200)
        self.ingrediente.refresh_from_db()
        self.assertEqual(self.ingrediente.nome, 'Batata Doce Roxa Orgânica')

    def test_ingrediente_excluir_sem_vinculo(self):
        ing_livre = Ingrediente.objects.create(nome='Cravo da Índia', unidade_padrao=UnidadeMedida.GRAMA)
        response = self.client.post(f'/cadastros/ingredientes/{ing_livre.id}/excluir/', follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertFalse(Ingrediente.objects.filter(id=ing_livre.id).exists())

    def test_cardapio_lista_view(self):
        response = self.client.get('/cadastros/cardapios/')
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'cadastros/cardapios_lista.html')
        self.assertContains(response, 'Lanche Especial da Quarta')

    def test_cardapio_criar_view(self):
        response = self.client.post('/cadastros/cardapios/novo/', {
            'nome': 'Almoço de Quinta Feijoada Light',
            'refeicao': TipoRefeicao.ALMOCO,
            'descricao': 'Com carnes magras.',
            'ativo': True,
        }, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(Cardapio.objects.filter(nome='Almoço de Quinta Feijoada Light').exists())

    def test_cardapio_detalhe_ficha_tecnica(self):
        response = self.client.get(f'/cadastros/cardapios/{self.cardapio.id}/')
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'cadastros/cardapio_detalhe.html')
        self.assertContains(response, 'Batata Doce Assada com Canela')

    def test_receita_criar_e_item_adicionar_view(self):
        # Cria nova receita no cardápio
        response_rec = self.client.post(f'/cadastros/cardapios/{self.cardapio.id}/receitas/nova/', {
            'nome': 'Suco Natural de Laranja',
            'fator_rendimento': '1.000',
            'modo_preparo': 'Espremer e servir sem açúcar.',
        }, follow=True)
        self.assertEqual(response_rec.status_code, 200)
        rec = ReceitaFichaTecnica.objects.get(nome='Suco Natural de Laranja')

        # Adiciona ingrediente a ela
        response_item = self.client.post(f'/cadastros/receitas/{rec.id}/itens/novo/', {
            'ingrediente': self.ingrediente.id,
            'quantidade_padrao': '0.1000',
            'unidade_medida': UnidadeMedida.QUILOGRAMA,
            'base_calculo': BaseCalculo.POR_ALUNO,
        }, follow=True)
        self.assertEqual(response_item.status_code, 200)
        self.assertTrue(ItemReceita.objects.filter(receita=rec, ingrediente=self.ingrediente).exists())

    def test_merendeira_bloqueada_para_criar_ingrediente(self):
        self.client.login(username='merendeira_cadastros', password='senha_merenda_123')
        response = self.client.post('/cadastros/ingredientes/novo/', {
            'nome': 'Ingrediente Não Autorizado',
            'unidade_padrao': UnidadeMedida.QUILOGRAMA,
        }, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertFalse(Ingrediente.objects.filter(nome='Ingrediente Não Autorizado').exists())
        self.assertContains(response, 'Permissão negada')


class CalculosModuloViewsTest(TestCase):
    def setUp(self):
        self.user = Usuario.objects.create_user(
            username='cozinheira_calc',
            password='senha_calc_123',
            nome_completo='Dona Geralda',
            perfil=PerfilUsuario.REFEITORIO
        )
        self.client.login(username='cozinheira_calc', password='senha_calc_123')
        self.cardapio = Cardapio.objects.create(nome='Cardápio Teste Almoço', refeicao=TipoRefeicao.ALMOCO)
        self.ing = Ingrediente.objects.create(nome='Macarrão Parafuso', unidade_padrao=UnidadeMedida.QUILOGRAMA)
        self.receita = ReceitaFichaTecnica.objects.create(cardapio=self.cardapio, nome='Massa com Molho')
        ItemReceita.objects.create(
            receita=self.receita,
            ingrediente=self.ing,
            quantidade_padrao=Decimal('0.0800'),
            unidade_medida=UnidadeMedida.QUILOGRAMA
        )
        self.freq = FrequenciaDiaria.objects.create(
            usuario_registro=self.user,
            data_refeicao=date.today(),
            refeicao_turno=TipoRefeicao.ALMOCO,
            total_estudantes_presentes=100
        )
        self.calculo = CalculoService.processar_calculo(
            cardapio=self.cardapio,
            frequencia=self.freq,
            usuario=self.user
        )

    def test_calculo_detalhe_view(self):
        response = self.client.get(f'/calculo/{self.calculo.id}/')
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'calculos/detalhe.html')
        self.assertContains(response, 'Macarrão Parafuso')
        # 100 alunos * 0.0800 = 8.0000 kg (formatado como 8,0000 em pt-br)
        self.assertContains(response, '8,0000')

    def test_calculo_proporcional_consolidacao_mesmo_ingrediente(self):
        # Adiciona uma segunda receita que usa o mesmo ingrediente Macarrão Parafuso
        receita_sopa = ReceitaFichaTecnica.objects.create(
            cardapio=self.cardapio,
            nome='Sopa de Legumes com Massa',
            fator_rendimento=Decimal('1.000')
        )
        ItemReceita.objects.create(
            receita=receita_sopa,
            ingrediente=self.ing,
            quantidade_padrao=Decimal('20.0000'),  # 20g por aluno
            unidade_medida=UnidadeMedida.GRAMA,    # Unidade em gramas
            base_calculo=BaseCalculo.POR_ALUNO
        )
        # Recalcula
        calculo_atualizado = CalculoService.processar_calculo(
            cardapio=self.cardapio,
            frequencia=self.freq,
            usuario=self.user,
            forcar_recalculo=True
        )
        # 100 alunos * 0.08kg = 8kg + 100 alunos * 20g (2kg) = 10kg
        item_calc = calculo_atualizado.itens.get(ingrediente=self.ing)
        self.assertEqual(item_calc.quantidade_calculada, Decimal('10.0000'))
        self.assertEqual(item_calc.unidade_medida, UnidadeMedida.QUILOGRAMA)

    def test_calculo_bloqueia_frequencia_invalida_ou_zerada(self):
        freq_zerada = FrequenciaDiaria.objects.create(
            usuario_registro=self.user,
            data_refeicao=date(2026, 12, 1),
            refeicao_turno=TipoRefeicao.ALMOCO,
            total_estudantes_presentes=0
        )
        with self.assertRaises(ValidationError):
            CalculoService.processar_calculo(
                cardapio=self.cardapio,
                frequencia=freq_zerada,
                usuario=self.user
            )

    def test_calculo_bloqueia_cardapio_sem_receitas(self):
        cardapio_vazio = Cardapio.objects.create(nome='Cardápio Vazio', refeicao=TipoRefeicao.ALMOCO)
        with self.assertRaises(ValidationError):
            CalculoService.processar_calculo(
                cardapio=cardapio_vazio,
                frequencia=self.freq,
                usuario=self.user
            )

    def test_conversao_automatica_grama_para_quilograma(self):
        # 1500g deve converter para 1.5kg
        qtd, un = CalculoService.converter_unidade_amigavel(Decimal('1500'), UnidadeMedida.GRAMA)
        self.assertEqual(qtd, Decimal('1.5000'))
        self.assertEqual(un, UnidadeMedida.QUILOGRAMA)

    def test_conversao_automatica_quilograma_fracionario_para_grama(self):
        # 0.450kg deve converter para 450g para facilitar pesagem no refeitório
        qtd, un = CalculoService.converter_unidade_amigavel(Decimal('0.4500'), UnidadeMedida.QUILOGRAMA)
        self.assertEqual(qtd, Decimal('450.0000'))
        self.assertEqual(un, UnidadeMedida.GRAMA)

    def test_conversao_automatica_mililitro_para_litro(self):
        # 2500ml deve converter para 2.5L
        qtd, un = CalculoService.converter_unidade_amigavel(Decimal('2500'), UnidadeMedida.MILILITRO)
        self.assertEqual(qtd, Decimal('2.5000'))
        self.assertEqual(un, UnidadeMedida.LITRO)

    def test_conversao_automatica_litro_fracionario_para_mililitro(self):
        # 0.750L deve converter para 750ml
        qtd, un = CalculoService.converter_unidade_amigavel(Decimal('0.7500'), UnidadeMedida.LITRO)
        self.assertEqual(qtd, Decimal('750.0000'))
        self.assertEqual(un, UnidadeMedida.MILILITRO)

    def test_unidade_contavel_permanece_inalterada(self):
        # 24 unidades devem permanecer 24 unidades
        qtd, un = CalculoService.converter_unidade_amigavel(Decimal('24.0000'), UnidadeMedida.UNIDADE)
        self.assertEqual(qtd, Decimal('24.0000'))
        self.assertEqual(un, UnidadeMedida.UNIDADE)

    def test_validacao_bloqueia_incompatibilidade_de_grandeza_fisica(self):
        # Ingrediente 'Macarrão Parafuso' é cadastrado como kg (massa)
        # Tentar cadastrar item de receita em litros (volume) deve gerar ValidationError
        item_invalido = ItemReceita(
            receita=self.receita,
            ingrediente=self.ing,
            quantidade_padrao=Decimal('1.0000'),
            unidade_medida=UnidadeMedida.LITRO,
            base_calculo=BaseCalculo.POR_ALUNO
        )
        with self.assertRaises(ValidationError) as ctx:
            item_invalido.full_clean()
        self.assertIn('Incompatibilidade de grandeza física', str(ctx.exception))

    def test_calculo_conferir_view(self):
        self.assertFalse(self.calculo.conferido)
        response = self.client.post(f'/calculo/{self.calculo.id}/conferir/', follow=True)
        self.assertEqual(response.status_code, 200)
        self.calculo.refresh_from_db()
        self.assertTrue(self.calculo.conferido)

    def test_calculo_ajustar_item_com_justificativa_rf09(self):
        item = self.calculo.itens.first()
        response = self.client.post(f'/calculo/itens/{item.id}/ajustar/', {
            'quantidade_ajustada': '9.500',
            'justificativa_ajuste': 'Acréscimo autorizado para repor turma extra.',
        }, follow=True)
        self.assertEqual(response.status_code, 200)
        item.refresh_from_db()
        self.assertEqual(item.quantidade_ajustada, Decimal('9.5000'))
        self.assertContains(response, 'Ajuste registrado')

    def test_calculo_imprimir_view(self):
        response = self.client.get(f'/calculo/{self.calculo.id}/imprimir/')
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'calculos/imprimir.html')
        self.assertContains(response, 'SPAE — Alimentação Escolar')
        self.assertContains(response, 'GUIA DE PRODUÇÃO E CONFERÊNCIA DIÁRIA DE INGREDIENTES')
        self.assertContains(response, 'Cardápio Teste Almoço')
        self.assertContains(response, 'Macarrão Parafuso')
        self.assertContains(response, '8,0000')
        self.assertContains(response, '100')
        self.assertContains(response, 'Responsável pelo Preparo (Merendeira)')
        self.assertContains(response, 'Nutricionista / Gestão Escolar')

    def test_calculo_imprimir_view_redireciona_anonimo(self):
        self.client.logout()
        response = self.client.get(f'/calculo/{self.calculo.id}/imprimir/')
        self.assertEqual(response.status_code, 302)
        self.assertIn('/login/', response.url)

    def test_calculo_exportar_csv_view(self):
        response = self.client.get(f'/calculo/{self.calculo.id}/exportar-csv/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'text/csv; charset=utf-8')
        self.assertIn('attachment; filename="SPAE_Resumo_Diario_', response['Content-Disposition'])

        conteudo_bytes = response.content
        # Verifica se o arquivo inicia com o BOM do UTF-8 (\xef\xbb\xbf)
        self.assertTrue(conteudo_bytes.startswith(b'\xef\xbb\xbf'))

        conteudo_texto = conteudo_bytes.decode('utf-8-sig')
        # Verifica o cabeçalho tabular com separador ponto-e-vírgula
        self.assertIn('Data da Refeição;Turno / Refeição;Cardápio;Estudantes Presentes;Ingrediente;Quantidade Calculada', conteudo_texto)
        # Verifica a linha de dados com valores formatados
        self.assertIn('Macarrão Parafuso', conteudo_texto)
        self.assertIn('8,0000', conteudo_texto)
        self.assertIn('100', conteudo_texto)
        self.assertIn('Cardápio Teste Almoço', conteudo_texto)

    def test_calculo_exportar_csv_com_ajuste_justificado(self):
        item = self.calculo.itens.first()
        item.quantidade_ajustada = Decimal('10.0000')
        item.justificativa_ajuste = 'Aumento de demanda confirmado.'
        item.save()

        response = self.client.get(f'/calculo/{self.calculo.id}/exportar-csv/')
        self.assertEqual(response.status_code, 200)

        conteudo_texto = response.content.decode('utf-8-sig')
        self.assertIn('10,0000', conteudo_texto)
        self.assertIn('Aumento de demanda confirmado.', conteudo_texto)


class AutenticacaoAutorizacaoModuloTest(TestCase):
    """Testes completos do Módulo de Autenticação e Autorização (RF01 - RBAC)."""

    def setUp(self):
        # Usuários com cada um dos 4 perfis do SPAE
        self.user_refeitorio = Usuario.objects.create_user(
            username='maria_merenda',
            password='senha_refeitorio_123',
            nome_completo='Maria das Graças',
            perfil=PerfilUsuario.REFEITORIO,
            ativo=True
        )
        self.user_frequencia = Usuario.objects.create_user(
            username='pedro_secretaria',
            password='senha_frequencia_123',
            nome_completo='Pedro Álvares',
            perfil=PerfilUsuario.FREQUENCIA,
            ativo=True
        )
        self.user_gestao = Usuario.objects.create_user(
            username='ana_nutri',
            password='senha_gestao_123',
            nome_completo='Ana Paula Nutricionista',
            perfil=PerfilUsuario.GESTAO,
            ativo=True
        )
        self.user_admin = Usuario.objects.create_user(
            username='carlos_admin',
            password='senha_admin_123',
            nome_completo='Carlos Administrador',
            perfil=PerfilUsuario.ADMIN,
            ativo=True
        )
        self.user_inativo = Usuario.objects.create_user(
            username='joao_inativo',
            password='senha_inativo_123',
            nome_completo='João Desativado',
            perfil=PerfilUsuario.REFEITORIO,
            ativo=False
        )

    def test_login_sucesso_com_credenciais_validas(self):
        response = self.client.post('/login/', {
            'username': 'maria_merenda',
            'password': 'senha_refeitorio_123',
        }, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context['user'].is_authenticated)
        self.assertEqual(response.context['user'].username, 'maria_merenda')
        self.assertContains(response, 'Bem-vindo(a), Maria das Graças!')

    def test_login_falha_com_senha_incorreta(self):
        response = self.client.post('/login/', {
            'username': 'maria_merenda',
            'password': 'senha_errada_xyz',
        })
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.context['user'].is_authenticated)
        self.assertContains(response, 'Usuário ou senha incorretos')

    def test_login_bloqueado_para_usuario_desativado(self):
        response = self.client.post('/login/', {
            'username': 'joao_inativo',
            'password': 'senha_inativo_123',
        })
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.context['user'].is_authenticated)
        self.assertContains(response, 'Esta conta de usuário está desativada')

    def test_logout_encerra_sessao(self):
        self.client.login(username='maria_merenda', password='senha_refeitorio_123')
        response = self.client.get('/logout/', follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.context['user'].is_authenticated)
        self.assertContains(response, 'Sessão encerrada com sucesso')

    def test_meu_perfil_atualizacao_nome(self):
        self.client.login(username='maria_merenda', password='senha_refeitorio_123')
        response = self.client.get('/meu-perfil/')
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'usuarios/meu_perfil.html')
        self.assertContains(response, 'Maria das Graças')

        # Atualiza o nome
        response_post = self.client.post('/meu-perfil/', {
            'nome_completo': 'Maria das Graças Silva',
        }, follow=True)
        self.assertEqual(response_post.status_code, 200)
        self.user_refeitorio.refresh_from_db()
        self.assertEqual(self.user_refeitorio.nome_completo, 'Maria das Graças Silva')
        self.assertContains(response_post, 'Seus dados de perfil foram atualizados com sucesso')

    def test_alterar_propria_senha(self):
        self.client.login(username='maria_merenda', password='senha_refeitorio_123')
        response = self.client.post('/alterar-senha/', {
            'old_password': 'senha_refeitorio_123',
            'new_password1': 'nova_senha_super_segura_456',
            'new_password2': 'nova_senha_super_segura_456',
        }, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Sua senha foi alterada com sucesso')

        # Confirma que a nova senha funciona
        self.client.logout()
        login_novo = self.client.login(username='maria_merenda', password='nova_senha_super_segura_456')
        self.assertTrue(login_novo)

    def test_rbac_admin_pode_gerenciar_usuarios(self):
        self.client.login(username='carlos_admin', password='senha_admin_123')

        # 1. Acessa lista
        response = self.client.get('/usuarios/')
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'usuarios/lista.html')
        self.assertContains(response, 'Gestão de Usuários e Permissões (RBAC)')

        # 2. Cria novo usuário
        response_create = self.client.post('/usuarios/novo/', {
            'username': 'novamerendeira',
            'nome_completo': 'Dona Florinda',
            'perfil': PerfilUsuario.REFEITORIO,
            'password': 'senha_inicial_123',
            'password_confirm': 'senha_inicial_123',
            'ativo': True,
        }, follow=True)
        self.assertEqual(response_create.status_code, 200)
        self.assertTrue(Usuario.objects.filter(username='novamerendeira').exists())
        novo_u = Usuario.objects.get(username='novamerendeira')
        self.assertEqual(novo_u.perfil, PerfilUsuario.REFEITORIO)
        self.assertTrue(novo_u.ativo)

        # 3. Edita usuário
        response_edit = self.client.post(f'/usuarios/{novo_u.id}/editar/', {
            'nome_completo': 'Dona Florinda Corrigida',
            'perfil': PerfilUsuario.GESTAO,
            'ativo': True,
        }, follow=True)
        self.assertEqual(response_edit.status_code, 200)
        novo_u.refresh_from_db()
        self.assertEqual(novo_u.nome_completo, 'Dona Florinda Corrigida')
        self.assertEqual(novo_u.perfil, PerfilUsuario.GESTAO)

        # 4. Redefine senha do usuário
        response_pwd = self.client.post(f'/usuarios/{novo_u.id}/redefinir-senha/', {
            'nova_senha': 'senha_redefinida_789',
            'confirmar_nova_senha': 'senha_redefinida_789',
        }, follow=True)
        self.assertEqual(response_pwd.status_code, 200)
        self.assertContains(response_pwd, 'redefinida com sucesso')

        # 5. Alterna status (desativa)
        response_toggle = self.client.post(f'/usuarios/{novo_u.id}/alternar-status/', follow=True)
        self.assertEqual(response_toggle.status_code, 200)
        novo_u.refresh_from_db()
        self.assertFalse(novo_u.ativo)

    def test_rbac_refeitorio_bloqueado_em_gestao_usuarios(self):
        # Usuário do refeitório NÃO pode acessar a área de administração de usuários
        self.client.login(username='maria_merenda', password='senha_refeitorio_123')
        response = self.client.get('/usuarios/', follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Acesso não autorizado')
        self.assertNotEqual(response.resolver_match.url_name, 'usuario_lista')

    def test_rbac_frequencia_bloqueada_em_cadastros_administrativos(self):
        # Secretaria/Frequência NÃO pode cadastrar ingredientes
        self.client.login(username='pedro_secretaria', password='senha_frequencia_123')
        response = self.client.get('/cadastros/ingredientes/novo/', follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Permissão negada')

    def test_rbac_refeitorio_bloqueado_em_lancar_frequencia(self):
        # Refeitório NÃO pode lançar frequência
        self.client.login(username='maria_merenda', password='senha_refeitorio_123')
        response = self.client.get('/frequencia/registrar/', follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Acesso não autorizado')

    def test_admin_bloqueado_de_desativar_a_si_proprio(self):
        self.client.login(username='carlos_admin', password='senha_admin_123')
        response = self.client.post(f'/usuarios/{self.user_admin.id}/alternar-status/', follow=True)
        self.assertEqual(response.status_code, 200)
        self.user_admin.refresh_from_db()
        self.assertTrue(self.user_admin.ativo)
        self.assertContains(response, 'você não pode desativar sua própria conta')





