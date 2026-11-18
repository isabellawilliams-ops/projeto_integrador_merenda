from datetime import date
from decimal import Decimal
from django.core.management.base import BaseCommand
from django.db import transaction

from merenda.models import (
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


class Command(BaseCommand):
    help = "Carga inicial de dados (seeds) para o SPAE: usuários, ingredientes, cardápios e fichas técnicas."

    def add_arguments(self, parser):
        parser.add_argument(
            '--limpar',
            action='store_true',
            help='Limpa os dados cadastrados antes de popular (atenção: apaga dados existentes).',
        )

    @transaction.atomic
    def handle(self, *args, **options):
        if options['limpar']:
            self.stdout.write(self.style.WARNING("Limpando dados anteriores..."))
            ItemCalculo.objects.all().delete()
            CalculoDiario.objects.all().delete()
            FrequenciaDiaria.objects.all().delete()
            ItemReceita.objects.all().delete()
            ReceitaFichaTecnica.objects.all().delete()
            Cardapio.objects.all().delete()
            Ingrediente.objects.all().delete()
            Usuario.objects.exclude(is_superuser=True).delete()

        self.stdout.write(self.style.HTTP_INFO("Iniciando carga de dados do SPAE..."))

        # 1. Usuários por Perfil
        usuarios_dados = [
            {
                'username': 'admin',
                'nome': 'Administrador do Sistema',
                'perfil': PerfilUsuario.ADMIN,
                'email': 'admin@escola.gov.br',
                'is_staff': True,
                'is_superuser': True,
                'senha': 'admin123',
            },
            {
                'username': 'nutricionista',
                'nome': 'Dra. Ana Beatriz Silva',
                'perfil': PerfilUsuario.GESTAO,
                'email': 'nutricao@escola.gov.br',
                'is_staff': True,
                'is_superuser': False,
                'senha': 'nutri123',
            },
            {
                'username': 'merendeira',
                'nome': 'Dona Maria de Fátima',
                'perfil': PerfilUsuario.REFEITORIO,
                'email': 'refeitorio@escola.gov.br',
                'is_staff': False,
                'is_superuser': False,
                'senha': 'merenda123',
            },
            {
                'username': 'secretaria',
                'nome': 'Carlos Eduardo Santos',
                'perfil': PerfilUsuario.FREQUENCIA,
                'email': 'secretaria@escola.gov.br',
                'is_staff': False,
                'is_superuser': False,
                'senha': 'portaria123',
            },
        ]

        usuarios = {}
        for u in usuarios_dados:
            user, created = Usuario.objects.get_or_create(
                username=u['username'],
                defaults={
                    'nome_completo': u['nome'],
                    'perfil': u['perfil'],
                    'email': u['email'],
                    'is_staff': u['is_staff'],
                    'is_superuser': u['is_superuser'],
                    'ativo': True,
                }
            )
            if created or not user.has_usable_password():
                user.set_password(u['senha'])
                user.save()
            usuarios[u['username']] = user
            self.stdout.write(f"  [Usuário] {user.username} ({user.get_perfil_display()}) pronto.")

        # 2. Catálogo de Ingredientes
        ingredientes_dados = [
            ("Arroz Branco Tipo 1", UnidadeMedida.QUILOGRAMA, "Armazenar em local seco, ventilado e sobre estrados."),
            ("Feijão Carioca", UnidadeMedida.QUILOGRAMA, "Grãos selecionados tipo 1. Guardar em despensa seca."),
            ("Feijão Preto", UnidadeMedida.QUILOGRAMA, "Grãos selecionados tipo 1."),
            ("Peito de Frango em Cubos", UnidadeMedida.QUILOGRAMA, "Manter congelado a -18°C até o dia do descongelamento."),
            ("Carne Bovina Moída (Patinho/Acém)", UnidadeMedida.QUILOGRAMA, "Manter refrigerada ou congelada."),
            ("Óleo de Soja Refinado", UnidadeMedida.LITRO, "Garrafas de 900ml ou galão 5L. Local protegido de luz."),
            ("Sal Refinado Iodado", UnidadeMedida.QUILOGRAMA, "Conservar em recipiente fechado e seco."),
            ("Alho Triturado", UnidadeMedida.QUILOGRAMA, "Uso para tempero diário das preparações."),
            ("Cebola Branca", UnidadeMedida.QUILOGRAMA, "Hortifrúti fresco. Higienizar e picar no dia."),
            ("Tomate Salada Fresco", UnidadeMedida.QUILOGRAMA, "Frutos maduros e higienizados."),
            ("Cenoura Fresca", UnidadeMedida.QUILOGRAMA, "Lavar, descascar e cortar em cubos ou rodelas."),
            ("Batata Inglesa", UnidadeMedida.QUILOGRAMA, "Armazenar em local arejado, escuro e seco."),
            ("Macarrão Espaguete com Ovos", UnidadeMedida.QUILOGRAMA, "Massa seca de sêmola."),
            ("Molho de Tomate Tradicional", UnidadeMedida.QUILOGRAMA, "Embalagem sachê/tetra pak."),
            ("Banana Prata", UnidadeMedida.UNIDADE, "Fruta fresca para sobremesa ou lanches."),
            ("Maçã Nacional Fuji", UnidadeMedida.UNIDADE, "Fruta fresca, consumo in natura."),
            ("Leite Integral Pasteurizado", UnidadeMedida.LITRO, "Bebida láctea/leite para lanches matutinos."),
            ("Pão Francês Fresco", UnidadeMedida.UNIDADE, "Entregue diariamente pela padaria parceira."),
            ("Margarina Vegetal com Sal", UnidadeMedida.QUILOGRAMA, "Armazenar sob refrigeração de 2°C a 8°C."),
            ("Aveia em Flocos Finos", UnidadeMedida.QUILOGRAMA, "Cereal matinal para preparo de vitaminas."),
            ("Ovos de Galinha Vermelhos", UnidadeMedida.UNIDADE, "Ovos frescos inspecionados."),
        ]

        ingredientes = {}
        for nome, un, obs in ingredientes_dados:
            ing, _ = Ingrediente.objects.get_or_create(
                nome=nome,
                defaults={'unidade_padrao': un, 'observacoes': obs}
            )
            ingredientes[nome] = ing
        self.stdout.write(self.style.SUCCESS(f"  [Ingredientes] {len(ingredientes)} insumos catalogados."))

        # 3. Cardápios e Fichas Técnicas
        hoje = date.today()

        # Cardápio 1: Almoço Tradicional
        c1, _ = Cardapio.objects.get_or_create(
            nome="Almoço Tradicional (Arroz, Feijão e Frango com Legumes)",
            refeicao=TipoRefeicao.ALMOCO,
            defaults={
                'descricao': 'Almoço nutritivo e balanceado com carboidratos, proteínas e salada/legumes.',
                'data_referencia': hoje,
                'ativo': True,
            }
        )

        r1, _ = ReceitaFichaTecnica.objects.get_or_create(
            cardapio=c1,
            nome="Arroz Branco Soltinho",
            defaults={
                'modo_preparo': 'Refogar o alho no óleo, acrescentar o arroz cru e a água fervente. Cozinhar até secar.',
                'fator_rendimento': Decimal('1.000'),
            }
        )
        ItemReceita.objects.get_or_create(receita=r1, ingrediente=ingredientes["Arroz Branco Tipo 1"], defaults={'quantidade_padrao': Decimal('0.0800'), 'unidade_medida': UnidadeMedida.QUILOGRAMA, 'base_calculo': BaseCalculo.POR_ALUNO})
        ItemReceita.objects.get_or_create(receita=r1, ingrediente=ingredientes["Óleo de Soja Refinado"], defaults={'quantidade_padrao': Decimal('0.0050'), 'unidade_medida': UnidadeMedida.LITRO, 'base_calculo': BaseCalculo.POR_ALUNO})
        ItemReceita.objects.get_or_create(receita=r1, ingrediente=ingredientes["Alho Triturado"], defaults={'quantidade_padrao': Decimal('0.0020'), 'unidade_medida': UnidadeMedida.QUILOGRAMA, 'base_calculo': BaseCalculo.POR_ALUNO})
        ItemReceita.objects.get_or_create(receita=r1, ingrediente=ingredientes["Sal Refinado Iodado"], defaults={'quantidade_padrao': Decimal('0.0020'), 'unidade_medida': UnidadeMedida.QUILOGRAMA, 'base_calculo': BaseCalculo.POR_ALUNO})

        r2, _ = ReceitaFichaTecnica.objects.get_or_create(
            cardapio=c1,
            nome="Feijão Carioca da Casa",
            defaults={
                'modo_preparo': 'Deixar de molho por 12h. Cozinhar na pressão e temperar com alho, cebola e sal.',
                'fator_rendimento': Decimal('1.000'),
            }
        )
        ItemReceita.objects.get_or_create(receita=r2, ingrediente=ingredientes["Feijão Carioca"], defaults={'quantidade_padrao': Decimal('0.0600'), 'unidade_medida': UnidadeMedida.QUILOGRAMA, 'base_calculo': BaseCalculo.POR_ALUNO})
        ItemReceita.objects.get_or_create(receita=r2, ingrediente=ingredientes["Óleo de Soja Refinado"], defaults={'quantidade_padrao': Decimal('0.0030'), 'unidade_medida': UnidadeMedida.LITRO, 'base_calculo': BaseCalculo.POR_ALUNO})
        ItemReceita.objects.get_or_create(receita=r2, ingrediente=ingredientes["Cebola Branca"], defaults={'quantidade_padrao': Decimal('0.0050'), 'unidade_medida': UnidadeMedida.QUILOGRAMA, 'base_calculo': BaseCalculo.POR_ALUNO})
        ItemReceita.objects.get_or_create(receita=r2, ingrediente=ingredientes["Alho Triturado"], defaults={'quantidade_padrao': Decimal('0.0020'), 'unidade_medida': UnidadeMedida.QUILOGRAMA, 'base_calculo': BaseCalculo.POR_ALUNO})
        ItemReceita.objects.get_or_create(receita=r2, ingrediente=ingredientes["Sal Refinado Iodado"], defaults={'quantidade_padrao': Decimal('0.0020'), 'unidade_medida': UnidadeMedida.QUILOGRAMA, 'base_calculo': BaseCalculo.POR_ALUNO})

        r3, _ = ReceitaFichaTecnica.objects.get_or_create(
            cardapio=c1,
            nome="Frango com Cenoura e Batata",
            defaults={
                'modo_preparo': 'Dourar a carne temperada, acrescentar os legumes picados e água até amaciar.',
                'fator_rendimento': Decimal('1.000'),
            }
        )
        ItemReceita.objects.get_or_create(receita=r3, ingrediente=ingredientes["Peito de Frango em Cubos"], defaults={'quantidade_padrao': Decimal('0.1000'), 'unidade_medida': UnidadeMedida.QUILOGRAMA, 'base_calculo': BaseCalculo.POR_ALUNO})
        ItemReceita.objects.get_or_create(receita=r3, ingrediente=ingredientes["Cenoura Fresca"], defaults={'quantidade_padrao': Decimal('0.0300'), 'unidade_medida': UnidadeMedida.QUILOGRAMA, 'base_calculo': BaseCalculo.POR_ALUNO})
        ItemReceita.objects.get_or_create(receita=r3, ingrediente=ingredientes["Batata Inglesa"], defaults={'quantidade_padrao': Decimal('0.0400'), 'unidade_medida': UnidadeMedida.QUILOGRAMA, 'base_calculo': BaseCalculo.POR_ALUNO})
        ItemReceita.objects.get_or_create(receita=r3, ingrediente=ingredientes["Óleo de Soja Refinado"], defaults={'quantidade_padrao': Decimal('0.0040'), 'unidade_medida': UnidadeMedida.LITRO, 'base_calculo': BaseCalculo.POR_ALUNO})
        ItemReceita.objects.get_or_create(receita=r3, ingrediente=ingredientes["Sal Refinado Iodado"], defaults={'quantidade_padrao': Decimal('0.0025'), 'unidade_medida': UnidadeMedida.QUILOGRAMA, 'base_calculo': BaseCalculo.POR_ALUNO})

        r4, _ = ReceitaFichaTecnica.objects.get_or_create(
            cardapio=c1,
            nome="Sobremesa: Banana Prata",
            defaults={
                'modo_preparo': 'Higienizar as cascas com solução clorada e distribuir aos alunos.',
                'fator_rendimento': Decimal('1.000'),
            }
        )
        ItemReceita.objects.get_or_create(receita=r4, ingrediente=ingredientes["Banana Prata"], defaults={'quantidade_padrao': Decimal('1.0000'), 'unidade_medida': UnidadeMedida.UNIDADE, 'base_calculo': BaseCalculo.POR_ALUNO})

        # Cardápio 2: Lanche da Manhã
        c2, _ = Cardapio.objects.get_or_create(
            nome="Lanche da Manhã (Vitamina de Banana e Pão com Margarina)",
            refeicao=TipoRefeicao.LANCHE_MANHA,
            defaults={
                'descricao': 'Lanche matinal para início da jornada de tempo integral.',
                'data_referencia': hoje,
                'ativo': True,
            }
        )
        r5, _ = ReceitaFichaTecnica.objects.get_or_create(
            cardapio=c2,
            nome="Vitamina de Banana com Aveia",
            defaults={'modo_preparo': 'Bater leite, banana e aveia em liquidificador industrial.', 'fator_rendimento': Decimal('1.000')}
        )
        ItemReceita.objects.get_or_create(receita=r5, ingrediente=ingredientes["Leite Integral Pasteurizado"], defaults={'quantidade_padrao': Decimal('0.2000'), 'unidade_medida': UnidadeMedida.LITRO, 'base_calculo': BaseCalculo.POR_ALUNO})
        ItemReceita.objects.get_or_create(receita=r5, ingrediente=ingredientes["Banana Prata"], defaults={'quantidade_padrao': Decimal('0.5000'), 'unidade_medida': UnidadeMedida.UNIDADE, 'base_calculo': BaseCalculo.POR_ALUNO})
        ItemReceita.objects.get_or_create(receita=r5, ingrediente=ingredientes["Aveia em Flocos Finos"], defaults={'quantidade_padrao': Decimal('0.0200'), 'unidade_medida': UnidadeMedida.QUILOGRAMA, 'base_calculo': BaseCalculo.POR_ALUNO})

        r6, _ = ReceitaFichaTecnica.objects.get_or_create(
            cardapio=c2,
            nome="Pão Francês com Margarina",
            defaults={'modo_preparo': 'Cortar o pão ao meio e passar margarina.', 'fator_rendimento': Decimal('1.000')}
        )
        ItemReceita.objects.get_or_create(receita=r6, ingrediente=ingredientes["Pão Francês Fresco"], defaults={'quantidade_padrao': Decimal('1.0000'), 'unidade_medida': UnidadeMedida.UNIDADE, 'base_calculo': BaseCalculo.POR_ALUNO})
        ItemReceita.objects.get_or_create(receita=r6, ingrediente=ingredientes["Margarina Vegetal com Sal"], defaults={'quantidade_padrao': Decimal('0.0100'), 'unidade_medida': UnidadeMedida.QUILOGRAMA, 'base_calculo': BaseCalculo.POR_ALUNO})

        self.stdout.write(self.style.SUCCESS("  [Cardápios e Fichas] Cardápios e receitas cadastrados com sucesso."))

        # 4. Frequência Diária de Exemplo (120 alunos conforme Seção 8 do Documento Norteador)
        freq, _ = FrequenciaDiaria.objects.get_or_create(
            data_refeicao=hoje,
            refeicao_turno=TipoRefeicao.ALMOCO,
            defaults={
                'usuario_registro': usuarios['secretaria'],
                'total_estudantes_presentes': 120,
            }
        )
        self.stdout.write(f"  [Frequência Diária] {freq}")

        # 5. Cálculo Diário de Exemplo
        calc, _ = CalculoDiario.objects.get_or_create(
            cardapio=c1,
            frequencia=freq,
            data_calculo=hoje,
            defaults={
                'usuario_responsavel': usuarios['merendeira'],
                'conferido': True,
            }
        )

        # Gerar os itens do cálculo para os 120 alunos
        # Agrupa quantidades por ingrediente somando se aparecer em mais de uma preparação
        totais = {}
        for receita in c1.receitas.all():
            for item in receita.itens.all():
                qtd = Decimal(freq.total_estudantes_presentes) * item.quantidade_padrao * receita.fator_rendimento
                ing_id = item.ingrediente_id
                if ing_id not in totais:
                    totais[ing_id] = {
                        'ingrediente': item.ingrediente,
                        'quantidade': Decimal('0'),
                        'unidade': item.unidade_medida
                    }
                totais[ing_id]['quantidade'] += qtd

        for ing_id, info in totais.items():
            ItemCalculo.objects.get_or_create(
                calculo=calc,
                ingrediente=info['ingrediente'],
                defaults={
                    'quantidade_calculada': info['quantidade'],
                    'unidade_medida': info['unidade'],
                }
            )

        self.stdout.write(self.style.SUCCESS(f"  [Cálculo Diário] Cálculo executado com {calc.itens.count()} ingredientes calculados."))
        self.stdout.write(self.style.SUCCESS("✓ Carga inicial de dados (seeds) concluída com sucesso!"))
