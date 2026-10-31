# Critérios de Qualidade — RemindMe

Issue #60. Seleciona as características de qualidade do produto relevantes para o RemindMe, explica por que cada uma importa e diz como cada uma é verificada. As avaliações desta pasta usam estes critérios.

- **Data:** 2026-10-16.
- **Referência:** características de qualidade do produto da ISO/IEC 25010, as mesmas do [relatório de qualidade](relatorio-de-qualidade.md). A seção 4 traz a correspondência com a ISO/IEC 9126, que a disciplina também usa.
- **Fontes dos critérios:** [visão](../visao.md) (problema e critérios de sucesso), [personas](../personas.md), [requisitos](../requisitos.md) (RNF e RB) e [drivers arquiteturais](../arquitetura.md#2-drivers-arquiteturais).
- **Regra seguida:** toda meta numérica vem da baseline. Onde a baseline não define meta, o critério diz isso e não inventa um valor (regra 2 do [`CLAUDE.md`](../../CLAUDE.md)).

## 1. Seleção e prioridade

O valor do RemindMe está nas regras: o título tem o estado certo, o saldo bate ao centavo e cada operação fica registrada (visão, seção 3). Por isso as características que protegem regra, dinheiro e rastro têm prioridade alta. Interface e integração ainda não existem, ou são pequenas no MVP, e ficam abaixo.

| Característica | Prioridade | Por que importa no RemindMe | Quem sente a falha |
|---|---|---|---|
| Adequação funcional | Alta | O sistema existe para aplicar regras de estado, saldo e alçada (DA-01). Um saldo errado ou uma baixa indevida fazem cobrar quem já pagou ou deixar de cobrar quem deve | Diego (registra pagamentos), Sérgio (é cobrado) |
| Confiabilidade | Alta | São operações financeiras. Um pagamento gravado pela metade ou duplicado quebra o saldo e a confiança no sistema (DA-03) | Carla, Diego |
| Segurança | Alta | O sistema guarda dados financeiros de clientes. O cliente não acessa o sistema (OPEN-57). O critério de sucesso "operação rastreável" depende de auditoria imutável (DA-02, DA-04) | Carla (responde pela empresa), Sérgio (dados próprios) |
| Manutenibilidade | Alta | O sistema é entregue em 16 specs, por três pessoas e com agentes de codificação. A regra precisa ficar em um único ponto e ser testável sem banco e sem interface (DA-09, ADR-001) | A equipe |
| Usabilidade | Média | Os usuários não são especialistas em finanças nem em sistemas. A recusa precisa explicar o motivo. Pesa mais quando houver interface (OPEN-01) | Diego, Carla, Sérgio |
| Eficiência de desempenho | Média | O volume de uma pequena empresa é baixo, mas a régua e os alertas rodam em lote e não podem travar o uso (DA-05) | Diego |
| Compatibilidade | Baixa | No MVP, a troca de dados com outros sistemas se limita ao CSV (RB-19). Canal e IA ficam atrás de interfaces | Helena (exporta para o sistema contábil) |
| Portabilidade | Baixa | Há uma única instalação, e a hospedagem está em aberto (OPEN-12). Importa a substituição de componentes (canal, IA, banco), coberta também por manutenibilidade | A equipe |

## 2. Critérios por característica

Para cada característica: as subcaracterísticas que mais pesam, os requisitos de origem, o critério verificável e onde ele é avaliado.

### 2.1 Adequação funcional — prioridade alta

| Subcaracterística | Critério | Origem | Como verificar |
|---|---|---|---|
| Completude funcional | Todo RF com SHALL das specs aprovadas está implementado | `requisitos.md`, convenções | Matriz requisito → teste ([rastreabilidade](../rastreabilidade.md)) |
| Correção funcional | Todos os critérios de aceite das specs aprovadas passam. O saldo é exato ao centavo, sem `float` | Specs; RB-22, RB-23; `testes.md`, princípio 5 | Suíte de aceite; cenários de cálculo ([funcionalidade](funcionalidade.md)) |
| Correção funcional | Transição fora da tabela de estados é recusada | RB-21; `estados.md` | Teste estado × operação |
| Pertinência funcional | Nenhum comportamento além da spec | `testes.md`, definição de pronto, item 1 | Revisão de código ([revisão](revisao-de-codigo.md)) |

**Meta:** 100% dos critérios de aceite das specs aprovadas passando. A falha de uma cláusula SHALL reprova o aceite (`requisitos.md`, convenções).

### 2.2 Confiabilidade — prioridade alta

| Subcaracterística | Critério | Origem | Como verificar |
|---|---|---|---|
| Tolerância a falhas | Falha no meio de uma operação financeira não deixa alteração parcial | RNF-09 (SHALL) | Teste com falha injetada ([confiabilidade](confiabilidade.md)) |
| Tolerância a falhas | Falha ou demora do serviço de IA não impede a operação de terminar | RNF-24; DA-06 | Teste com IA simulada lenta ou com falha (Specs 009 e 011) |
| Disponibilidade | 99% do tempo de cada mês | RNF-07 (SHOULD, **P**) | Monitoramento, depois de OPEN-09 e OPEN-12 |
| Recuperabilidade | Backup diário com 7 dias de retenção, e uma restauração testada | RNF-08 (SHALL, **P**) | Verificação da rotina, depois de OPEN-09 e OPEN-12 |

**Meta:** zero alteração parcial em falha injetada. Disponibilidade, backup e tempo limite da IA aguardam a confirmação dos valores (P) em OPEN-09.

### 2.3 Segurança — prioridade alta

| Subcaracterística | Critério | Origem | Como verificar |
|---|---|---|---|
| Confidencialidade | Acesso negado por padrão. Cada perfil só executa o que lhe é permitido. A resposta a um cliente não revela dados de outro (RNF-25) | RNF-01, RNF-02, RNF-25, RB-03 | Teste por perfil × operação; teste de acesso a título de outro cliente |
| Confidencialidade | Nenhum nome, documento ou contato vai para o serviço de IA | RNF-22 | Inspeção do conteúdo enviado à IA simulada |
| Integridade | Permissões e alçadas verificadas no servidor, sem depender da interface | RNF-03, RB-02, RB-15 | Teste chamando a operação sem interface |
| Responsabilização | Toda mudança de estado tem responsável, data e ação | RB-01, RF-61, RF-62 | Teste de auditoria por operação |
| Não repúdio | Registro de auditoria não é alterado nem excluído | RB-30, RNF-06 | Teste de tentativa de alteração |
| Autenticidade | Senha só como hash com salt; tráfego só por HTTPS | RNF-04, RNF-05 | Inspeção; teste sem TLS (depois de OPEN-03 e OPEN-12) |

**Meta:** nenhuma célula perfil × operação permitida sem estar explicitamente prevista. Toda mudança de estado auditada.

### 2.4 Manutenibilidade — prioridade alta

| Subcaracterística | Critério | Origem | Como verificar |
|---|---|---|---|
| Modularidade | O domínio não importa aplicação, infraestrutura, framework, banco, canal nem IA | ADR-001; `CLAUDE.md`, regra 9 | Teste de dependência entre camadas |
| Analisabilidade | Cada regra de negócio em um único ponto, com teste nomeado pelo identificador | RNF-19; DA-09 | Revisão de código; busca pelo identificador |
| Testabilidade | A suíte inteira roda sem credencial externa | RNF-23; DA-07 | Execução em ambiente limpo |
| Modificabilidade | Tipos de obrigação, categorias e etapas da régua criados por configuração | RNF-20 | Teste de cadastro e uso (Specs 007, 010, 014) |

**Meta:** 100% das RB implementadas com teste nomeado. Complexidade, tamanho e cobertura de testes são acompanhados nas métricas de [manutenibilidade](manutenibilidade.md), mas a baseline não fixa limite para eles. A medição de cobertura depende da decisão da issue #81.

### 2.5 Usabilidade — prioridade média

| Subcaracterística | Critério | Origem | Como verificar |
|---|---|---|---|
| Proteção contra erro do usuário | Entrada inválida informa o campo e o motivo | RNF-14 | Teste por campo |
| Reconhecibilidade | Estado atual visível em toda tela de orçamento, título e obrigação | RNF-16 | Inspeção das telas |
| Operabilidade | Painel do perfil com as pendências logo após o login; títulos Vencidos e obrigações Atrasadas destacados | RNF-15, RNF-17 | Inspeção por perfil |

**Meta:** toda recusa com motivo. RNF-15 a RNF-17 só são avaliáveis quando houver interface ([usabilidade](usabilidade.md), cenários CU-01 a CU-08).

### 2.6 Eficiência de desempenho — prioridade média

| Subcaracterística | Critério | Origem | Como verificar |
|---|---|---|---|
| Comportamento no tempo | 95% das consultas e cadastros em menos de 2 s | RNF-11 | Medição de P95 ([eficiência](eficiencia.md)) |
| Comportamento no tempo | Envio da régua processado em até 5 min do horário programado | RNF-12 | Medição do atraso (Spec 008) |
| Utilização de recursos | O limite de RNF-11 se mantém durante o processamento em lote | RNF-13 | Medição de P95 durante o lote |

**Meta:** os valores de RNF-11 a RNF-13. A baseline não define volume de referência. A medição atual usa 2000 títulos.

### 2.7 Compatibilidade — prioridade baixa

| Subcaracterística | Critério | Origem | Como verificar |
|---|---|---|---|
| Interoperabilidade | Importação CSV validada linha a linha, aceita inteira ou recusada inteira | RF-83, RF-84, RB-19 | Teste com arquivo inválido (Spec 015) |
| Interoperabilidade | Exportação CSV de títulos, lançamentos e demonstração de resultado | RF-85 | Teste de exportação (Spec 015) |

**Meta:** a baseline não define o leiaute do CSV nem o sistema contábil de destino. Fica para a Spec 015.

### 2.8 Portabilidade — prioridade baixa

| Subcaracterística | Critério | Origem | Como verificar |
|---|---|---|---|
| Adaptabilidade | Roda em Python 3.11 ou mais recente, só com a biblioteca padrão | OPEN-01; `execucao.md` | Suíte em várias versões ([portabilidade](portabilidade.md)) |
| Substituibilidade | Canal de notificação, serviço de IA e repositórios trocáveis sem mudar o domínio | ADR-002, ADR-003, ADR-001 | Simuladores e implementações reais sobre a mesma interface |

**Meta:** a baseline não fixa sistemas operacionais nem ambientes de hospedagem (OPEN-12).

## 3. Critérios de sucesso da visão

Cada critério de sucesso da [visão](../visao.md#7-critérios-de-sucesso) depende principalmente de uma característica.

| Critério de sucesso | Característica | Spec que o entrega |
|---|---|---|
| Nenhum título vence sem cobrança | Adequação funcional | 008 |
| Nenhuma obrigação estoura em silêncio | Adequação funcional | 010 |
| Resultado disponível sem fechamento manual | Adequação funcional, eficiência | 011, 012 |
| Operação rastreável | Segurança (responsabilização) | 001; cada spec |
| IA sob controle | Adequação funcional, segurança | 011 |

## 4. Correspondência com a ISO/IEC 9126

| ISO/IEC 9126 | ISO/IEC 25010 |
|---|---|
| Funcionalidade: adequação, acurácia | Adequação funcional: completude, correção, pertinência |
| Funcionalidade: segurança de acesso | Segurança |
| Funcionalidade: interoperabilidade | Compatibilidade |
| Confiabilidade | Confiabilidade |
| Usabilidade | Usabilidade |
| Eficiência | Eficiência de desempenho |
| Manutenibilidade | Manutenibilidade |
| Portabilidade: coexistência | Compatibilidade |
| Portabilidade: adaptabilidade, instalabilidade, substituibilidade | Portabilidade |

## 5. Situação atual

Resultado das avaliações já feitas, todas sobre a Spec 006, a única implementada.

| Característica | Prioridade | Situação | Documento |
|---|---|---|---|
| Adequação funcional | Alta | Atende, com ressalvas | [Funcionalidade](funcionalidade.md) |
| Confiabilidade | Alta | Boa | [Confiabilidade](confiabilidade.md) |
| Segurança | Alta | Parcial no escopo | [Revisão de código](revisao-de-codigo.md) |
| Manutenibilidade | Alta | Boa | [Manutenibilidade](manutenibilidade.md) |
| Usabilidade | Média | Parcial | [Usabilidade](usabilidade.md) |
| Eficiência de desempenho | Média | Atende RNF-11 | [Eficiência](eficiencia.md) |
| Compatibilidade | Baixa | Não avaliada | — |
| Portabilidade | Baixa | Boa | [Portabilidade](portabilidade.md) |

A equipe deve revisar a prioridade de cada característica quando aprovar este documento.
