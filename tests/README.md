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
