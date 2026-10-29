# Spec 017 — Interface web: acesso, clientes, títulos e auditoria

## 1. Identificação

| | |
|---|---|
| **ID** | 017 |
| **Nome** | Interface web: acesso, clientes, títulos e auditoria |
| **Objetivo** | Permitir que cada perfil use pelo navegador o que as Specs 002, 003, 006 e 013 já garantem, com os dados guardados entre execuções, na máquina de quem apresenta. |
| **Valor entregue** | A Dona, o Operador Financeiro, a Contadora e o Administrador entram no RemindMe, veem no painel o que cabe a cada um e cadastram clientes e títulos, registram, estornam e cancelam, consultam a auditoria e administram usuários, sem tocar no código. |
| **Situação** | **Verificada** — todos os critérios de aceitação passaram (seção 8). |
| **Aprovada por** | João Pedro Silva Guerra, em 2026-10-23, por autorização prévia dada ao agente antes da redação; a revisão do conteúdo fica no PR |

## 2. Rastreabilidade

| Tipo | Itens |
|---|---|
| RF | Telas de RF-01, RF-02, RF-03, RF-20 a RF-23, RF-25 a RF-27, RF-30, RF-31, RF-64, RF-65, RF-66, RF-67; disparo automático de RF-24 |
| RB | Nenhuma regra nova: todas continuam no domínio (RB-01, RB-02, RB-03, RB-21, RB-22, RB-23, RB-30) |
| RNF | RNF-01, RNF-02, RNF-03, RNF-05, RNF-06, RNF-09, RNF-11, RNF-14, RNF-15 e RNF-17 (parte dos títulos), RNF-16, RNF-21, RNF-23 |
| UC | UC-01, UC-02, UC-03, UC-06, UC-12 |
| Entidades | As das Specs 001, 002, 003 e 006 |
| Drivers e ADRs | DA-02, DA-03, DA-04, DA-05, DA-07; DT-06, DT-07; ADR-001, ADR-004, ADR-005, ADR-006, ADR-007 |
| Depende de | Specs 001, 002, 003, 006 e 013. Decisões OPEN-01 (interface), OPEN-12, OPEN-13, OPEN-25, OPEN-26, OPEN-29, OPEN-36, OPEN-37, OPEN-38, OPEN-39, OPEN-43 e OPEN-48. |

## 3. Escopo

### Incluído

- Servidor web local, iniciado com `python3 -m remindme`, com páginas HTML e sem JavaScript (ADR-006).
- Persistência em SQLite, com transação real e auditoria que o banco não deixa alterar nem excluir (ADR-007).
- Relógio do sistema, com a data de referência de America/Sao_Paulo e os horários em UTC (OPEN-26).
- Verificação automática de vencimento na inicialização e a cada hora, no próprio processo (OPEN-13, OPEN-48).
- Telas: entrar e sair; painel do perfil; clientes; títulos, pagamentos, estorno e cancelamento; auditoria; usuários e permissões.
- Pedido de pagamento com identificador, para o envio repetido não registrar dois pagamentos (OPEN-25).
- Proteção dos formulários contra envio de outro site, cabeçalhos de segurança e escape de todo valor exibido.
- HTTPS quando há certificado; sem certificado, só a própria máquina (OPEN-38).
- Comandos para criar o primeiro Administrador (OPEN-39) e preparar dados de demonstração para a apresentação (OPEN-12).
- Testes de API no próprio processo e testes de navegador opcionais (OPEN-29).

### Fora do escopo

| Item | Onde é tratado |
|---|---|
| Orçamentos, régua, renegociação, obrigações, lançamentos, apuração, configuração e CSV | Specs 004, 005, 007 a 012, 014 e 015, cada uma com as suas telas |
| Obrigações e cobranças no painel (RNF-15 e RNF-17 completos) | Spec 016 |
| Acesso do Cliente aos próprios títulos | Spec 009 (OPEN-08) |
| Hospedagem externa | Fora do MVP (OPEN-12) |
| Backup diário (RNF-08) | Operacional, na entrega; o arquivo SQLite se copia pela API de backup |

## 4. Comportamento

### Pré-condições

- Python 3.11 ou mais recente.
- Um Administrador criado na instalação (OPEN-39), ou os dados de demonstração.

### Fluxo principal: registrar um pagamento pelo navegador (UC-06)

