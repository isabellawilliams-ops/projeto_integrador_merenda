# Manual do Usuário — SPAE (Sistema de Planejamento da Alimentação Escolar)

> **Documento Oficial de Instrução e Boas Práticas**  
> Versão: 1.0 (2026)  
> Público-Alvo: Merendeiras, Equipe da Portaria/Secretaria, Nutricionistas, Gestores Escolares e Equipe de TI.

---

## Sumário

1. [Visão Geral do Sistema](#1-visão-geral-do-sistema)
2. [Perfis de Acesso e Credenciais de Demonstração](#2-perfis-de-acesso-e-credenciais-de-demonstração)
3. [Primeiros Passos: Acesso e Login](#3-primeiros-passos-acesso-e-login)
4. [Guia por Perfil de Usuário](#4-guia-por-perfil-de-usuário)
   - [4.1 Perfil Frequência (Secretaria e Portaria)](#41-perfil-frequência-secretaria-e-portaria)
   - [4.2 Perfil Gestão (Nutricionista e Direção)](#42-perfil-gestão-nutricionista-e-direção)
   - [4.3 Perfil Refeitório (Merendeiras e Cozinha)](#43-perfil-refeitório-merendeiras-e-cozinha)
   - [4.4 Perfil Administrador (TI e Coordenação)](#44-perfil-administrador-ti-e-coordenação)
5. [Motor de Cálculo e Regras de Conversão](#5-motor-de-cálculo-e-regras-de-conversão)
6. [Impressão e Exportação de Fichas](#6-impressão-e-exportação-de-fichas)
7. [Dúvidas Frequentes e Resolução de Problemas](#7-dúvidas-frequentes-e-resolução-de-problemas)

---

## 1. Visão Geral do Sistema

O **SPAE (Sistema de Planejamento da Alimentação Escolar)** foi projetado para eliminar cálculos manuais demorados e sujeitos a erros na preparação das refeições de escolas públicas de tempo integral.

O sistema cruza automaticamente:
- A **Frequência Diária Real** de alunos presentes (informada pela secretaria ou portaria no início do turno).
- Os **Cardápios e Fichas Técnicas** homologados pela equipe de nutrição.

O resultado é a indicação precisa das quantidades de cada insumo em unidades adequadas para a cozinha (quilogramas, gramas, litros, mililitros ou unidades inteiras), prevenindo tanto a falta de alimento quanto o desperdício de comida pública.

---

## 2. Perfis de Acesso e Credenciais de Demonstração

O SPAE utiliza Controle de Acesso Baseado em Papéis (**RBAC**). Cada usuário possui telas e permissões adaptadas ao seu trabalho diário:

| Perfil | Identificador | Função Principal |
|---|---|---|
| **Refeitório** | `refeitorio` | Visualizar lista de insumos com fontes grandes no celular, conferir itens (`conferido=True`) e justificar eventuais ajustes manuais (RF09). |
| **Frequência** | `frequencia` | Registrar e atualizar a contagem de estudantes presentes por turno e data. |
| **Gestão** | `gestao` | Cadastrar e parametrizar cardápios, fichas técnicas de receitas, insumos e fatores de rendimento/perda. |
| **Administrador** | `admin` | Gerenciar contas de usuários, alterar papéis, redefinir senhas e auditar registros. |

### Contas de Demonstração Rápidas

Na tela de login, há botões de preenchimento rápido com as seguintes credenciais padrão:

- **Merendeira (Refeitório):** Usuário: `merendeira` | Senha: `merenda123`
- **Secretaria (Frequência):** Usuário: `secretaria` | Senha: `portaria123`
- **Nutricionista (Gestão):** Usuário: `nutricionista` | Senha: `nutri123`
- **Administrador (TI):** Usuário: `admin` | Senha: `admin123`

---

## 3. Primeiros Passos: Acesso e Login

1. Abra o navegador no computador ou no celular e acesse o endereço do sistema (ex: `http://localhost:8000` ou endereço da rede escolar).
2. Na tela de autenticação:
   - Digite seu **Usuário** e sua **Senha**.
   - Você pode clicar no ícone de olho para conferir os caracteres digitados.
3. Clique em **Entrar no Sistema**.
4. Você será direcionado para a **Home / Painel Principal**, onde verá:
   - Resumo do dia (refeição planejada e contagem de estudantes).
   - Situação da conferência da merenda.
   - Acesso rápido adaptado ao seu perfil.

> [!NOTE]
> Se esquecer a senha ou tiver sua conta bloqueada, solicite a redefinição diretamente ao Administrador da escola.

---

## 4. Guia por Perfil de Usuário

### 4.1 Perfil Frequência (Secretaria e Portaria)

A contagem rápida da presença é o gatilho inicial para o cálculo da merenda do dia.

#### Como Lançar a Presença Diária:
1. No menu superior ou na Home, clique em **Frequência** ou no botão **Lançar Presença de Estudantes**.
2. No formulário:
   - **Data da Refeição:** Por padrão vem a data de hoje (ajuste caso esteja adiantando o lançamento).
   - **Turno / Refeição:** Selecione entre `Lanche da Manhã`, `Almoço` ou `Lanche da Tarde`.
   - **Total de Estudantes Presentes:** Digite o número inteiro positivo de alunos (ex: `120`). Valores nulos ou menores que zero são bloqueados.
3. Clique em **Salvar Presença**.
4. **Atualização Automática:** Se você lançar novamente a presença para a mesma data e mesmo turno, o sistema atualiza o número existente de forma transparente, evitando duplicidades.

---

### 4.2 Perfil Gestão (Nutricionista e Direção)

Responsável pela definição das preparações, proporções e insumos.

#### Acesso ao Módulo de Cadastros:
- No menu superior, clique em **Cadastros** para acessar a central administrativa.

#### 1. Cadastrar Ingredientes:
1. Acesse **Cadastros > Catálogo de Ingredientes > Novo Ingrediente**.
2. Preencha:
   - **Nome:** Ex: *Feijão Carioca tipo 1*.
   - **Unidade Padrão:** `kg`, `g`, `L`, `ml` ou `un`.
   - **Observações de Armazenamento:** Ex: *Armazenar em local seco e arejado, longe do piso*.
3. Clique em **Salvar Ingrediente**.

#### 2. Cadastrar Cardápios e Fichas Técnicas:
1. Acesse **Cadastros > Cardápios Escolares > Novo Cardápio**.
2. Informe o **Nome** (ex: *Almoço de Terça-feira*), o **Tipo de Refeição** (`Almoço`) e a descrição nutricional.
3. Abra o cardápio criado e clique em **Nova Preparação (Receita)**:
   - Nome: Ex: *Arroz Branco com Cenoura*.
   - Fator de Rendimento: Padrão `1.000` (ajuste se houver perda ou contração na cocção).
   - Modo de Preparo: Instruções passo a passo para a cozinha.
4. Adicione os insumos da receita:
   - Selecione o ingrediente.
   - Informe a quantidade padrão (ex: `0.0800`).
   - Selecione a unidade (`kg` ou `g`).
   - Base de cálculo: `Por Aluno`, `Por Porção` ou `Por Lote`.

> [!WARNING]
> O sistema bloqueia a associação de grandezas incompatíveis. Por exemplo: não é permitido cadastrar litros para um insumo cuja unidade padrão seja quilograma.

---

### 4.3 Perfil Refeitório (Merendeiras e Cozinha)

A interface do refeitório foi projetada com **design Mobile-First**, botões confortáveis e fontes de alta visibilidade, legíveis à distância de um braço.

#### Como Utilizar na Rotina Diária:
1. Ao chegar no refeitório, abra o sistema no celular ou no tablet da cozinha.
2. Na Home ou no menu **Cálculo**, acesse a tela do **Cálculo Proporcional da Merenda**.
3. O sistema já exibe a lista completa de insumos calculados exatamente para a quantidade de estudantes presentes no dia.
4. Conforme separa os ingredientes no estoque, verifique a unidade indicada (ex: `8,0000 kg`, `450,0000 g`, `2,5000 L`).
5. **Ajuste Manual com Justificativa (RF09):**
   - Caso precise alterar a quantidade sugerida (ex: sobra do dia anterior ou reposição emergencial), clique em **Ajustar Quantidade** no cartão do insumo.
   - Digite o novo valor e preencha a **Justificativa Obrigatória**.
   - Clique em **Salvar Ajuste**. O cartão exibirá o valor original riscado e o novo valor em destaque.
6. **Conferência Final:**
   - Com todos os insumos conferidos, clique no botão superior **Marcar como Conferido**. O status mudará para verde, indicando que a merenda está homologada para preparo.

---

### 4.4 Perfil Administrador (TI e Coordenação)

O Administrador é responsável pela segurança, gestão de acessos e parametrizações técnicas.

#### Funcionalidades Administrativas:
- **Gestão de Usuários:** Acesse pelo menu **Usuários** ou pelo Hub de Cadastros.
- **Cadastrar Novo Usuário:** Defina o login (`username`), nome completo, papel de atuação (`refeitorio`, `frequencia`, `gestao` ou `admin`) e senha inicial.
- **Editar e Alternar Status:** Ative ou desative acessos de funcionários com um clique. Administradores são protegidos contra auto-desativação acidental.
- **Redefinição de Senha:** Troque com segurança a senha de qualquer colaborador sem precisar conhecer a senha anterior.

---

## 5. Motor de Cálculo e Regras de Conversão

A fórmula fundamental aplicada pelo SPAE para cada item do cardápio é:

$$\text{Quantidade Calculada} = \text{Total de Estudantes} \times \text{Quantidade Padrão por Aluno} \times \text{Fator de Rendimento}$$

### Regras de Conversão Automática de Unidades

O sistema converte automaticamente unidades dentro da mesma grandeza para facilitar a leitura na cozinha:

| Grandeza | Quantidade Calculada | Unidade de Exibição | Exemplo Prático |
|---|---|---|---|
| **Massa** | $\ge 1.000\text{ g}$ | **kg** (Quilogramas) | $1.600\text{ g} \rightarrow 1{,}6000\text{ kg}$ |
| **Massa** | $< 1\text{ kg}$ e $> 0\text{ kg}$ | **g** (Gramas) | $0{,}3500\text{ kg} \rightarrow 350{,}0000\text{ g}$ |
| **Volume** | $\ge 1.000\text{ ml}$ | **L** (Litros) | $2.000\text{ ml} \rightarrow 2{,}0000\text{ L}$ |
| **Volume** | $< 1\text{ L}$ e $> 0\text{ L}$ | **ml** (Mililitros) | $0{,}4000\text{ L} \rightarrow 400{,}0000\text{ ml}$ |
| **Contável** | Qualquer valor | **un** (Unidades) | $30\text{ un}$ permanece $30\text{ un}$ |

> [!IMPORTANT]
> O SPAE **nunca** converte massa para volume (ex: kg para litros) sem fator de densidade explícito, garantindo rigor físico e nutricional.

---

## 6. Impressão e Exportação de Fichas

Para atender auditorias do PNAE e rotinas operacionais com prancheta física na cozinha, o sistema possui ferramentas dedicadas de impressão e exportação (RF11):

1. **Ficha de Prancheta A4 (Impressão):**
   - Na tela do cálculo diário, clique em **Imprimir Ficha (A4)**.
   - A página formata automaticamente o documento ocultando menus da web, incluindo checklist com caixas `[ ]` para ticar com caneta, modo de preparo e termos de assinatura para a merendeira e nutricionista.
   - Clique em **Imprimir Ficha Agora** ou use o atalho `Ctrl + P`.
2. **Exportar Planilha (CSV / Excel):**
   - Clique em **Exportar CSV**.
   - O arquivo é gerado com codificação `UTF-8 com BOM` e delimitador `;`, abrindo perfeitamente no Microsoft Excel e LibreOffice Calc sem caracteres corrompidos e com números decimais no padrão brasileiro.

---

## 7. Dúvidas Frequentes e Resolução de Problemas

**1. O cálculo de hoje não está aparecendo na tela do refeitório. O que fazer?**  
*Resposta:* Verifique se a equipe da portaria/secretaria já lançou a contagem de estudantes presentes para a data de hoje. Sem a presença informada, o cálculo não pode ser gerado.

**2. O que fazer quando um ingrediente estiver em falta e precisarmos usar outro?**  
*Resposta:* A merendeira pode ajustar a quantidade do item faltante para zero, registrando na justificativa a substituição realizada, e registrar o item substituto conforme instrução da gestão.

**3. Como alterar a minha própria senha?**  
*Resposta:* Clique no seu nome no canto superior direito da tela, selecione **Meu Perfil** e depois clique em **Alterar Senha**.

**4. Posso usar o sistema sem internet no refeitório?**  
*Resposta:* O sistema opera perfeitamente na rede local (Wi-Fi interno da escola) ou conectado ao servidor central da unidade de ensino.
