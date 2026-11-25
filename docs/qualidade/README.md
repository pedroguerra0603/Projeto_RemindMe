# Qualidade — RemindMe

Avaliação da qualidade do produto pelas características da ISO/IEC 25010, mais os testes e a revisão de código. O resumo está no [relatório de qualidade](relatorio-de-qualidade.md).

> **Como ler esta pasta.** Os documentos abaixo são o registro de duas rodadas de qualidade, de 2026-10-09 e de 2026-10-16, feitas quando só a [Spec 006](../../.specify/specs/006-titulo-pagamento-baixa-e-estorno.md) estava implementada. Eles ficam como estão, com a data, porque registram o que foi medido naquele momento. A situação atual está em: [`testes.md`](../testes.md) (suíte e pirâmide), [`execucao.md`](../execucao.md#integração-contínua) (integração contínua em 9 combinações), [`defeitos.md`](defeitos.md) (D-07 a D-10, de 2026-11-25), [`portabilidade.md`](portabilidade.md#6-atualização-de-2026-11-25-windows-e-macos) (seção 6) e [`divergencias.md`](divergencias.md).

| Documento | Conteúdo | Issue | Data |
|---|---|---|---|
| [Critérios de qualidade](criterios.md) | Características relevantes, prioridade e como verificar | #60 | 2026-10-16 |
| [Confiabilidade](confiabilidade.md) | Cenários de falha e recuperação | #48 | 2026-10-09 |
| [Usabilidade](usabilidade.md) | Checklist e cenários de usabilidade | #52 | 2026-10-09 |
| [Eficiência](eficiencia.md) | Métricas de desempenho | #58 | 2026-10-09 |
| [Manutenibilidade](manutenibilidade.md) | Métricas e avaliação do código | #61 | 2026-10-09 |
| [Portabilidade](portabilidade.md) | Testes de ambiente | #63 | 2026-10-09 |
| [Matriz de critérios de aceite](matriz-criterios-de-aceite.md) | Spec → teste → resultado | #66 | 2026-10-09 |
| [Exceções](excecoes.md) | Casos de teste de erro e exceção | #68 | 2026-10-09 |
| [Regressão](regressao.md) | Execuções da suíte antes e depois de cada alteração | #69 | 2026-10-09 |
| [Defeitos](defeitos.md) | Registro de defeitos e evidências | #70 | 2026-10-09 |
| [Revisão de código](revisao-de-codigo.md) | Checklist de revisão | #71 | — |
| [Segurança de acesso](seguranca-de-acesso.md) | Matriz perfil × operação; autorização, isolamento e auditoria | #75 | 2026-10-16 |
| [Concorrência e idempotência](concorrencia-e-idempotencia.md) | Operações repetidas e falha no meio do pagamento | #76 | 2026-10-16 |
| [Datas e fuso horário](datas-e-fuso.md) | Vencimento, bordas de dia e data de referência | #77 | 2026-10-16 |
| [Acurácia monetária](acuracia-monetaria.md) | Centavos, `Decimal` e valores de muitos dígitos | #78 | 2026-10-16 |
| [Processo e normas de qualidade](processo.md) | SDD × ISO/IEC 12207, ISO 9001 e CMMI | #84 | 2026-10-16 |
| [Relatório de qualidade](relatorio-de-qualidade.md) | Consolidação | #72 | 2026-10-09 |
| [Funcionalidade](funcionalidade.md) | Completude, correção e pertinência das funções implementadas | #62 | 2026-10-16 |
| [Divergências](divergencias.md) | Código × spec × baseline | #57 | 2026-10-16 |

A estratégia de testes, a pirâmide, o plano de testes de API e de ponta a ponta e os simuladores estão em [`docs/testes.md`](../testes.md) (#79, #80, #83). A decisão sobre pytest e cobertura é OPEN-27 (#81), e a integração contínua está em [`execucao.md`](../execucao.md) (#82).

Os testes estão em [`tests/`](../../tests/README.md). Para executar, na raiz do repositório:

```
python3 -m unittest discover -s tests -t .
```
