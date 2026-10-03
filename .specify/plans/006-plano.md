# Plano técnico — Spec 006

Spec: [006 — Título: cadastro manual, pagamento, baixa e estorno](../specs/006-titulo-pagamento-baixa-e-estorno.md). Issue: #55.

## Tecnologia

- Python 3.11, somente a biblioteca padrão (OPEN-01, decidido em 2026-10-03: escolha livre, com o domínio isolado do framework).
- Testes com `unittest`, da biblioteca padrão. Nenhuma dependência a instalar.
- Framework web e banco de dados não entram nesta spec: ela não tem interface e não tem persistência real (OPEN-02 continua aberta).

## Organização

| Camada | Módulo | Conteúdo |
|---|---|---|
| Domínio | `src/remindme/dominio/titulo.py` | `Titulo`, `Pagamento`, `EstadoTitulo`; RB-21, RB-22, RB-23 |
| Domínio | `src/remindme/dominio/regras.py` | RB-02 e OPEN-16: quem estorna e quem cancela |
| Domínio | `src/remindme/dominio/usuario.py` | `Usuario` e `Perfil` (somente o necessário para RB-02) |
| Domínio | `src/remindme/dominio/auditoria.py` | `RegistroAuditoria` |
| Domínio | `src/remindme/dominio/erros.py` | `OperacaoRecusada`, com o motivo |
| Aplicação | `src/remindme/aplicacao/servico_titulos.py` | Um método por operação da spec; verifica permissão, abre a transação, chama o domínio, grava a auditoria |
| Aplicação | `src/remindme/aplicacao/portas.py` | Interfaces: repositório de títulos, consulta de clientes, auditoria, unidade de trabalho, relógio |
| Infraestrutura | `src/remindme/infraestrutura/memoria.py` | Implementações em memória, com transação por cópia e restauração |

O domínio não importa nada de aplicação nem de infraestrutura (ADR-001). Datas de referência são passadas ao domínio; o relógio fica atrás de uma interface.

## Decisões locais

- Valores monetários em `Decimal`, com duas casas.
- Atomicidade (RNF-09, CA-23): a unidade de trabalho em memória guarda uma cópia do estado ao abrir a transação e a restaura se qualquer passo, inclusive a auditoria, falhar.
- Auditoria mínima: a Spec 001 ainda não existe. Esta spec grava o registro de auditoria por uma interface que a Spec 001 vai implementar de verdade.
- Nome dos testes: Python não aceita hífen em identificador. `RB-23_recusa...` vira `test_RB_23_recusa...`, e `CA-06` vira `test_CA_06_...`.

## Tarefas

1. Domínio: `Titulo`, `Pagamento` e transições de estado, com testes por RB.
2. Regras de perfil: RB-02 e cancelamento pelo Dono.
3. Aplicação: serviço de títulos, com auditoria e transação.
4. Consulta com filtros e sinalização de próximo do vencimento.
5. Testes de aceite CA-01 a CA-24.
6. Registrar o resultado na seção 8 da spec.
