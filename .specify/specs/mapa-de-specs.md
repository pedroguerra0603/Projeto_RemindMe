# Mapa de Specs — RemindMe

Lista ordenada das unidades implementáveis do sistema. O mapa não é implementação: ele decompõe a baseline de [`/docs`](../../docs/README.md) em fatias com comportamento verificável e mostra em que ordem elas podem ser construídas.

- **Situação do mapa:** Proposto, aguardando revisão da equipe.
- **Gerado em:** 2026-10-03, por agente (Claude), a partir da baseline revisada na mesma data.
- **Revisado por:** *(preencher com nomes e data)*

## Como o mapa foi montado

1. As specs agrupam comportamento por capacidade observável, e não por camada técnica. Não há spec "fazer backend" nem "criar banco".
2. Um RF não vira uma spec automaticamente: RF relacionados ficam na mesma spec.
3. A ordem segue as dependências do domínio. O núcleo de recebíveis vem antes das frentes de apoio.
4. Requisitos transversais (auditoria, autorização, atomicidade) aparecem nos critérios de cada spec que afetam, além de terem a fundação em 001 e 002.
5. Decisão que a baseline não toma está registrada como `OPEN-nn` em [`open.md`](../open.md).

## Mapa

| ID | Spec | RF | RB | RNF | UC | Entidades | Drivers e ADRs | Depende de | Situação |
|---|---|---|---|---|---|---|---|---|---|
| 001 | Fundação: estrutura em camadas e auditoria de operações | RF-04, RF-05, RF-61, RF-62 | RB-01, RB-30 | RNF-06, RNF-09, RNF-19, RNF-21, RNF-23 | — | `RegistroAuditoria` | DA-01, DA-02, DA-03, DA-07, DA-09; ADR-001, ADR-004 | OPEN-01, OPEN-02 | A escrever |
| 002 | Autenticação e autorização por perfil | RF-02, RF-03, RF-65, RF-66, RF-67 | RB-03 | RNF-01 a RNF-05 | UC-01, UC-02 | `Usuario`, `Perfil` | DA-04 | 001; OPEN-03, OPEN-10 | A escrever |
| 003 | Cadastro de clientes | RF-01 | — | RNF-14 | UC-03 | `Cliente` | — | 001, 002 | A escrever |
| 004 | Orçamento: itens, valores e alçada de desconto | RF-06, RF-07, RF-10, RF-13 a RF-18 | RB-15, RB-24 | RNF-03 | UC-04, UC-05 | `Orcamento`, `ItemOrcamento`, `AlcadaDesconto`, `AprovacaoDesconto` | DA-01 | 003 | A escrever |
| 005 | Envio, decisão do cliente e conversão em título | RF-08, RF-09, RF-11, RF-12, RF-19 | RB-05, RB-18 | RNF-09 | UC-04 | `Orcamento`, `Titulo` | DA-01, DA-07; ADR-002 | 004, 006; OPEN-15 | A escrever |
| [006](006-titulo-pagamento-baixa-e-estorno.md) | Título: cadastro manual, pagamento, baixa e estorno | RF-20 a RF-27, RF-30, RF-31, RF-68 | RB-02, RB-21, RB-22, RB-23 | RNF-09, RNF-19 | UC-06 | `Titulo`, `Pagamento` | DA-01, DA-03, DA-09; ADR-001 | 001; para o uso completo, 002 e 003 | **Verificada** |
| 007 | Régua de cobrança: configuração | RF-32, RF-36 | RB-10 | RNF-18, RNF-20 | UC-13 | `ReguaCobranca`, `EtapaCobranca` | DA-10 | 002 | A escrever |
| 008 | Régua de cobrança: execução e histórico | RF-33, RF-34, RF-35, RF-37, RF-38, RF-39, RF-70, RF-71 | RB-10, RB-11, RB-18 | RNF-12, RNF-13 | UC-08 | `TentativaCobranca` | DA-05, DA-07, DA-08; ADR-002 | 006, 007; OPEN-13 | A escrever |
| 009 | Renegociação com extração de intenção | RF-28, RF-29, RF-69, RF-72 a RF-76 | RB-11, RB-17, RB-20, RB-26, RB-27, RB-28 | RNF-22, RNF-24, RNF-25 | UC-07 | `Renegociacao` | DA-06; ADR-003 | 006, 008; OPEN-04, OPEN-06, OPEN-08, OPEN-14 | A escrever |
| 010 | Calendário de obrigações | RF-40 a RF-50, RF-77 | RB-04, RB-07, RB-13, RB-16, RB-29 | RNF-15 | UC-09 | `Obrigacao`, `Evidencia` | DA-01, DA-05 | 002; OPEN-13 | A escrever |
| 011 | Lançamentos e classificação assistida por IA | RF-51, RF-52, RF-58, RF-59, RF-78 a RF-81 | RB-08, RB-09, RB-12, RB-14, RB-27 | RNF-22, RNF-24, RNF-26 | UC-10 | `LancamentoFinanceiro`, `CategoriaFinanceira`, `SugestaoClassificacao` | DA-06; ADR-003 | 006; OPEN-04, OPEN-05, OPEN-07 | A escrever |
| 012 | Apuração do resultado | RF-53 a RF-57, RF-82 | RB-06, RB-12 | RNF-11 | UC-11 | `LancamentoFinanceiro`, `CategoriaFinanceira` | — | 011 | A escrever |
| 013 | Consulta de auditoria | RF-64 | RB-30 | RNF-06 | UC-12 | `RegistroAuditoria` | DA-02; ADR-004 | 001, 002 | A escrever |
| 014 | Configuração de regras | RF-03, RF-14 | RB-07, RB-08, RB-16, RB-28 | RNF-18, RNF-20 | UC-13 | `AlcadaDesconto`, `CategoriaFinanceira` | DA-10 | 002 | A escrever |
| 015 | Importação e exportação em CSV | RF-83, RF-84, RF-85 | RB-19 | RNF-09 | UC-14 | `Cliente`, `Titulo`, `LancamentoFinanceiro` | DA-03 | 003, 006, 012 | A escrever |
| 016 | Painel por perfil | — | RB-13 | RNF-15, RNF-16, RNF-17 | UC-01 | — | — | 006, 010, 011 | A escrever |

