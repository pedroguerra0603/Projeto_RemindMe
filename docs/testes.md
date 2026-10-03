# Estratégia de Testes e Qualidade — RemindMe

> O projeto ainda não tem código. Este documento define como os testes serão organizados quando a implementação começar. As ferramentas dependem das escolhas de tecnologia (OPEN-01).

## Princípios

1. **Cada cláusula obrigatória vira ao menos um teste.** Todo RF com SHALL e toda RB têm teste.
2. **O teste leva o identificador no nome.** Exemplo: `RB-23_recusa_pagamento_maior_que_o_saldo`.
3. **Regra de domínio é testada sem banco e sem interface.**
4. **A suíte roda sem credencial externa**, com canal de notificação e serviço de IA simulados (RNF-23).
5. **O critério de aceite é binário.** Cada critério de uma spec, no formato Dado, Quando, Então, corresponde a um teste que passa ou não passa.

## Níveis

| Nível | O que cobre | Depende de |
|---|---|---|
| Unidade de domínio | Regras de negócio, cálculos e transições de estado | Nada externo |
| Aplicação | Casos de uso: permissão, transação, auditoria | Repositórios em memória; canal e IA simulados |
| Integração | Persistência, atomicidade, unicidade | Banco de dados de teste |
| Aceite | Critérios Dado, Quando, Então de cada spec | Sistema completo com simuladores |

## O que não pode faltar

| Assunto | Teste |
|---|---|
| Estados | Toda transição válida das [tabelas de estados](uml/estados.md) e ao menos uma transição inválida por entidade |
| Alçada | Desconto igual à alçada, um ponto acima e um ponto abaixo (RB-15) |
| Pagamento | Valor zero, negativo, igual ao saldo, maior que o saldo (RB-23) |
| Autorização | Cada perfil × cada operação sensível (RNF-02) |
| Isolamento do cliente | Cliente tenta acessar título de outro cliente (RNF-25) |
| Atomicidade | Falha injetada no meio de uma operação financeira (RNF-09) |
| IA | Confiança igual, acima e abaixo do limiar; categoria inexistente; falha; tempo excedido (RB-08, RB-14) |
| Régua | Execução repetida do agendador não repete etapa (DA-08) |
| Auditoria | Toda mudança de estado gera registro; tentativa de alteração é recusada (RB-01, RB-30) |

## Definição de pronto

Uma issue de implementação está pronta quando:

1. o código implementa a spec aprovada, sem comportamento além dela;
2. todos os critérios de aceite da spec têm teste passando;
3. a suíte inteira passa;
4. spec e código foram alterados no mesmo PR, quando o comportamento mudou;
5. o PR foi revisado por um colega e fecha a issue com `Closes #N`.

## Verificação manual

Enquanto não houver suíte automatizada, a verificação de cada spec é registrada em `.specify/specs/NNN-verificacao.md`, com um resultado por critério de aceite: passou, não passou ou não verificado.

## Rastreabilidade

Cláusula EARS → Issue → PR → commits → teste. A ligação é feita pelo identificador: ele aparece no título da issue, na descrição do PR e no nome do teste.
