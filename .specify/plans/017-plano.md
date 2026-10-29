# Plano técnico — Spec 017

Spec: [017 — Interface web: acesso, clientes, títulos e auditoria](../specs/017-interface-web.md).

## Tecnologia

- Python 3.11, somente a biblioteca padrão (OPEN-01): `wsgiref` para o servidor, `http.cookies`, `html` e `urllib.parse` na interface (ADR-006); `sqlite3` para o banco (ADR-007); `ssl` para HTTPS (OPEN-38); `zoneinfo` para o fuso de referência, com alternativa fixa em UTC-3 quando o sistema não tem a base de fusos (OPEN-26).
- Páginas HTML renderizadas no servidor, sem JavaScript, com um único arquivo CSS.
- Testes de API em `unittest`, chamando a aplicação WSGI no próprio processo; teste de navegador com Playwright, opcional (OPEN-29).

## Organização

| Camada | Módulo | Conteúdo |
|---|---|---|
| Apresentação | `apresentacao/web/aplicacao_web.py` | Aplicação WSGI: rotas, sessão por cookie, proteção dos formulários, cabeçalhos de segurança, páginas de erro |
| Apresentação | `apresentacao/web/paginas.py` | Páginas: entrada, painel, clientes, títulos, auditoria, usuários, permissões, erros |
| Apresentação | `apresentacao/web/html.py`, `formatos.py` | Escape de HTML (INV-4); reais, datas, CPF, CNPJ e telefone no formato brasileiro |
| Apresentação | `apresentacao/web/estatico/` | `estilo.css` e `icone.svg` |
| Entradas automáticas | `entradas/agendador.py` | Verificação de vencimento na inicialização e a cada hora (OPEN-13, OPEN-48) |
| Infraestrutura | `infraestrutura/sqlite.py` | Migração numerada, unidade de trabalho com `BEGIN IMMEDIATE` e um repositório por porta; gatilhos que recusam alterar e excluir auditoria |
| Infraestrutura | `infraestrutura/relogio.py` | Relógio do sistema, em UTC |
| Composição | `inicializacao.py`, `__main__.py`, `demonstracao.py`; `iniciar.py` na raiz | Montagem das camadas, linha de comando, dados de demonstração |

## Decisões locais

- **Sessão em cookie `HttpOnly` e `SameSite=Lax`**, com `Secure` quando há HTTPS. O identificador vai só no cookie; o banco guarda o resumo (Spec 002).
- **Proteção dos formulários.** Todo formulário que altera dados leva o token de proteção da sessão, conferido com `hmac.compare_digest`. O formulário de entrada, que ainda não tem sessão, usa um token em cookie próprio.
- **Cabeçalhos.** `Content-Security-Policy` sem script e sem estilo inline, `frame-ancestors 'none'`, `X-Frame-Options: DENY`, `nosniff`, `Referrer-Policy: same-origin` e `Cache-Control: no-store` nas páginas; `Strict-Transport-Security` com HTTPS.
- **Erros dos formulários (RNF-14).** A recusa do domínio traz os campos (`OperacaoRecusada.campos`); a página volta com os valores digitados e a mensagem junto de cada campo, com `aria-invalid`. A leitura de valor em reais e de data é da apresentação; as regras continuam no domínio.
- **Permissão das páginas.** O menu mostra só as operações do perfil (RF-65). Abrir a página de uma operação não permitida chama `ServicoAcesso.exigir`, que passa pelo ponto único de autorização e devolve o motivo da matriz (RF-67).
- **Pedido de pagamento (OPEN-25).** O formulário de pagamento leva um identificador gerado ao montar a página; o serviço ignora o segundo envio com o mesmo identificador, e o banco tem `UNIQUE (titulo_id, pedido_id)`.
- **Erro não tratado (RNF-21).** A página de erro mostra só o identificador de correlação. Se o erro veio de um serviço, o identificador é o que a execução já registrou; se veio da própria interface, a interface registra.
- **Servidor.** O `wsgiref` atende uma requisição por vez, o que basta para a apresentação local; o agendador roda em outra linha de execução, com conexão SQLite própria.
- **Demonstração.** Os dados são criados pelos serviços, com as sessões dos próprios usuários, para que a auditoria seja a de uma operação real. A senha é informada no comando ou gerada na hora e mostrada no terminal; não fica em arquivo.
- **Painel.** Nesta spec, o painel tem os títulos (a receber, em atraso, vencendo em breve, baixados) e, para quem consulta a auditoria, as últimas operações. Obrigações e cobranças entram na Spec 016.

## Tarefas

Em [`../tasks/017-tarefas.md`](../tasks/017-tarefas.md).
