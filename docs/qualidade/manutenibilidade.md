# Avaliação de Manutenibilidade — RemindMe

Issue #61. Característica **Manutenibilidade** da ISO/IEC 25010, nas subcaracterísticas pedidas: analisabilidade, modificabilidade, estabilidade e testabilidade. As subcaracterísticas de modularidade e reusabilidade entram junto com modificabilidade.

- **Data:** 2026-10-09.
- **Escopo:** `src/remindme/` na versão de `main` em `b17b1ed`, mais as correções de #70.
- **Requisitos de referência:** RNF-19 (cada regra em um único ponto, com teste nomeado), RNF-20 (configuração sem código), ADR-001 (domínio isolado), DA-09.
- **Teste automatizado:** [`tests/arquitetura/test_camadas.py`](../../tests/arquitetura/test_camadas.py) passa a vigiar a regra de dependência a cada execução da suíte.

## 1. Métricas

Contagem por análise da árvore sintática (`ast`), sem linhas em branco e sem comentários. Complexidade ciclomática de McCabe: 1 + número de decisões.

| Módulo | Camada | Linhas | Funções | Maior complexidade | Importa |
|---|---|---|---|---|---|
| `dominio/titulo.py` | Domínio | 123 | 9 | 5 (`registrar_pagamento`, `estornar_pagamento`) | `dominio` |
| `dominio/regras.py` | Domínio | 11 | 2 | 2 | `dominio` |
| `dominio/usuario.py`, `auditoria.py`, `erros.py` | Domínio | 31 | 1 | 1 | — |
| `aplicacao/servico_titulos.py` | Aplicação | 162 | 12 | 8 (`_atende`, uma expressão booleana de 4 filtros) | `aplicacao`, `dominio` |
| `aplicacao/portas.py` | Aplicação | 21 | 8 | 1 | `dominio` |
| `infraestrutura/memoria.py` | Infraestrutura | 49 | 13 | 2 | `dominio` |
| **Total** | | **397** | **45** | | |

| Indicador | Valor | Referência usual |
|---|---|---|
| Maior complexidade ciclomática | 8 | Até 10 é considerado simples |
| Maior função | 22 linhas (`cadastrar_manual`, com a docstring) | — |
| Importações não usadas | 0 | 0 |
| Dependências fora da biblioteca padrão | 0 | OPEN-01 |
| Testes automatizados | Contagem final no [relatório de qualidade](relatorio-de-qualidade.md) | — |

## 2. Avaliação por subcaracterística

| Subcaracterística | Avaliação | Evidência |
|---|---|---|
| Analisabilidade | **Boa** | Nomes do glossário em todo o código (`Titulo`, `Pagamento`, `saldo`, `estornar_pagamento`). Cada regra cita o identificador na docstring ou na mensagem (RB-21, RB-22, RB-23, RB-02). A estrutura de pastas é a das camadas de `docs/arquitetura.md`. |
| Modificabilidade | **Boa** | Domínio sem dependência externa (verificado por `test_ADR_001_*`). A persistência fica atrás de `portas.py`; trocar a implementação em memória por um banco não toca no domínio. Os estados aceitos por operação estão em constantes (`ESTADOS_QUE_ACEITAM_PAGAMENTO`), o que facilita incluir Em Renegociação na Spec 009. |
| Estabilidade | **Regular** | `Titulo` é uma `dataclass` mutável com atributos públicos. Qualquer chamador pode atribuir `titulo.estado` ou `titulo.valor` diretamente e contornar RB-21 e INV-5. Hoje nenhum chamador faz isso, mas nada impede (M-01). |
| Testabilidade | **Boa** | Relógio e data de referência são injetados; repositórios em memória; regras de domínio testáveis sem aplicação. Ponto fraco: o identificador de título e de pagamento é gerado com `uuid4` dentro do serviço e não pode ser fixado no teste (M-04). |

## 3. Constatações

| ID | Constatação | Severidade | Recomendação |
|---|---|---|---|
| M-01 | Estado e valor do título podem ser alterados por atribuição direta, sem passar pelas regras | Média | Propor à equipe proteger os atributos (por exemplo, `estado` só de leitura e alterado por métodos do domínio). Muda a forma do código, não o comportamento; não foi feito nesta issue |
| M-02 | Os quatro métodos de alteração do serviço repetem a mesma sequência: abrir transação, obter, guardar estado anterior, chamar o domínio, salvar e auditar | Baixa | Aceitável com quatro operações. Extrair um método comum se surgirem mais operações sobre título (Spec 009) |
| M-03 | O serviço usa ora `uow.titulos`, ora `self._uow.titulos` para o mesmo objeto | Baixa | Padronizar em uma das formas na próxima alteração do serviço |
| M-04 | Identificadores gerados internamente com `uuid4`, sem como injetar | Baixa | Injetar um gerador de identificador, como já se faz com o relógio, quando um teste precisar disso |
| M-05 | As mensagens misturam texto para o usuário e identificador de regra | Baixa | Ver recomendação de [usabilidade](usabilidade.md) |
| M-06 | Validação de entrada incompleta: valor não `Decimal`, `NaN` ou infinito gerava erro interno | Alta | Corrigido em #70 ([defeitos](defeitos.md)) |
| M-07 | Não há verificação automática de estilo nem de tipos | Baixa | Decidir junto da issue sobre ferramentas de teste (OPEN sobre pytest e cobertura); exige instalar dependência |

## 4. Conclusão

O código é pequeno, segue as camadas da arquitetura e mantém as regras de negócio em um único ponto do domínio, como exige RNF-19. A principal fragilidade é de estabilidade (M-01): a proteção das invariantes depende de disciplina, e não do código. O teste de camadas adicionado nesta issue impede que a regra de dependência do ADR-001 seja quebrada sem que a suíte acuse.