1. O usuário abre o sistema e entra com e-mail e senha.
2. O sistema mostra o painel do perfil, com os títulos Vencidos em destaque.
3. O usuário abre um título e informa o valor e a data do pagamento.
4. O sistema registra o pagamento pelo serviço da Spec 006 e mostra o título com o novo saldo e o estado atual.

### Fluxos alternativos

- **A1 — Sem sessão.** Qualquer página, exceto a de entrada e os arquivos de estilo, leva à tela de entrada (RNF-01).
- **A2 — Menu por perfil.** Só aparecem as funcionalidades permitidas (RF-65). A página de uma operação não permitida responde com o motivo (RF-67), e o formulário enviado mesmo assim é negado no servidor (RNF-03).
- **A3 — Entrada inválida.** O formulário volta com os valores digitados e o motivo junto de cada campo (RNF-14).
- **A4 — Pedido repetido.** O mesmo formulário de pagamento enviado duas vezes registra um único pagamento (OPEN-25).
- **A5 — Verificação automática.** Na inicialização e a cada hora, os títulos Abertos com vencimento passado passam a Vencido, com registro de operação automática (OPEN-13, OPEN-48).
- **A6 — Sair.** A sessão termina, e o navegador volta à tela de entrada.
- **A7 — Reinício.** O que foi gravado continua lá depois de reiniciar a aplicação.
- **A8 — Demonstração.** Um comando cria um banco novo com um usuário de cada perfil, exceto Cliente, clientes e títulos em todos os estados, e mostra a senha no terminal; ela não fica em arquivo. Se a demonstração já existir, o mesmo comando a reaproveita sem apagar nada (e recusa, sem apagar, uma senha que não confere); `--substituir` recria tudo. Se a porta estiver ocupada, o servidor usa a seguinte livre e avisa. O endereço mostrado é `http://127.0.0.1:<porta>`, e o navegador abre sozinho. Guia em [`docs/apresentacao.md`](../../docs/apresentacao.md).

### Exceções

- **E1 — Formulário sem a proteção da sessão.** O envio é recusado, e nada é alterado.
- **E2 — Erro não tratado.** A página de erro mostra o identificador de correlação, sem detalhes internos, e o erro é registrado (RNF-21).
- **E3 — Servidor na rede sem certificado.** O servidor não inicia e explica o motivo (OPEN-38).
- **E4 — Página inexistente.** A resposta é "página não encontrada".

## 5. Invariantes

| ID | Invariante | Origem |
|---|---|---|
| INV-1 | Nenhuma regra de negócio ou de permissão fica na apresentação: toda operação passa pelos serviços da aplicação. | ADR-001, DT-06 |
| INV-2 | Toda página com dados exige sessão válida. | RNF-01 |
| INV-3 | Todo formulário que altera dados exige a proteção da sessão. | ADR-006 |
| INV-4 | Todo valor exibido passa pelo escape de HTML. | ADR-006 |
| INV-5 | O banco não deixa alterar nem excluir registro de auditoria. | RB-30, RNF-06, ADR-007 |
| INV-6 | Uma operação que falha no banco não deixa alteração parcial. | RNF-09 |
| INV-7 | A suíte obrigatória roda sem dependência nem credencial; os testes de navegador são opcionais. | RNF-23, OPEN-29 |

## 6. Critérios de aceitação

