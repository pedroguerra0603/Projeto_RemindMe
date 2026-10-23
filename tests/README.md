# tests

Testes do RemindMe, com `unittest` da biblioteca padrão. Para executar, na raiz do repositório:

```
python3 -m unittest discover -s tests -t .
```

A estratégia está em [`docs/testes.md`](../docs/testes.md). Cada teste leva o identificador da regra ou do critério no nome. Como Python não aceita hífen em identificador, `RB-23_recusa_pagamento_maior_que_o_saldo` vira `test_RB_23_recusa_pagamento_maior_que_o_saldo`.

| Pasta | Nível |
|---|---|
| `dominio/` | Unidade de domínio: regras e transições, sem banco e sem interface |
| `aplicacao/` | Critérios de aceite de cada spec, com repositórios em memória |
| `infraestrutura/` | Unidade das implementações em memória e do SQLite: repositórios, auditoria, unidade de trabalho, relógio |
| `integracao/` | Serviço com unidade de trabalho, repositórios, auditoria, relógio e clientes; contrato do repositório de títulos, a reaplicar quando houver banco (OPEN-02) |
| `arquitetura/` | Regra de dependência entre camadas (ADR-001) e uso só da biblioteca padrão |
| `desempenho/` | Limite de tempo de RNF-11 e o script de métricas de `docs/qualidade/eficiencia.md` |
| `apresentacao/` | Testes de API da interface web, chamando a aplicação WSGI no próprio processo (Spec 017, OPEN-29) |
| `ponta_a_ponta/` | Fluxo crítico no navegador, com Playwright; opcional e pulado quando o Playwright não está instalado |

`apoio.py` abre sessões direto nos dublês, para os testes que não tratam de login (Spec 002), e define o custo baixo do `scrypt` usado na suíte. O contrato do repositório de títulos (`integracao/`) é reaplicado ao SQLite em `infraestrutura/test_sqlite.py`.
