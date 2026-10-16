# Avaliação da Funcionalidade — RemindMe

Issue #62. Verifica se as funcionalidades implementadas atendem aos requisitos e se os resultados produzidos estão corretos. Usa os critérios de adequação funcional definidos em [critérios de qualidade](criterios.md), seção 2.1.

- **Data:** 2026-10-16.
- **Objeto avaliado:** a [Spec 006](../../.specify/specs/006-titulo-pagamento-baixa-e-estorno.md), única implementada. Base: `main` em `4b4ef09`.
- **Referência:** ISO/IEC 25010, adequação funcional (completude, correção e pertinência). Inclui as subcaracterísticas da funcionalidade na ISO/IEC 9126: adequação, acurácia, interoperabilidade, segurança de acesso e conformidade.
- **Execução:** `python3 -m unittest discover -s tests -t .` → 132 testes, OK, em Python 3.13.16. Mais dez cenários independentes da suíte, pelo serviço de aplicação (seção 3.2).

## 1. Resumo

| Subcaracterística | Medida | Resultado | Avaliação |
|---|---|---|---|
| Completude funcional | RF da Spec 006 implementados | 11 de 11 | Atende |
| Correção funcional | Critérios de aceite passando | 24 de 24 | Atende |
| Correção funcional | Cenários independentes com o resultado esperado pela spec | 7 de 10; 3 dependem de decisão ou de spec futura | Atende com ressalvas |
| Acurácia (9126) | Cálculos de saldo exatos ao centavo | 4 de 4 cenários | Atende |
| Pertinência funcional | Comportamento além da spec | Nenhum que altere dados | Atende |
| Segurança de acesso (9126) | Restrições de perfil da spec aplicadas | RB-02 e OPEN-16 aplicadas; RB-03 ainda não | Parcial, fora do escopo da spec |
| Interoperabilidade (9126) | — | Não há integração na Spec 006 | Não se aplica |
| Conformidade (9126) | Termos do glossário e identificadores no código | Conforme | Atende |

**Conclusão.** A Spec 006 atende à adequação funcional: todos os requisitos do escopo estão implementados, e os resultados estão corretos ao centavo. As ressalvas não são defeitos do código em relação à spec. São três pontos em que o resultado depende de decisão ou de spec futura: o estado depois do estorno de título não Baixado (OPEN-23), o Contador ainda conseguir cadastrar e pagar (RB-03, Spec 002) e o título só passar a Vencido quando a verificação é chamada (Spec 008).

## 2. Completude funcional

Cada RF do escopo da Spec 006, com o comportamento esperado e onde está implementado. Os testes de cada linha estão na [rastreabilidade](../rastreabilidade.md), seção 3.

| RF | Comportamento exigido | Implementado | Observação |
|---|---|---|---|
| RF-20 | Cadastro manual com cliente, valor e vencimento válidos cria título Aberto | Sim | "Usuário autorizado" depende da Spec 002 |
| RF-21 | Armazena valor, vencimento, cliente, origem, condição de pagamento e estado | Sim | — |
| RF-22 | Filtra por cliente, vencimento, estado e período | Sim | "Período" filtra o vencimento (OPEN-19) |
| RF-23 | Sinaliza título Aberto próximo do vencimento | Sim | A antecedência é parâmetro da consulta (OPEN-21) |
| RF-24 | Título Aberto com vencimento passado e saldo maior que zero passa a Vencido | Sim | Só quando a verificação é chamada; o disparo periódico é da Spec 008 |
| RF-25 | Associa o pagamento ao título e reduz o saldo | Sim | "Usuário autorizado" depende da Spec 002 |
| RF-26 | Saldo zero muda o estado para Baixado | Sim | — |
| RF-27 | Pagamento parcial mantém o estado e apresenta o saldo restante | Sim | — |
| RF-30 | Estorno pelo Dono anula o pagamento, restaura o saldo e devolve o título a Aberto ou Vencido | Sim | Estado depois do estorno de título não Baixado em aberto (OPEN-23) |
| RF-31 | Cancelamento ou estorno sem motivo é recusado | Sim | "Alteração de valor" não tem operação (OPEN-22) |
| RF-68 | Pagamento maior que o saldo, ou menor ou igual a zero, é recusado | Sim | — |

**Medida:** 11 de 11 RF implementados (100%). As regras RB-02, RB-22 e RB-23 estão implementadas por inteiro, e RB-01 e RB-21 dentro do escopo da spec: auditoria só de título e pagamento, e sem o estado Em Renegociação.

## 3. Correção funcional

### 3.1 Critérios de aceite

Os 24 critérios de aceite passam, com 29 testes em `tests/aplicacao/test_spec_006_aceite.py`. Os fluxos A1 a A6, as exceções E1 a E8 e as invariantes INV-1 a INV-8 estão cobertos. Detalhe por critério na [matriz](matriz-criterios-de-aceite.md).