RNF-07 (disponibilidade) e RNF-08 (backup) são operacionais. Não pertencem a nenhuma spec de comportamento e serão tratados na entrega, depois de OPEN-09 e OPEN-12.

## Justificativa da ordem

1. **001 a 003** criam o que todas as outras usam: auditoria, acesso e cliente.
2. **006 vem antes de 005** porque a conversão do orçamento precisa de um título para gerar. O título existe sozinho, por cadastro manual (RF-20).
3. **004 e 005** fecham o caminho do orçamento ao título.
4. **007 e 008** cobram os títulos que 006 mantém.
5. **009** depende do título e da régua, que ela suspende.
6. **010** é independente do núcleo de recebíveis e pode ser feita em paralelo depois de 002.
7. **011 e 012** dependem dos pagamentos de 006.
8. **013 a 016** consomem o que as anteriores produzem.

## Primeira spec para implementação

A spec **006** foi escrita primeiro porque:

- concentra as regras centrais do domínio (RB-21, RB-22, RB-23, RB-02);
- é verificável só com o domínio, sem interface e sem banco;
- não depende de nenhuma decisão em aberto além de OPEN-11, que tem resposta simples.

Ela foi aprovada em 2026-10-03 por João Pedro Guerra, Renan Gandolpho e Bernardo Sanches, e verificada na mesma data.

## Perguntas de revisão

Para cada spec do mapa, a equipe deve responder:

- [ ] É pequena o bastante para um PR revisável?
- [ ] Termina em comportamento verificável?
- [ ] Tem rastreabilidade para RF, RB, RNF e UC?
- [ ] Preserva as regras de negócio?
- [ ] Depende de decisão ausente? Se sim, o `OPEN-nn` está registrado?
