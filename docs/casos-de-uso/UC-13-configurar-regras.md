# UC-13 — Configurar regras

| | |
|---|---|
| **Ator principal** | Administrador |
| **Atores de apoio** | Dono |
| **Objetivo** | Ajustar as regras variáveis do processo sem alterar o que já aconteceu. |
| **Gatilho** | O Administrador solicita a alteração de uma configuração. |
| **Regras de negócio** | RB-07, RB-08, RB-15, RB-16, RB-18, RB-28 |
| **Requisitos** | RF-03, RF-14, RF-32, RF-36, RNF-18, RNF-19, RNF-20 |

## Pré-condições

- O Administrador está autenticado.

## Fluxo principal

1. O Administrador escolhe o que configurar: alçadas de desconto, régua de cobrança, tipos de obrigação e antecedência de aviso, categorias financeiras, limiar de confiança da IA, limites de renegociação ou canal de notificação.
2. O Administrador informa os novos valores.
3. O sistema valida a configuração.
4. O sistema grava a configuração e registra a alteração na auditoria.
5. O sistema aplica a configuração aos processamentos seguintes.

## Fluxos alternativos

- **A1 — Habilitar canal WhatsApp.** No passo 2, o Administrador habilita o canal WhatsApp. Cobranças e alertas seguintes usam esse canal (RB-18).
- **A2 — Nova etapa de cobrança.** No passo 2, o Administrador inclui uma etapa na régua. A etapa vale apenas para envios ainda não realizados (RF-36).

## Exceções

- **E1 — Configuração inválida.** No passo 3, o sistema recusa a configuração e informa o campo e o motivo. Exemplos: alçada fora de 0 a 100%, régua sem etapa, limiar fora de 0 a 1.
- **E2 — Categoria em uso.** A exclusão de uma categoria com lançamentos é recusada.

## Pós-condições

- Sucesso: configuração gravada e auditada; registros anteriores inalterados (RNF-18).
- Falha: configuração anterior mantida.