### 3.2 Cenários independentes

Para não depender só dos testes escritos junto com o código, a avaliação executou dez cenários pelo `ServicoTitulos`, com repositórios em memória. Cada cenário compara o resultado com o que a spec e a baseline dizem. Os cenários C-01 a C-04 verificam a acurácia, C-05 e C-06 o vencimento e a consulta, C-07 e C-08 a restrição de perfil, C-09 o estorno e C-10 a auditoria.

Resultado da execução, com data de referência 2026-10-16:

```
C-01 3 pagamentos de 33,33 sobre 100,00              -> [Decimal('66.67'), Decimal('33.34'), Decimal('0.01')]
C-02 pagamento de 0,02 sobre saldo 0,01              -> recusado: O valor do pagamento é maior que o saldo de 0.01 (RB-23).
C-03 pagamento de 0,01 baixa                         -> (Decimal('0.00'), 'Baixado')
C-04 valor de 16 digitos, pagamento parcial          -> 98765432109876.53
C-05 verificacao de vencimentos                      -> 1
C-06 consulta c1 Vencido                             -> [(Decimal('50.00'), 'Vencido')]
C-07 Contador cadastra titulo (RB-03)                -> Aberto
C-08 Contador registra pagamento (RB-03)             -> 49.00
C-09 estorno parcial, Aberto com vencimento passado  -> (Decimal('100.00'), 'Aberto')
C-10 registros de auditoria gravados                 -> 15
```

| Cenário | Esperado | Obtido | Avaliação |
|---|---|---|---|
| C-01 | Saldos 66,67, 33,34 e 0,01: sem perda de centavo (INV-1) | Igual | Conforme |
| C-02 | Recusa, com o saldo disponível no motivo (RB-23, RNF-14) | Igual | Conforme |
| C-03 | Saldo 0,00 e título Baixado (RB-22) | Igual | Conforme |
| C-04 | Saldo exato com 16 dígitos | Igual | Conforme |
| C-05 | Um título passa a Vencido (RF-24) | Igual | Conforme |
| C-06 | Só o título Vencido do cliente c1 (RF-22) | Igual | Conforme |
| C-07 | Contador não cria título (RB-03) | Título criado | Ressalva: depende da Spec 002; já registrado na seção 8 da Spec 006 (DV-11) |
| C-08 | Contador não registra pagamento (RB-03) | Pagamento registrado | Ressalva: idem |
| C-09 | Pela tabela de estados, Aberto. Pela redação de A4, Vencido | Aberto | Ressalva: spec e tabela de estados discordam (DV-01, OPEN-23) |
| C-10 | Um registro por operação e por mudança de estado (RB-01) | 15 registros | Conforme: 13 operações aceitas (5 cadastros, 7 pagamentos e 1 estorno) e 2 mudanças de estado (Baixado em C-03, Vencido em C-05). A recusa de C-02 não gerou registro, e o estorno de C-09 não mudou o estado |

**Medida:** 7 de 10 cenários conforme. Os 3 restantes não são defeitos do código em relação à spec: dependem da Spec 002 (C-07 e C-08) ou de uma decisão sobre a redação da spec (C-09).

### 3.3 Acurácia

| Verificação | Resultado |
|---|---|
| Valores monetários em `Decimal` em todo o domínio, sem `float` | Conforme. `_exigir_decimal` recusa `float`, texto, `None`, `NaN` e infinito (D-01 a D-04) |
| Pagamentos fracionados somam o valor exato | Conforme (C-01, C-03; `test_INV_1_saldo_e_exato_em_centavos`) |
| Valores grandes sem perda | Conforme (C-04; `test_E1_valor_alto_nao_perde_precisao`). O contexto padrão do `Decimal` tem 28 dígitos significativos, muito acima de qualquer valor de uma pequena empresa |
| Precisão de duas casas | Não garantida: R$ 0,001 é aceito. Aguarda OPEN-20 |

## 4. Pertinência funcional

O código não tem comportamento além da spec que altere dados. Os pontos que vão além do texto da spec são consequências necessárias ou estruturas sem efeito:

| Item | Avaliação |
|---|---|
| Recusa de título ou pagamento inexistente | Consequência necessária das operações; testada em `test_titulo_inexistente_e_recusado_em_toda_operacao` e `test_E5_estorno_de_pagamento_inexistente_e_recusado` |
| `Perfil.ADMINISTRADOR` | Segue o glossário. Nenhuma regra da Spec 006 o usa. A existência do perfil está em aberto (OPEN-10, DV-04) |
| `VisaoTitulo` | Estrutura de leitura de A6. Não altera dados |

## 5. Segurança de acesso e conformidade

