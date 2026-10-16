# Avaliação de Confiabilidade — RemindMe

Issue #48. Característica **Confiabilidade** da ISO/IEC 25010: maturidade, tolerância a falhas e recuperabilidade. Avaliada sobre o que está implementado, a Spec 006.

- **Data:** 2026-10-09.
- **Escopo:** `src/remindme/` na branch `main` em `b17b1ed`, mais as correções desta avaliação.
- **Requisitos de referência:** RNF-09 (atomicidade), RNF-21 (registro de erro não tratado), RNF-07 e RNF-08 (disponibilidade e backup, ainda **(P)**), INV-7 e E8 da Spec 006.
- **Testes:** [`tests/aplicacao/test_confiabilidade.py`](../../tests/aplicacao/test_confiabilidade.py).

## 1. Operações críticas

São as operações que alteram dinheiro ou estado. Uma falha no meio delas é o risco principal do sistema.

| Operação | Serviço | O que grava |
|---|---|---|
| Cadastrar título | `cadastrar_titulo` | Título; auditoria |
| Registrar pagamento | `registrar_pagamento` | Pagamento no título; estado; auditoria da operação e da mudança de estado |
| Verificar vencimentos | `verificar_vencimentos` | Estado de vários títulos; auditoria de cada mudança |
| Estornar pagamento | `estornar_pagamento` | Pagamento estornado; estado; auditoria |
| Cancelar título | `cancelar_titulo` | Estado; auditoria |

## 2. Cenários de falha e recuperação

| ID | Falha | Reação esperada | Recuperação | Evidência | Resultado |
|---|---|---|---|---|---|
| F-01 | A gravação da auditoria falha no meio de qualquer operação crítica | A operação é desfeita por inteiro; o erro chega ao chamador | Nenhuma: não há o que corrigir nos dados | `test_RNF_09_falha_em_cada_operacao_nao_deixa_alteracao_parcial` (falha na auditoria × 5 operações); `test_CA_23` | Passou |
| F-02 | A gravação do título falha no meio de qualquer operação crítica | Idem | Idem | `test_RNF_09_falha_em_cada_operacao_nao_deixa_alteracao_parcial` (falha na gravação × 5 operações) | Passou |
| F-03 | A falha ocorre no meio do lote de vencimentos, depois de alguns títulos já marcados | O lote inteiro é desfeito | O lote é executado de novo na próxima verificação | `test_RNF_09_falha_no_meio_do_lote_de_vencimentos_desfaz_o_lote_inteiro` | Passou |
| F-04 | O usuário repete a operação depois da falha | O efeito acontece uma única vez | — | `test_RNF_09_operacao_repetida_depois_da_falha_tem_o_efeito_de_uma_unica_vez` | Passou |
| F-05 | Depois de uma falha, outro usuário consulta os títulos | A consulta funciona e mostra o estado anterior à falha | — | `test_RNF_09_consulta_continua_disponivel_depois_de_falha` | Passou |
| F-06 | A unidade de trabalho é reutilizada depois de uma falha | Ela fica pronta para a próxima transação | — | `test_RNF_09_unidade_de_trabalho_fica_pronta_depois_da_falha` | Passou |
| F-07 | O chamador altera o objeto `Titulo` que recebeu | O que está armazenado não muda | — | `test_INV_7_alterar_o_objeto_devolvido_nao_altera_o_armazenado` | Passou |
| F-08 | Entrada inválida (valor `NaN`, infinito, `float`, texto; motivo que não é texto) | Recusa com motivo, sem alterar dados (E1, E7) | — | [`test_excecoes.py`](../../tests/aplicacao/test_excecoes.py) | Não passava: defeitos D-01 a D-04, corrigidos em #70 |
| F-09 | Erro não tratado | Registrar data, operação, usuário e identificador de correlação (RNF-21) | — | Não implementado: depende da Spec 001 | Pendente |
| F-10 | Perda do processo ou da máquina | Os dados sobrevivem; backup diário (RNF-08) | Restauração do backup | Não aplicável: persistência em memória até OPEN-02 | Pendente |

Os testes F-01 a F-03 foram validados por mutação: com a restauração da unidade de trabalho desligada, 7 casos falham.

## 3. Avaliação por subcaracterística

| Subcaracterística | Avaliação | Justificativa |
|---|---|---|
| Maturidade | Boa no escopo da Spec 006 | 24 critérios de aceite passam; invariantes verificados a cada passo de 50 sequências aleatórias (CA-24). Quatro defeitos de validação de entrada encontrados e corrigidos (#70). |
| Tolerância a falhas | Boa | Toda operação crítica é atômica (F-01 a F-03). Recusa por regra não altera dados. |
| Recuperabilidade | Parcial | A transação desfaz a operação, e o usuário pode repetir (F-04). Não há persistência nem backup: os dados se perdem ao fim do processo (F-10). |
| Disponibilidade | Não avaliável | Não há sistema implantado (OPEN-09, OPEN-12). |

## 4. Riscos e recomendações

| Risco | Recomendação | Onde tratar |
|---|---|---|
| A atomicidade em memória é feita por cópia de todo o estado; não vale para concorrência entre processos | Usar a transação do banco quando OPEN-02 for decidida e repetir F-01 a F-03 como testes de integração | Spec 001 |
| Erro não tratado não é registrado | Implementar RNF-21 com identificador de correlação | Spec 001 |
| Lote de vencimentos é tudo ou nada; um título com problema impede o lote inteiro | Avaliar se o lote deve ser por título quando o agendador existir (OPEN-13) | Spec 008 |
| Sem backup | Definir as metas de RNF-07 e RNF-08 | OPEN-09 |
