# Plano técnico — Spec 002

Spec: [002 — Autenticação e autorização por perfil](../specs/002-autenticacao-e-autorizacao.md).

## Tecnologia

- Python 3.11, somente a biblioteca padrão (OPEN-01). Hash de senha por `hashlib.scrypt` (OPEN-33), identificadores por `secrets`.
- Testes com `unittest`, sem interface (RNF-03). A tela de login é da Spec 017.

## Organização

| Camada | Módulo | Conteúdo |
|---|---|---|
| Domínio | `dominio/usuario.py` | `Usuario` com e-mail e situação; validação do cadastro (E7), troca de perfil (A2) e inativação (A3) |
| Domínio | `dominio/operacoes.py` | `Operacao`: as linhas da matriz e a consulta de clientes (OPEN-42) |
| Domínio | `dominio/regras.py` | Células fixadas por regra: RB-02, RB-03, RB-15, RB-26 e OPEN-16, num único ponto (RNF-19) |
| Domínio | `dominio/permissoes.py` | `MatrizPermissoes`: matriz inicial, `exigir` (RF-67), `conceder` e `retirar` (A4, E5, OPEN-45) |
| Domínio | `dominio/erros.py` | `OperacaoRecusada` com os campos inválidos (RNF-14) e `OperacaoNegada` |
| Aplicação | `aplicacao/acesso.py` | `Sessao` guardada pelo resumo do identificador; `Autorizacao`, o único ponto de verificação (INV-5) |
| Aplicação | `aplicacao/execucao.py` | `Execucao`: transação, autorização e erro não tratado de toda operação; substitui a classe `Auditoria` da Spec 001 |
| Aplicação | `aplicacao/senhas.py` | `CifradorScrypt` e a senha mínima (OPEN-44) |
| Aplicação | `aplicacao/servico_acesso.py` | Entrar, sair, sessão ativa, usuários e permissões; primeiro Administrador (OPEN-39) |
| Aplicação | `aplicacao/servico_titulos.py` | As operações da Spec 006 passam a receber a sessão |
| Infraestrutura | `infraestrutura/memoria.py` | Dublês de usuários, sessões e permissões; unidade de trabalho com bloco aninhado |

## Decisões locais

- **Sessão no servidor (OPEN-03).** O navegador recebe um identificador aleatório de 32 bytes; o armazenamento guarda só o resumo SHA-256 dele, a data de abertura, o vencimento (8 horas, OPEN-43) e o token de proteção dos formulários.
- **Toda operação recebe a sessão.** Os serviços não aceitam um objeto `Usuario` vindo de fora: a sessão é conferida, o usuário é relido do armazenamento, e a permissão vem do perfil atual e da matriz atual. Assim valem A2, A3 e A4 sem novo login (CA-12, CA-14, CA-15).
- **Autorização antes do domínio.** `Execucao.operacao` abre a transação e chama `Autorizacao.exigir` antes de qualquer leitura do título, por isso a recusa por perfil não revela se o título existe.
- **Consultas também passam pela autorização.** Consultar títulos e usuários exige a permissão da matriz; uma consulta não grava auditoria.
- **Entrar e sair são auditados (OPEN-47).** O registro afetado é o usuário, com o campo `sessão`, sem a senha e sem o identificador.
- **E1 sem atalho.** O e-mail inexistente também passa pela conferência de um hash, para que o tempo de resposta não revele quais e-mails existem.
- **Verificação automática de vencimento** ganhou método próprio, `verificar_vencimentos_automaticamente`, para o agendador. A versão com sessão exige a permissão "Verificar vencimentos".
- **Custo do `scrypt`.** O padrão é n = 2^17, r = 8, p = 1, o mínimo da OWASP. Os testes usam n = 2^4.
- **Testes.** `tests/apoio.py` abre sessões direto no dublê para os testes que não tratam de login. Os testes da Spec 002 entram pelo login de verdade.

## Tarefas

Em [`../tasks/002-tarefas.md`](../tasks/002-tarefas.md).