| Item | Resultado |
|---|---|
| RB-02: só o Dono estorna | Conforme: os outros quatro perfis são recusados (`test_RB_02_nenhum_outro_perfil_estorna`) |
| OPEN-16: só o Dono cancela | Conforme: os outros quatro perfis são recusados (`test_OPEN_16_nenhum_outro_perfil_cancela`) |
| RB-03: Contador só consulta | Não aplicada (C-07, C-08). A autorização geral é da Spec 002, e a Spec 006 declara isso na seção 8 |
| Glossário | O código usa título, pagamento, estorno, saldo, vencimento, condição de pagamento, cliente e perfil. Nenhum termo da lista "Termos que não usamos" aparece em `src/` |
| Identificadores | Docstrings citam RF, RB e OPEN; testes de regra e critério levam o identificador no nome, com a exceção registrada em DV-14 |

## 6. Recomendações

| Recomendação | Depende de |
|---|---|
| Decidir OPEN-23 e ajustar A4 ou o código, com teste para o título Aberto com vencimento passado | Equipe |
| Aplicar RB-03 ao cadastro e ao pagamento e repetir C-07 e C-08 | Spec 002 |
| Cobrir na Spec 008 o título já vencido que ainda não passou pela verificação (DV-15) | Spec 008 |
| Decidir a precisão monetária e repetir a seção 3.3 | OPEN-20 |
| Repetir esta avaliação a cada nova spec aprovada | — |

## Anexo — script dos cenários

Executado na raiz do repositório com `python3 -I avaliar_funcionalidade.py`. Não faz parte da suíte, porque C-07 a C-09 registram o comportamento atual em pontos que ainda dependem de decisão.

```python
import sys
sys.path.insert(0, "src")
from datetime import date, datetime, timedelta
from decimal import Decimal as D
from remindme.aplicacao.servico_titulos import ServicoTitulos, FiltroTitulos
from remindme.dominio.erros import OperacaoRecusada
from remindme.dominio.titulo import EstadoTitulo
from remindme.dominio.usuario import Usuario, Perfil
from remindme.infraestrutura.memoria import *

HOJE = date(2026, 10, 16)
rep, aud = RepositorioTitulosEmMemoria(), AuditoriaEmMemoria()
s = ServicoTitulos(UnidadeDeTrabalhoEmMemoria(rep, aud), ClientesEmMemoria({"c1", "c2"}), RelogioFixo(datetime(2026, 10, 16, 9)))
dono = Usuario("u1", "Carla", Perfil.DONO)
op = Usuario("u2", "Diego", Perfil.OPERADOR_FINANCEIRO)
cont = Usuario("u3", "Helena", Perfil.CONTADOR)

def caso(nome, f):
    try:
        print(f"{nome:<52} -> {f()}")
    except OperacaoRecusada as e:
        print(f"{nome:<52} -> recusado: {e.motivo}")

t = s.cadastrar_titulo(op, "c1", D("100.00"), HOJE + timedelta(days=10))
caso("C-01 3 pagamentos de 33,33 sobre 100,00", lambda: [s.registrar_pagamento(op, t.id, D("33.33"), HOJE).saldo for _ in range(3)])
caso("C-02 pagamento de 0,02 sobre saldo 0,01", lambda: s.registrar_pagamento(op, t.id, D("0.02"), HOJE).saldo)
caso("C-03 pagamento de 0,01 baixa", lambda: (lambda x: (x.saldo, x.estado.value))(s.registrar_pagamento(op, t.id, D("0.01"), HOJE)))
g = s.cadastrar_titulo(op, "c2", D("98765432109876.54"), HOJE)
caso("C-04 valor de 16 digitos, pagamento parcial", lambda: s.registrar_pagamento(op, g.id, D("0.01"), HOJE).saldo)
v = s.cadastrar_titulo(op, "c1", D("50.00"), HOJE - timedelta(days=1))
caso("C-05 verificacao de vencimentos", lambda: len(s.verificar_vencimentos(dono, HOJE)))
caso("C-06 consulta c1 Vencido", lambda: [(x.valor, x.estado.value) for x in s.consultar_titulos(FiltroTitulos("c1", EstadoTitulo.VENCIDO), HOJE, 5)])
caso("C-07 Contador cadastra titulo (RB-03)", lambda: s.cadastrar_titulo(cont, "c1", D("10.00"), HOJE).estado.value)
caso("C-08 Contador registra pagamento (RB-03)", lambda: s.registrar_pagamento(cont, v.id, D("1.00"), HOJE).saldo)
a = s.cadastrar_titulo(op, "c1", D("100.00"), HOJE - timedelta(days=3))
p = s.registrar_pagamento(op, a.id, D("40.00"), HOJE)
pid = p.pagamentos[-1].id
caso("C-09 estorno parcial, Aberto com vencimento passado", lambda: (lambda x: (x.saldo, x.estado.value))(s.estornar_pagamento(dono, a.id, pid, "cheque devolvido", HOJE)))
caso("C-10 registros de auditoria gravados", lambda: len(aud.registros))
```
