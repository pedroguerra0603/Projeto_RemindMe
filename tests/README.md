# tests

Testes do RemindMe, com `unittest` da biblioteca padrão. Para executar, na raiz do repositório:

```
python3 -m unittest discover -s tests -t .
```

A estratégia está em [`docs/testes.md`](../docs/testes.md). Cada teste leva o identificador da regra ou do critério no nome. Como Python não aceita hífen em identificador, `RB-23_recusa_pagamento_maior_que_o_saldo` vira `test_RB_23_recusa_pagamento_maior_que_o_saldo`.

| Pasta | Nível |
|---|---|
| `dominio/` | Unidade de domínio: regras, transições e registro de auditoria, sem banco e sem interface |
| `aplicacao/` | Critérios de aceite de cada spec, com repositórios em memória (`test_spec_001_aceite.py`, `test_spec_006_aceite.py`) |
| `infraestrutura/` | Unidade das implementações em memória: repositório, auditoria, registro de erros, unidade de trabalho, relógio |
| `integracao/` | Serviço com unidade de trabalho, repositórios, auditoria, relógio e clientes; contrato do repositório de títulos, a reaplicar quando houver banco (OPEN-02) |
| `arquitetura/` | Regra de dependência entre camadas (ADR-001) e uso só da biblioteca padrão |
| `desempenho/` | Limite de tempo de RNF-11 e o script de métricas de `docs/qualidade/eficiencia.md` |

Um teste da Spec 001 (`test_CA_13_RNF_23_suite_inteira_passa_sem_variavel_de_credencial`) roda a suíte inteira em outro processo, com o ambiente reduzido ao mínimo, para provar que ela não depende de credencial (RNF-23). O processo filho é marcado pela variável `REMINDME_CA_13_PROCESSO_FILHO` e não repete esse teste.
