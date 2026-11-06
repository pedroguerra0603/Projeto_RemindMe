# Spec 019 — Troca da própria senha

## 1. Identificação

| | |
|---|---|
| **ID** | 019 |
| **Nome** | Troca da própria senha |
| **Objetivo** | Permitir que cada usuário ativo e autenticado substitua a própria senha, informando a atual, sem depender do Administrador. |
| **Valor entregue** | O Operador Financeiro que recebeu a senha provisória do Administrador (OPEN-35) passa a usar uma senha que só ele conhece. Quem desconfia que a senha vazou troca-a e encerra, na hora, as sessões abertas em outros navegadores. |
| **Situação** | Proposta |
| **Aprovada por** | *(nomes e data)* |

## 2. Rastreabilidade

| Tipo | Itens |
|---|---|
| RF | RF-95, RF-96 (novos); RF-04 (responsável na auditoria); preserva RF-66 |
| RB | Nenhuma nova |
| RNF | RNF-01, RNF-04, RNF-09, RNF-14 |
| UC | [UC-16](../../docs/casos-de-uso/UC-16-trocar-a-propria-senha.md) (novo) |
| Entidades | `Usuario` (hash da senha); sessão, registro técnico da Spec 002 |
| Drivers e ADRs | DA-02, DA-03, DA-04; ADR-004, ADR-006, ADR-007 |
| Depende de | Specs 001, 002 e 017. Decisões OPEN-33 (`scrypt`), OPEN-34 (sem bloqueio por tentativas), OPEN-44 (tamanho da senha) e OPEN-58, tomada em 2026-11-06 por Bernardo Sanches. |

## 3. Escopo

### Incluído

- Troca da própria senha por qualquer usuário ativo com sessão válida, de qualquer perfil, informando a senha atual, a nova senha e a confirmação da nova.
- Regras da nova senha: as de OPEN-44 (de 8 a 256 caracteres, sem regra de composição), igual à confirmação e diferente da atual.
- Encerramento das demais sessões do usuário, mantendo a sessão em que a troca foi feita.
- Registro da troca na auditoria, sem a senha.
- Tela "Trocar senha", com link no topo de todas as páginas, para todos os perfis.

### Fora do escopo

| Item | Motivo |
|---|---|
| Redefinição da senha de outro usuário pelo Administrador | OPEN-59, aberta. Decidido em 2026-11-06 que fica fora desta spec. |
| Troca obrigatória da senha provisória no primeiro acesso | OPEN-60, aberta. Decidido em 2026-11-06 que fica fora desta spec. |
| Recuperação de senha esquecida | Exige um canal para falar com o usuário (ADR-002), que ainda não existe. |
| Bloqueio após tentativas erradas da senha atual | Como no login, fora do escopo (OPEN-34). |
| Histórico de senhas e expiração periódica | Não há requisito. O NIST SP 800-63B desaconselha a troca periódica obrigatória. |
| Linha na matriz de permissões | A troca não é uma permissão de perfil; ver "Acesso", na seção 4. |

## 4. Comportamento

### Pré-condições

- O usuário está ativo e tem sessão válida (Spec 002).
- Nenhuma permissão da matriz é exigida (ver "Acesso").

### Fluxo principal: troca da senha provisória

1. O usuário abre "Trocar senha", pelo link no topo da página.
2. O usuário informa a senha atual, a nova senha e a confirmação da nova.
3. O sistema confere a sessão (RNF-01).
4. O sistema confere a senha atual contra o hash guardado.
5. O sistema valida a nova senha (OPEN-44), a confirmação e a diferença em relação à atual.
6. O sistema guarda o hash `scrypt` da nova senha, com salt novo (RNF-04, OPEN-33).
7. O sistema encerra as demais sessões do usuário e mantém a sessão em uso.
8. O sistema registra a troca na auditoria, com o usuário como responsável e sem a senha (RF-04).
9. O usuário volta ao painel, com o aviso de que a senha foi alterada e de que as outras sessões foram encerradas.

