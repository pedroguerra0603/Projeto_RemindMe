# UC-10 — Classificar lançamento

| | |
|---|---|
| **Ator principal** | Operador Financeiro |
| **Atores de apoio** | Serviço de IA, Dono |
| **Objetivo** | Dar a cada lançamento a categoria correta do plano de contas, com a IA sugerindo e o sistema decidindo. |
| **Gatilho** | Um lançamento financeiro é gerado (UC-06). |
| **Regras de negócio** | RB-03, RB-08, RB-09, RB-12, RB-14, RB-27 |
| **Requisitos** | RF-51, RF-52, RF-58, RF-59, RF-78 a RF-81, RNF-22, RNF-24, RNF-26 |

## Pré-condições

- O plano de contas tem ao menos uma categoria de receita e uma de despesa.
- O limiar de confiança está configurado (UC-13).

## Fluxo principal

1. O sistema cria o lançamento no estado Pendente de Classificação.
2. O sistema solicita ao serviço de IA uma sugestão de categoria, enviando apenas a descrição do lançamento.
3. O serviço de IA devolve uma categoria e um grau de confiança.
4. O sistema verifica que a categoria existe no plano de contas e que a confiança atinge o limiar (RB-08).
5. O sistema confirma a classificação e muda o lançamento para Classificado.
6. O lançamento passa a entrar na apuração do resultado.

## Fluxos alternativos

- **A1 — Revisão humana.** No passo 4, a sugestão não atende à RB-08. O lançamento vai para a fila de revisão. O Operador Financeiro escolhe a categoria e o fluxo segue no passo 5 (RB-14).
- **A2 — Correção de sugestão.** Na revisão, o usuário confirma categoria diferente da sugerida. O sistema registra a divergência com a sugestão original, a categoria final e o usuário (RB-09).
- **A3 — Reclassificação.** Um usuário autorizado altera a categoria de um lançamento já Classificado. O sistema atualiza a categoria e registra a alteração (RF-59).

## Exceções

- **E1 — Serviço de IA indisponível.** No passo 2, o serviço falha ou excede o tempo limite. O lançamento vai para a fila de revisão (RF-80, RNF-24).
- **E2 — Categoria inexistente.** No passo 4, a categoria sugerida não existe no plano de contas. O lançamento vai para a fila de revisão.
- **E3 — Contador tenta classificar.** O sistema nega a operação: o perfil Contador é somente leitura (RB-03).

## Pós-condições

- Sucesso: lançamento Classificado e incluído na apuração.
- Pendente: lançamento Pendente de Classificação, fora da apuração (RB-12).
- Toda sugestão da IA fica registrada, aceita ou não.