| ID | Dado | Quando | Então | Cobre |
|---|---|---|---|---|
| CA-01 | nenhuma sessão | qualquer página protegida é pedida | a resposta leva à tela de entrada, sem dados | RNF-01, A1, INV-2 |
| CA-02 | um usuário ativo | ele entra com e-mail e senha corretos | vê o painel com o nome e o perfil, e o menu só tem as funcionalidades permitidas | RF-65, A2 |
| CA-03 | credenciais inválidas | alguém tenta entrar | a tela de entrada volta com a mensagem genérica, e nenhuma sessão é criada | RF-66 |
| CA-04 | o Contador com sessão | ele abre o formulário de novo título e, depois, envia o formulário mesmo assim | as duas respostas negam com o motivo, e nada é criado | RF-67, RNF-03, A2 |
| CA-05 | o Operador Financeiro com sessão | ele cadastra um cliente com CPF inválido | o formulário volta com os valores digitados e o motivo junto do campo documento | RNF-14, A3 |
| CA-06 | um título Aberto de R$ 100,00 | o Operador registra R$ 100,00 pelo formulário | a página do título mostra saldo de R$ 0,00 e o estado Baixado | UC-06, RNF-16 |
| CA-07 | o formulário de pagamento | ele é enviado duas vezes com o mesmo identificador | há um único pagamento | OPEN-25, A4 |
| CA-08 | um formulário sem a proteção da sessão | ele é enviado | é recusado, e nada muda | E1, INV-3 |
| CA-09 | um cliente cujo nome tem `<script>` | a lista de clientes é aberta | o nome aparece escapado | INV-4 |
| CA-10 | títulos Vencidos | a Dona abre o painel | os Vencidos aparecem em destaque, com o total em atraso | RNF-15, RNF-17 |
| CA-11 | um título com um pagamento estornado | a Dona abre o título | o histórico mostra quem estornou, quando e o motivo | UC-12, A1 |
| CA-12 | um título gravado | a aplicação é montada de novo sobre o mesmo banco | o título continua lá, com o mesmo saldo | A7 |
| CA-13 | o banco SQLite | alguém tenta alterar ou excluir um registro de auditoria direto no banco | o banco recusa | RNF-06, INV-5 |
| CA-14 | uma falha de gravação no banco durante um pagamento | o pagamento é solicitado | nada permanece: nem pagamento, nem auditoria | RNF-09, INV-6 |
| CA-15 | um título Aberto com vencimento ontem | o agendador roda | o título passa a Vencido, com registro de operação automática | A5 |
| CA-16 | o servidor configurado para a rede | ele inicia sem certificado; depois, com certificado e chave | sem certificado, recusa; com eles, usa HTTPS e o cookie de sessão é seguro | OPEN-38, RNF-05, E3 |
| CA-17 | o Administrador com sessão | ele cadastra um usuário e retira uma permissão pela tela | o usuário existe, e a permissão vale na operação seguinte | UC-02, RF-03 |
| CA-18 | um usuário com sessão | ele sai | a sessão deixa de valer | A6 |
| CA-19 | um banco vazio | a demonstração é preparada | há um usuário de cada perfil, exceto Cliente, clientes e títulos Aberto, Vencido, Baixado e Cancelado | A8 |
| CA-20 | um erro inesperado ao montar uma página | a página é pedida | a resposta é a página de erro, com o identificador de correlação, e o erro é registrado | E2, RNF-21 |
| CA-21 | qualquer resposta | ela é inspecionada | tem os cabeçalhos de segurança, e o cookie de sessão é `HttpOnly` e `SameSite` | INV-3 |
| CA-22 | uma página que não existe | ela é pedida | a resposta é "página não encontrada" | E4 |
| CA-23 | o navegador, se o Playwright estiver instalado | o usuário entra, registra o pagamento integral de um título e o abre | o título aparece Baixado | Fluxo principal; `docs/testes.md` |

Os testes automatizados levam no nome o identificador do critério, por exemplo `test_CA_08_formulario_sem_protecao_e_recusado`.

## 7. Questões em aberto

| ID | Questão | Bloqueia a implementação? |
|---|---|---|
| OPEN-01 | Framework web | Decidida em 2026-10-23, por delegação: WSGI da biblioteca padrão (ADR-006). |
| OPEN-12 | Hospedagem | Decidida em 2026-10-23, por delegação: execução local. |
| OPEN-29 | Ferramentas de teste | Decidida em 2026-10-23, por delegação: `unittest` no próprio processo; Playwright opcional. |
| OPEN-36 | Banco relacional | Decidida em 2026-10-23, por delegação: SQLite (ADR-007). |
| OPEN-38 | HTTPS na execução local | Decidida em 2026-10-23, por delegação. |
| OPEN-48 | Frequência da verificação automática | Decidida em 2026-10-23, por delegação: na inicialização e a cada hora. |

## 8. Verificação

Verificada em 2026-10-23, com `python3 -m unittest discover -s tests -t .`: 331 testes, todos passando (7 pulados, dos quais 6 dependem de specs futuras e 1 é o teste de navegador, sem o Playwright). Com o Playwright instalado, o teste de navegador também passa (6 pulados). A suíte também passou com o ambiente vazio (`env -i`). Testes em [`tests/apresentacao/test_spec_017_web.py`](../../tests/apresentacao/test_spec_017_web.py), [`tests/infraestrutura/test_sqlite.py`](../../tests/infraestrutura/test_sqlite.py) e [`tests/ponta_a_ponta/test_navegador.py`](../../tests/ponta_a_ponta/test_navegador.py). Plano em [`plans/017-plano.md`](../plans/017-plano.md) e tarefas em [`tasks/017-tarefas.md`](../tasks/017-tarefas.md).