Os passos 6 a 8 acontecem numa só transação (RNF-09).

### Fluxos alternativos

- **A1 — Sem outras sessões.** No passo 7 não há sessão a encerrar; o restante do fluxo não muda.
- **A2 — Entrada seguinte.** A partir da troca, a entrada aceita só a nova senha. A antiga é recusada com a mensagem genérica de RF-66.

### Exceções

- **E1 — Senha atual ausente ou incorreta.** A troca é recusada, com o motivo no campo da senha atual (RF-96). Nem a senha nem as sessões mudam. Como o usuário já está identificado pela sessão, a mensagem indica o campo; a mensagem genérica de RF-66 vale para a tela de entrada.
- **E2 — Nova senha inválida.** Ausente, com menos de 8 ou mais de 256 caracteres (OPEN-44): recusada, com o motivo no campo da nova senha.
- **E3 — Confirmação diferente da nova senha.** Recusada, com o motivo no campo da confirmação.
- **E4 — Nova senha igual à atual.** Recusada, com o motivo no campo da nova senha.
- **E5 — Sem sessão válida.** Sessão ausente, desconhecida, vencida ou de usuário inativo: recusada (RNF-01). A interface volta à tela de entrada.
- **E6 — Falha durante a troca**, por exemplo na gravação da auditoria. Nenhuma alteração permanece: a senha antiga continua valendo e as sessões continuam abertas (RNF-09).
- **E7 — Formulário sem a proteção da sessão.** Recusado, como todo formulário da interface (Spec 017).

Toda recusa indica, de uma vez, todos os campos com problema (RNF-14), não altera nenhum dado e não devolve à página as senhas digitadas.

### Acesso

A troca da própria senha não é uma linha da matriz de permissões da Spec 002. Como entrar e sair do sistema, ela age só sobre a conta do usuário identificado pela sessão e vale para todo usuário ativo, de qualquer perfil (OPEN-58). Retirá-la de um perfil deixaria o usuário preso à senha provisória, que o Administrador conhece.

É uma exceção explícita ao INV-2 da Spec 002, do mesmo tipo de entrar, sair e consultar a sessão. A exigência de sessão válida de usuário ativo continua (RNF-01), verificada no mesmo ponto único (Spec 002, INV-5).

## 5. Invariantes

| ID | Invariante | Origem |
|---|---|---|
| INV-1 | A senha, atual ou nova, nunca é armazenada, auditada nem devolvida em claro, inclusive na página de recusa. | RNF-04; Spec 002, INV-3 |
| INV-2 | A senha só muda com a senha atual correta, informada na mesma operação. | RF-95, RF-96 |
| INV-3 | Depois da troca, nenhuma sessão do usuário continua válida, exceto aquela em que a troca foi feita. As sessões de outros usuários não mudam. | RF-95, OPEN-58 |
| INV-4 | O novo hash, o encerramento das outras sessões e o registro de auditoria são gravados na mesma transação: tudo ou nada. | RNF-09 |
| INV-5 | Um usuário só troca a própria senha: a operação identifica o usuário pela sessão e não recebe identificador de usuário. | OPEN-58, OPEN-59 |

## 6. Critérios de aceitação

