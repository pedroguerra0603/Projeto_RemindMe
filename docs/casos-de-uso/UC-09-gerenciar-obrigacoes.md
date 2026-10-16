# UC-09 — Gerenciar obrigações

| | |
|---|---|
| **Ator principal** | Operador Financeiro |
| **Atores de apoio** | Dono, Agendador |
| **Objetivo** | Cumprir no prazo as obrigações fiscais e contratuais da empresa, com comprovação. |
| **Gatilho** | Um usuário autorizado cadastra uma obrigação, ou o agendador verifica os prazos. |
| **Regras de negócio** | RB-01, RB-04, RB-07, RB-13, RB-16, RB-29 |
| **Requisitos** | RF-40 a RF-50, RF-77, RNF-15 |

## Pré-condições

- O usuário está autenticado com perfil Operador Financeiro ou Dono.

## Fluxo principal

1. O usuário cadastra a obrigação com tipo, periodicidade, prazo, responsável e se exige evidência.
2. O sistema apresenta a obrigação no calendário, no estado Pendente.
3. Na antecedência configurada, o sistema alerta o responsável (RB-07).
4. O responsável registra o cumprimento e anexa a evidência.
5. O sistema muda o estado para Cumprida e registra data, usuário e evidência.
6. Se a obrigação é recorrente, o sistema gera a próxima ocorrência com o novo prazo.

## Fluxos alternativos

- **A1 — Obrigação sem exigência de evidência.** No passo 4, o responsável registra o cumprimento sem anexo. O fluxo segue no passo 5.
- **A2 — Cumprimento sem a evidência exigida.** No passo 4, o responsável registra o cumprimento sem anexar a evidência exigida. O sistema muda o estado para Aguardando Evidência e mantém o alerta no painel do Operador Financeiro até o anexo (RB-13, RB-29).
- **A3 — Alteração de prazo ou responsável.** Um usuário autorizado altera o prazo ou o responsável. O sistema registra a alteração no histórico da obrigação (RF-41).

## Exceções

- **E1 — Prazo estoura.** O prazo passa sem que a obrigação esteja Cumprida. O sistema muda o estado para Atrasada (RF-48).
- **E2 — Atraso persiste.** A obrigação permanece Atrasada pela tolerância configurada. O sistema envia alerta escalonado ao Dono (RB-16).
- **E3 — Dados obrigatórios ausentes.** No passo 1, o sistema recusa o cadastro e indica os campos faltantes.

## Pós-condições

- Sucesso: obrigação Cumprida, com data, usuário e evidência; próxima ocorrência gerada quando recorrente.
- Atraso: obrigação Atrasada, com o atraso registrado no histórico e o Dono alertado.

## Diagramas

- Estados da obrigação: [estados](../uml/estados.md#obrigação).
