# Relatório de Qualidade — RemindMe

Issue #72. Consolida os resultados dos testes, as métricas, os problemas encontrados e as correções feitas na rodada de qualidade de outubro de 2026 (issues #48 a #71).

- **Data:** 2026-10-09.
- **Objeto avaliado:** a Spec 006 (título: cadastro manual, pagamento, baixa e estorno), única spec implementada. Linha de base: `b17b1ed`.
- **Referência:** características de qualidade do produto da ISO/IEC 25010.
- **Execução:** issues atribuídas a Renan Ribeiro Gandolpho, executadas com agente de codificação (Claude Code), com coautoria de Renan nos commits e revisão no PR, conforme o uso de agentes descrito em `docs/combinados.md`.

## 1. Resumo

| Indicador | Antes (`b17b1ed`) | Depois |
|---|---|---|
| Testes automatizados | 48 | 132 |
| Critérios de aceite da Spec 006 passando | 24 de 24 | 24 de 24 |
| Transições de estado testadas (estado × operação) | parcial | 20 de 20 |
| Defeitos conhecidos | 0 | 5 encontrados, 5 corrigidos |
| Versões do Python verificadas | 1 | 3 (3.11, 3.12, 3.13) |
| Pior P95 com 2000 títulos | não medido | 58 ms (limite de RNF-11: 2 s) |
| Questões em aberto novas | — | 1 (OPEN-20) |

**Conclusão.** A Spec 006 atende a todos os seus critérios de aceite e invariantes, e as falhas injetadas não deixam alteração parcial. Os cinco defeitos encontrados eram de validação de entrada e foram corrigidos no domínio, sem regressão. As fragilidades restantes são de estabilidade do código (atributos do título alteráveis por atribuição direta) e de limites da implementação provisória em memória, que dependem de decisões em aberto (OPEN-02).

## 2. Resultados dos testes

Execução de 2026-10-09: `python3 -m unittest discover -s tests -t .` → `Ran 132 tests ... OK`.

| Nível | Pasta | Testes | Issue | Resultado |
|---|---|---|---|---|
| Unidade de domínio | `tests/dominio/` | 56 (19 de regras, 27 de unidades, 10 de invariantes) | #64, #67 | Passou |
| Unidade de infraestrutura | `tests/infraestrutura/` | 11 | #64 | Passou |
| Aplicação: aceite | `tests/aplicacao/test_spec_006_aceite.py` | 29 | Spec 006 | Passou |
| Aplicação: confiabilidade | `tests/aplicacao/test_confiabilidade.py` | 6 | #48 | Passou |
| Aplicação: usabilidade | `tests/aplicacao/test_usabilidade.py` | 4 | #52 | Passou |
| Aplicação: exceções | `tests/aplicacao/test_excecoes.py` | 11 | #68 | Passou após #70 |
| Integração | `tests/integracao/` | 9 | #65 | Passou |
| Arquitetura | `tests/arquitetura/` | 3 | #61 | Passou |
| Desempenho | `tests/desempenho/` | 3 | #58 | Passou |
| **Total** | | **132** | | **Passou** |

| Verificação | Resultado | Documento |
|---|---|---|
| Matriz spec → teste → resultado | 24 de 24 critérios; A1 a A6, E1 a E8 e INV-1 a INV-8 cobertos | [Matriz](matriz-criterios-de-aceite.md) |
| Regressão por commit | Nenhuma regressão em 16 commits; os 48 testes da linha de base passam contra o código corrigido | [Regressão](regressao.md) |
| Ambientes | 11 ambientes, todos passando | [Portabilidade](portabilidade.md) |
| Mutação manual | 5 mutações nas regras, todas detectadas | [Revisão de código](revisao-de-codigo.md), R-28 |

## 3. Avaliação por característica