| ID | Dado | Quando | Então | Cobre |
|---|---|---|---|---|
| CA-01 | um Operador Financeiro com sessão aberta e a senha "senha-antiga-1" | ele troca para "senha-nova-123", com a confirmação igual | a troca é aceita; a entrada seguinte com a senha nova abre sessão, e com a antiga é recusada com a mensagem genérica | RF-95, A2, RF-66 |
| CA-02 | um usuário com sessão aberta e outra sessão em outro navegador | ele informa a senha atual errada, com nova senha e confirmação válidas | a troca é recusada com o motivo no campo da senha atual; a senha antiga continua entrando, e as duas sessões continuam válidas | RF-96, E1, INV-2 |
| CA-03 | um usuário com sessão aberta | ele informa uma nova senha de 7 caracteres e, depois, uma de 257 | as duas trocas são recusadas com o motivo no campo da nova senha | E2, OPEN-44 |
| CA-04 | um usuário com sessão aberta | a confirmação é diferente da nova senha | a troca é recusada com o motivo no campo da confirmação | E3 |
| CA-05 | um usuário com sessão aberta | a nova senha é igual à atual | a troca é recusada com o motivo no campo da nova senha | E4 |
| CA-06 | um usuário com sessão aberta | ele envia a troca com os três campos vazios | a troca é recusada, indicando os três campos de uma vez | RNF-14 |
| CA-07 | um usuário com três sessões abertas (A, B e C) | ele troca a senha pela sessão A | A continua válida; B e C são recusadas na operação seguinte | RF-95, INV-3 |
| CA-08 | sessões abertas de dois usuários | um deles troca a senha | as sessões do outro usuário continuam válidas | INV-3, INV-5 |
| CA-09 | nenhuma sessão, uma sessão desconhecida, uma vencida e uma de usuário inativo | a troca é solicitada em cada caso | as quatro são recusadas, e nenhuma senha muda | RNF-01, E5 |
| CA-10 | um usuário que troca a senha | o armazenamento e a auditoria são inspecionados | o usuário tem novo hash `scrypt`, com salt diferente do anterior; a auditoria tem um registro "senha: alterada", com o usuário como responsável; nenhum registro contém a senha antiga nem a nova | RNF-04, RF-04, INV-1 |
| CA-11 | uma falha injetada na gravação da auditoria | o usuário troca a senha | a operação falha; a senha antiga continua entrando, e as outras sessões continuam abertas | RNF-09, E6, INV-4 |
| CA-12 | um usuário de cada perfil, e um Contador cujo perfil teve retiradas todas as permissões configuráveis | cada um troca a própria senha | todas as trocas são aceitas | Acesso, OPEN-58 |
| CA-13 | a interface web, sem sessão | a página "Trocar senha" é pedida, ou o formulário é enviado | a resposta leva à tela de entrada, e nada muda | RNF-01, E5 |
| CA-14 | um usuário de cada perfil na interface web | ele abre o painel | o topo tem o link "Trocar senha" | Escopo |
| CA-15 | um usuário na interface web | ele envia o formulário com erros | a página volta com status 400, com o motivo em cada campo; nenhum campo de senha vem preenchido, e o HTML não contém as senhas digitadas | RNF-14, INV-1 |
| CA-16 | um usuário na interface web | ele envia o formulário sem a proteção da sessão | o envio é recusado, e a senha não muda | E7 |
| CA-17 | um usuário com sessões em dois navegadores | ele troca a senha pela interface em um deles | é levado ao painel com o aviso da troca; o outro navegador, na página seguinte, volta à tela de entrada com o aviso de sessão encerrada | RF-95, INV-3 |
| CA-18 | o sistema em execução, num navegador real | o usuário entra, troca a senha pela tela, sai e tenta entrar com a senha antiga e com a nova | a antiga é recusada e a nova abre o painel; um segundo navegador, com sessão aberta antes da troca, é levado à tela de entrada | RF-95, RF-96, ponta a ponta |
| CA-19 | o banco SQLite | o usuário troca a senha e a aplicação é reaberta sobre o mesmo arquivo | a senha nova continua valendo, a antiga não, e as sessões encerradas não voltam | ADR-007, RF-95 |

Os testes automatizados levam no nome o identificador do critério, por exemplo `test_CA_07_outras_sessoes_sao_encerradas`.

## 7. Questões em aberto

| ID | Questão | Bloqueia a implementação? |
|---|---|---|
| OPEN-58 | Cada usuário pode trocar a própria senha? | Não: decidida em 2026-11-06 por Bernardo Sanches. |
| OPEN-59 | O Administrador pode redefinir a senha de outro usuário? | Não: fica fora desta spec. |
| OPEN-60 | A senha provisória deve ser trocada no primeiro acesso? | Não: fica fora desta spec. |

## 8. Verificação

A preencher depois da implementação.
