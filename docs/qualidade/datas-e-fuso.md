# Datas, Vencimentos e Fuso Horário — RemindMe

Issue #77. Lição do caso dos ingressos online (Rock in Rio 2019), em que a divergência de fuso horário entre servidores liberou vendas antes do horário oficial. No RemindMe, vencimento de título, atraso de obrigação e horário de envio da régua dependem de "hoje": um erro de fuso ou de borda de dia muda o estado de títulos e obrigações.

- **Data:** 2026-10-16.
- **Objeto:** Spec 006.
- **Requisitos e regras:** RF-24, RF-25, RF-62, RB-21; OPEN-17, OPEN-19, OPEN-23.
- **Testes:** [`tests/dominio/test_datas.py`](../../tests/dominio/test_datas.py) (14) e [`tests/aplicacao/test_datas_na_aplicacao.py`](../../tests/aplicacao/test_datas_na_aplicacao.py) (4). Todos passam.

## 1. A data de referência é injetada

| Ponto | Como é |
|---|---|
| Domínio | `marcar_vencido(data_referencia)`, `estornar_pagamento(..., data_referencia)` e `proximo_do_vencimento(data_referencia, ...)` recebem a data de fora |
| Aplicação | `verificar_vencimentos(usuario, data_referencia)`; a hora da auditoria vem da porta `Relogio` |
| Garantia | `test_RF_24_codigo_de_producao_nao_le_o_relogio_da_maquina` falha se qualquer arquivo de `src/remindme/` usar `today`, `now`, `utcnow` ou `fromtimestamp` |

## 2. Casos de teste

| Caso | Resultado esperado | Teste |
|---|---|---|
| Título que vence **hoje** | Continua Aberto (não está Vencido) | `test_RF_24_titulo_que_vence_hoje_...` |
| Título que venceu **ontem** | Passa a Vencido | `test_RF_24_titulo_que_venceu_ontem_...` |
| Título que vence amanhã | Continua Aberto | `test_RF_24_titulo_que_vence_amanha_...` |
| O dia seguinte ao vencimento | Vence | `test_RF_24_o_dia_seguinte_...` |
| Verificar duas vezes no mesmo dia | Muda uma vez só | `test_RF_24_verificar_duas_vezes_...` |
| Virada de mês, de ano e ano bissexto (29/02/2028; 28/02/2027) | Venceu no dia seguinte, não no próprio dia | `test_RF_24_virada_de_mes_ano_e_bissexto` |
| Proximidade do vencimento (RF-23) | Inclui hoje e o último dia da antecedência | `test_RF_23_...` |
| Estorno no dia do vencimento / no dia seguinte | Volta a Aberto / a Vencido | `test_RF_30_estorno_no_dia_...` |
| Verificação de vencimentos na borda (serviço) | Só o que venceu muda; o que vence hoje fica | `test_RF_24_verificacao_de_vencimentos_na_borda_...` |
| Hora da auditoria às 23:59:59 e 00:00:01 | Vem do relógio injetado | `test_RF_62_a_hora_do_registro_...` |
| Filtro por período | Inclui os dois extremos | `test_RF_22_filtro_de_periodo_...` |
| Fuso da máquina em UTC+14, UTC, UTC−11 e UTC−3 | Resultado idêntico | `test_RF_24_vencimento_e_o_mesmo_em_fusos_extremos` |

O teste de fuso muda `TZ` e chama `time.tzset()` dentro do processo, e restaura o valor ao final. Não roda em Windows, que não tem `tzset`; lá fica pulado. A execução da suíte inteira com `TZ=Pacific/Kiritimati` foi registrada em [portabilidade](portabilidade.md) (P-08).

## 3. Pagamento com data futura (OPEN-17)

A baseline não diz se a data do pagamento pode ser passada ou futura (OPEN-17, aberta; sugestão: aceitar passada e recusar futura). O código **aceita qualquer data**. Os testes `test_OPEN_17_provisorio_...` caracterizam esse comportamento atual sem decidi-lo; quando a equipe decidir, o teste de data futura muda para exigir a recusa, no mesmo PR da decisão. Verificado também que a data do pagamento não decide o estado do título: pagamento parcial datado depois do vencimento não vence o título (RF-24 manda).

## 4. Fuso horário de referência

A baseline não define o fuso do sistema. Hoje isso não causa erro, porque **o relógio da máquina nunca é lido**: a data chega de fora, como `date` sem fuso. O risco aparece quando a interface e o agendador (Specs 001, 008 e 010) precisarem calcular "hoje" e o horário de envio da régua (RNF-12). Registrado como **OPEN-23**, com sugestão de America/Sao_Paulo para a data de referência e UTC para os horários guardados. O `Relogio.agora()` devolve hoje `datetime` sem fuso; o adaptador real precisará escolher entre sem fuso e com fuso.

## 5. Pendente

| Caso | Depende de |
|---|---|
| Atraso de obrigação e escalonamento (RB-16) | Spec 010 |
| Horário de envio da régua perto da meia-noite e na troca de horário | Specs 008 e 010; OPEN-23 |
| Filtro por período com outra data que não o vencimento | OPEN-19 |
