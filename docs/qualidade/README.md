# Qualidade — RemindMe

Avaliação da qualidade do produto pelas características da ISO/IEC 25010, mais os testes e a revisão de código. Avalia o que está implementado: a [Spec 006](../../.specify/specs/006-titulo-pagamento-baixa-e-estorno.md). O resumo está no [relatório de qualidade](relatorio-de-qualidade.md).

| Documento | Conteúdo | Issue |
|---|---|---|
| [Critérios de qualidade](criterios.md) | Características relevantes, prioridade e como verificar | #60 |
| [Confiabilidade](confiabilidade.md) | Cenários de falha e recuperação | #48 |
| [Usabilidade](usabilidade.md) | Checklist e cenários de usabilidade | #52 |
| [Eficiência](eficiencia.md) | Métricas de desempenho | #58 |
| [Manutenibilidade](manutenibilidade.md) | Métricas e avaliação do código | #61 |
| [Portabilidade](portabilidade.md) | Testes de ambiente | #63 |
| [Matriz de critérios de aceite](matriz-criterios-de-aceite.md) | Spec → teste → resultado | #66 |
| [Exceções](excecoes.md) | Casos de teste de erro e exceção | #68 |
| [Regressão](regressao.md) | Execuções da suíte antes e depois de cada alteração | #69 |
| [Defeitos](defeitos.md) | Registro de defeitos e evidências | #70 |
| [Revisão de código](revisao-de-codigo.md) | Checklist de revisão | #71 |
| [Segurança de acesso](seguranca-de-acesso.md) | Matriz perfil × operação; autorização, isolamento e auditoria | #75 |
| [Concorrência e idempotência](concorrencia-e-idempotencia.md) | Operações repetidas e falha no meio do pagamento | #76 |
| [Datas e fuso horário](datas-e-fuso.md) | Vencimento, bordas de dia e data de referência | #77 |
| [Acurácia monetária](acuracia-monetaria.md) | Centavos, `Decimal` e valores de muitos dígitos | #78 |
| [Processo e normas de qualidade](processo.md) | SDD × ISO/IEC 12207, ISO 9001 e CMMI | #84 |
| [Relatório de qualidade](relatorio-de-qualidade.md) | Consolidação | #72 |
| [Funcionalidade](funcionalidade.md) | Completude, correção e pertinência das funções implementadas | #62 |
| [Divergências](divergencias.md) | Código × spec × baseline | #57 |

A estratégia de testes, a pirâmide, o plano de testes de API e de ponta a ponta e os simuladores estão em [`docs/testes.md`](../testes.md) (#79, #80, #83). A decisão sobre pytest e cobertura é OPEN-27 (#81), e a integração contínua está em [`execucao.md`](../execucao.md) (#82).

Os testes estão em [`tests/`](../../tests/README.md). Para executar, na raiz do repositório:

```
python3 -m unittest discover -s tests -t .
```