### Critérios de aceitação

| Critério | Teste | Resultado |
|---|---|---|
| CA-01 | `test_CA_01` (15 páginas e 9 envios, com sessão inventada) | Passou |
| CA-02 | `test_CA_02` (Contador, Administrador e Operador) | Passou |
| CA-03 | `test_CA_03` | Passou |
| CA-04 | `test_CA_04` | Passou |
| CA-05 | `test_CA_05` | Passou |
| CA-06 | `test_CA_06` | Passou |
| CA-07 | `test_CA_07` | Passou |
| CA-08 | `test_CA_08` | Passou |
| CA-09 | `test_CA_09` | Passou |
| CA-10 | `test_CA_10` | Passou |
| CA-11 | `test_CA_11` | Passou |
| CA-12 | `test_CA_12` (pela interface) e `test_CA_12` de `tests/infraestrutura/test_sqlite.py` (pelos serviços) | Passou |
| CA-13 | `test_CA_13` de `test_sqlite.py`; `test_RNF_06_perfil_nenhum_exclui_*` | Passou |
| CA-14 | `test_CA_14` de `test_sqlite.py` | Passou |
| CA-15 | `test_CA_15`; `test_OPEN_48_*` (agendador em segundo plano) | Passou |
| CA-16 | `test_CA_16_OPEN_38_*`, `test_CA_16_RNF_05_com_https_*` e `test_CA_16_RNF_05_servidor_com_certificado_*` (servidor HTTPS real, com certificado gerado pelo `openssl`) | Passou |
| CA-17 | `test_CA_17` | Passou |
| CA-18 | `test_CA_18`; `test_usuario_inativado_pela_tela_*` | Passou |
| CA-19 | `test_CA_19` | Passou |
| CA-20 | `test_CA_20` | Passou |
| CA-21 | `test_CA_21` | Passou |
| CA-22 | `test_CA_22`; `test_metodo_errado_*` (405, 413 e arquivos estáticos) | Passou |
| CA-23 | `test_CA_23` em `tests/ponta_a_ponta/test_navegador.py`, com Playwright 1.56 e Chromium; pulado onde o Playwright não está instalado | Passou |

### Invariantes

| Invariante | Como foi verificada | Resultado |
|---|---|---|
| INV-1 | `test_INV_1_a_apresentacao_nao_usa_regras_do_dominio_diretamente` e a regra de camadas de `tests/arquitetura/test_camadas.py` | Passou |
| INV-2 | CA-01 e CA-18 | Passou |
| INV-3 | CA-08 e CA-21 | Passou |
| INV-4 | CA-09 | Passou |
| INV-5 | CA-13 | Passou |
| INV-6 | CA-14 | Passou |
| INV-7 | Suíte com o ambiente vazio; o teste de navegador é pulado sem o Playwright | Passou |

### Divergências e limitações

| Item | Situação |
|---|---|
| Testes antigos ajustados | O teste de CA-13 da Spec 001 passou a procurar as formas de ler variável de ambiente (`os.environ`, `getenv`), porque o servidor WSGI tem o atributo `base_environ`, que é a requisição. O teste de RF-24 passou a aceitar um único ponto que lê o relógio da máquina, o adaptador `infraestrutura/relogio.py`. A pendência de RNF-06 no armazenamento real virou teste. |
| Servidor de apresentação | O `wsgiref` atende uma requisição por vez. Basta para a execução local (OPEN-12); para hospedagem real, a aplicação WSGI roda em outro servidor WSGI sem mudança de código. |
| Mensagens de recusa | Algumas ainda trazem o identificador da regra, como "(RB-23)", e o saldo em formato decimal, como "3800.00" (usabilidade, U-09). Ficam para revisão da equipe. |
| Campo de data | O formato exibido segue o idioma do navegador; num navegador em português, dd/mm/aaaa. |
| Backup (RNF-08) | Não automatizado; o arquivo SQLite se copia com a API de backup. Fica para a entrega. |
| Painel | Só a parte de títulos de RNF-15 e RNF-17; obrigações e cobranças entram na Spec 016. |
