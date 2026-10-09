# Qualidade — RemindMe

Avaliação da qualidade do produto pelas características da ISO/IEC 25010, mais os testes e a revisão de código. Avalia o que está implementado: a [Spec 006](../../.specify/specs/006-titulo-pagamento-baixa-e-estorno.md). O resumo está no [relatório de qualidade](relatorio-de-qualidade.md).

| Documento | Conteúdo | Issue |
|---|---|---|
| [Confiabilidade](confiabilidade.md) | Cenários de falha e recuperação | #48 |
| [Usabilidade](usabilidade.md) | Checklist e cenários de usabilidade | #52 |
| [Eficiência](eficiencia.md) | Métricas de desempenho | #58 |
| [Manutenibilidade](manutenibilidade.md) | Métricas e avaliação do código | #61 |
| [Portabilidade](portabilidade.md) | Testes de ambiente | #63 |
| [Matriz de critérios de aceite](matriz-criterios-de-aceite.md) | Spec → teste → resultado | #66 |
| [Regressão](regressao.md) | Execuções da suíte antes e depois de cada alteração | #69 |
| [Defeitos](defeitos.md) | Registro de defeitos e evidências | #70 |
| [Revisão de código](revisao-de-codigo.md) | Checklist de revisão | #71 |
| [Relatório de qualidade](relatorio-de-qualidade.md) | Consolidação | #72 |

Os testes estão em [`tests/`](../../tests/README.md). Para executar, na raiz do repositório:

```
python3 -m unittest discover -s tests -t .
```