| Característica (ISO/IEC 25010) | Avaliação | Principal evidência | Documento |
|---|---|---|---|
| Adequação funcional | Atende | 24 de 24 critérios; tabela de transições completa; regras de perfil para todos os perfis | [Matriz](matriz-criterios-de-aceite.md) |
| Confiabilidade | Boa | Falha na auditoria ou na gravação, em qualquer operação, não deixa alteração parcial (F-01 a F-07) | [Confiabilidade](confiabilidade.md) |
| Eficiência de desempenho | Atende RNF-11 | P95 de 58 ms com 2000 títulos. Custo linear no volume, pela cópia do repositório em memória (E-01) | [Eficiência](eficiencia.md) |
| Usabilidade | Parcial | Toda recusa informa campo e motivo (RNF-14). Sem interface; mensagens com identificador de regra e valor fora do formato brasileiro | [Usabilidade](usabilidade.md) |
| Manutenibilidade | Boa | 403 linhas, complexidade máxima 8, domínio isolado verificado por teste. Atributos do título alteráveis de fora (M-01) | [Manutenibilidade](manutenibilidade.md) |
| Portabilidade | Boa | Só a biblioteca padrão; passa em 3 versões do Python e 11 ambientes. Windows e macOS não testados | [Portabilidade](portabilidade.md) |
| Segurança | Parcial no escopo | Estorno e cancelamento só pelo Dono, para todos os perfis; recusa por perfil não revela o título. Autenticação e isolamento do Cliente dependem das Specs 002 e 009 | [Revisão de código](revisao-de-codigo.md), R-22 a R-24 |
| Compatibilidade | Não avaliada | Não há integração com outro sistema | — |

## 4. Métricas

| Métrica | Valor |
|---|---|
| Linhas de código de produção (sem brancos e comentários) | 403 |
| Linhas de código de teste | 1.388 |
| Funções de produção | 46 |
| Maior complexidade ciclomática | 8 (`_atende`, filtro da consulta) |
| Dependências externas | 0 |
| Tempo da suíte | cerca de 3,3 s |
| P95 das operações interativas, 2000 títulos | 24 a 49 ms; lote de vencimentos, 58 ms |
| Memória adicional por transação, 2000 títulos | 1,7 MiB (cópia do repositório) |

## 5. Problemas encontrados e correções

| ID | Problema | Severidade | Situação | Documento |
|---|---|---|---|---|
| D-01 | `NaN` gera erro interno em vez de recusa | Média | Corrigido em #70 | [Defeitos](defeitos.md) |
| D-02 | Título com valor infinito é aceito | Alta | Corrigido em #70 | [Defeitos](defeitos.md) |
| D-03 | Pagamento em `float` fica anexado ao título antes do erro | Alta | Corrigido em #70 | [Defeitos](defeitos.md) |
| D-04 | Valor em texto ou `None` gera erro interno | Média | Corrigido em #70 | [Defeitos](defeitos.md) |
| D-05 | Motivo que não é texto gera erro interno | Baixa | Corrigido em #70 | [Defeitos](defeitos.md) |
| OPEN-20 | Precisão monetária não definida: R$ 0,001 é aceito | — | Registrada para decisão da equipe | [`.specify/open.md`](../../.specify/open.md) |
| M-01 | Estado e valor do título alteráveis por atribuição direta | Média | Recomendação à equipe | [Manutenibilidade](manutenibilidade.md) |
| E-01 | Toda operação copia o repositório inteiro | Baixa no volume atual | Aguarda OPEN-02 | [Eficiência](eficiencia.md) |
| U-09, U-10 | Mensagens com identificador de regra; valor fora do formato brasileiro | Baixa | Recomendação para a primeira spec com interface | [Usabilidade](usabilidade.md) |
| — | A suíte original não detectava a troca de `>=` por `>` no estorno no dia do vencimento | — | Coberto por teste novo em #64 | [Revisão de código](revisao-de-codigo.md) |

## 6. Pendências e próximos passos

| Pendência | Depende de |
|---|---|
| Decidir a precisão monetária | OPEN-20 |
| Decidir se pagamento com data futura é aceito | OPEN-17 |
| Proteger estado e valor do título (M-01) | Proposta à equipe |
| Repetir confiabilidade, eficiência e integração com banco real | OPEN-02, Spec 001 |
| Registrar erro não tratado com identificador de correlação (RNF-21) | Spec 001 |
| Executar os cenários de usabilidade CU-01 a CU-08 | Primeira spec com interface (OPEN-01) |
| Rodar a suíte em Windows e macOS, a cada PR | Issue de integração contínua |

## 7. Documentos da rodada

[Confiabilidade](confiabilidade.md) · [Usabilidade](usabilidade.md) · [Eficiência](eficiencia.md) · [Manutenibilidade](manutenibilidade.md) · [Portabilidade](portabilidade.md) · [Matriz de critérios](matriz-criterios-de-aceite.md) · [Exceções](excecoes.md) · [Regressão](regressao.md) · [Defeitos](defeitos.md) · [Revisão de código](revisao-de-codigo.md)
