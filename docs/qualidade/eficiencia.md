# Avaliação de Eficiência — RemindMe

Issue #58. Característica **Eficiência de desempenho** da ISO/IEC 25010: comportamento no tempo e utilização de recursos.

- **Data:** 2026-10-09.
- **Requisitos de referência:** RNF-11 (95% das consultas e cadastros em menos de 2 s), RNF-13 (lote não degrada o uso interativo).
- **Medição:** [`tests/desempenho/medir_eficiencia.py`](../../tests/desempenho/medir_eficiencia.py), executado com `python3 -m tests.desempenho.medir_eficiencia`.
- **Teste automatizado:** [`tests/desempenho/test_eficiencia.py`](../../tests/desempenho/test_eficiencia.py) verifica o limite de RNF-11 com 300 títulos, a cada execução da suíte.
- **Ambiente:** Linux x86_64, Intel Xeon 2,80 GHz, 4 núcleos; Python 3.13.16; persistência em memória (OPEN-02).

## 1. Operações críticas medidas

| Operação | Por que é crítica |
|---|---|
| Cadastrar título | Operação de cadastro de RNF-11 |
| Registrar pagamento | A mais frequente do Operador Financeiro (UC-06) |
| Estornar pagamento, cancelar título | Alteram dinheiro e estado |
| Consultar com filtro | Operação de consulta de RNF-11; base do painel |
| Verificar vencimentos | Lote que a Spec 008 vai disparar periodicamente (RNF-13) |

Cenário: N títulos de 50 clientes, metade com vencimento ontem. Cada operação é repetida 20 vezes, sobre títulos diferentes.

## 2. Tempo de resposta

| Operação | 100 títulos: P50 / P95 (ms) | 500 títulos: P50 / P95 (ms) | 2000 títulos: P50 / P95 (ms) |
|---|---|---|---|
| Cadastrar título | 1,19 / 1,39 | 5,54 / 8,88 | 23,51 / 24,76 |
| Registrar pagamento | 1,45 / 1,74 | 5,96 / 10,57 | 24,08 / 41,28 |
| Estornar pagamento | 1,52 / 1,74 | 8,32 / 11,02 | 23,28 / 25,28 |
| Cancelar título | 1,50 / 1,60 | 5,98 / 6,43 | 23,43 / 23,77 |
| Consultar com filtro | 3,23 / 5,23 | 12,18 / 13,72 | 46,85 / 48,86 |
| Verificar vencimentos (lote) | 2,87 / 4,05 | 11,63 / 12,21 | 46,15 / 58,27 |

**Resultado para RNF-11:** atende com folga. Com 2000 títulos, o pior P95 é 58 ms, cerca de 3% do limite de 2 s.

## 3. Utilização de memória

| Títulos | Memória do repositório (MiB) | Memória adicional durante um pagamento (MiB) |
|---|---|---|
| 100 | 0,1 | 0,1 |
| 500 | 0,4 | 0,4 |
| 2000 | 1,6 | 1,7 |

## 4. Análise

| ID | Constatação | Causa | Impacto |
|---|---|---|---|
| E-01 | O tempo de **toda** operação cresce linearmente com o número de títulos armazenados, cerca de 12 µs por título, mesmo quando a operação altera um título só | `UnidadeDeTrabalhoEmMemoria.__enter__` copia o repositório inteiro (`copy.deepcopy`) para poder desfazer a transação | Por extrapolação linear, o limite de RNF-11 seria atingido perto de 170 mil títulos. Para uma pequena empresa, longe do volume real |
| E-02 | Cada transação ocupa memória adicional igual ao tamanho do repositório | Mesma causa de E-01 | Duplica a memória durante a operação |
| E-03 | A consulta abre transação e copia todos os títulos, mesmo sem alterar nada | `consultar_titulos` usa a unidade de trabalho, e `listar` devolve cópia de cada título | Consulta custa o dobro das operações de alteração |
| E-04 | Cadastrar N títulos em sequência custa O(N²): 2000 títulos levam cerca de 23 s | Consequência de E-01 | Afeta importação em lote (Spec 015) se a persistência continuar em memória |

As quatro constatações vêm da implementação em memória, que é provisória até a escolha do banco (OPEN-02). O domínio não tem custo relevante: as regras de pagamento, estorno e vencimento são O(número de pagamentos do título).

## 5. Recomendações

| Recomendação | Onde tratar |
|---|---|
| Não otimizar a implementação em memória agora: atende RNF-11 e será substituída | — |
| Com o banco escolhido, refazer as medições com o mesmo script e o mesmo cenário, e manter o teste de RNF-11 | Spec 001, OPEN-02 |
| Medir o lote de vencimentos concorrendo com operações interativas, para RNF-13 | Spec 008 |
| Se a importação CSV usar a persistência em memória, gravar o lote em uma transação só, e não uma por linha | Spec 015 |
