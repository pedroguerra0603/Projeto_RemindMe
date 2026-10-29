# Como executar — RemindMe

O RemindMe roda como aplicação web local, com Python 3.11 ou mais recente e **sem instalar nada**: servidor, banco (SQLite) e testes usam só a biblioteca padrão (OPEN-01, ADR-006, ADR-007). A primeira interface é a da [Spec 017](../.specify/specs/017-interface-web.md).

## Ver a aplicação em 1 minuto (demonstração)

Na raiz do repositório:

```
python3 iniciar.py demonstracao
```

O comando cria o banco `remindme-demonstracao.db` com dados de exemplo, mostra no terminal os usuários e a senha gerada, inicia o servidor e abre o navegador em **http://127.0.0.1:8000**. Rodar o mesmo comando de novo reaproveita a demonstração. No Windows, dá para usar o atalho `RemindMe-demonstracao.bat`; sem Python, use o GitHub Codespaces. Os três caminhos e a solução de problemas estão em [`apresentacao.md`](apresentacao.md). Entre com um dos usuários:

| Perfil | E-mail |
|---|---|
| Dono | `carla@demo.example` |
| Operador Financeiro | `diego@demo.example` |
| Contador | `helena@demo.example` |
| Administrador | `admin@demo.example` |

A senha é a mesma para todos e aparece no terminal. Para escolher a senha, use `--senha` (pelo menos 8 caracteres): `python3 iniciar.py demonstracao --senha minha-senha-de-apresentacao`. Para recomeçar do zero, acrescente `--substituir`. `Ctrl+C` encerra o servidor; para voltar depois ao mesmo banco, `python3 iniciar.py --banco remindme-demonstracao.db`.

A demonstração tem clientes e títulos em todos os estados: Aberto, Vencido (pela verificação automática), Baixado, Cancelado, com pagamento parcial e com estorno, além da trilha de auditoria de cada operação.

## Uso com dados reais

```
python3 iniciar.py criar-administrador      # pergunta nome, e-mail e senha (OPEN-39)
python3 iniciar.py                          # servidor em http://127.0.0.1:8000, banco remindme.db
```

O Administrador cadastra os demais usuários pela tela **Usuários**, com senha provisória (OPEN-35), e ajusta a tela **Permissões**. As permissões fixadas por regra de negócio aparecem com cadeado e não mudam.

| Opção | Uso |
|---|---|
| `--banco arquivo.db` | Arquivo SQLite (padrão: `remindme.db`). Bancos `*.db` não vão para o Git. |
| `--porta 8000` | Porta do servidor |
| `--host 127.0.0.1` | Endereço de escuta. Sem certificado, só a própria máquina (OPEN-38) |
| `--certificado cert.pem --chave chave.pem` | Liga o HTTPS (RNF-05); com eles, o servidor pode atender pela rede (`--host 0.0.0.0`) |

`python3 -m remindme` também funciona, com a pasta `src` no caminho de importação (por exemplo, `PYTHONPATH=src python3 -m remindme`). O comando `iniciar.py` faz isso sozinho.

**Verificação automática de vencimento.** Com o servidor no ar, os títulos Abertos com vencimento passado passam a Vencido na inicialização e a cada hora, com registro de operação automática na auditoria (OPEN-13, OPEN-48). O "hoje" é o de America/Sao_Paulo (OPEN-26).

## Pré-requisitos

- Python 3.11 ou mais recente.
- Nenhuma dependência externa para usar ou testar. O Playwright é opcional, só para o teste de navegador.

## Executar os testes

Na raiz do repositório:

```
python3 -m unittest discover -s tests -t .
```

## Integração contínua

A suíte roda sozinha a cada PR e a cada push na `main`, pelo fluxo [`.github/workflows/testes.yml`](../.github/workflows/testes.yml). A ferramenta é o GitHub Actions (OPEN-28, decidida em 2026-10-23). O fluxo não usa segredo nem instala dependência (RNF-23).

| Item | Valor |
|---|---|
| Quando | Em todo PR e em todo push na `main` |
| Matriz | Python 3.11, 3.12 e 3.13, em Ubuntu, Windows e macOS (9 combinações) |
| Comando | O mesmo do desenvolvimento: `python -m unittest discover -s tests -t . -v` |

**Como ler o resultado.** Na página do PR, a seção de verificações lista uma linha por combinação, no formato `testes / suíte (Python 3.12, ubuntu-latest)`. Verde significa que a suíte inteira passou. Vermelho significa que algum teste falhou: abra a linha, depois o passo "Executar a suíte", e procure `FAIL:` ou `ERROR:`, que trazem o nome do teste, com o identificador da regra, e o motivo. Teste com `skipped` está pendente de uma spec e não é falha. `expected failures` é defeito conhecido e registrado em [`qualidade/defeitos.md`](qualidade/defeitos.md); `unexpected successes` quer dizer que o defeito foi corrigido e a marcação deve ser retirada.

**Um PR com teste falhando aparece como reprovado** (marca vermelha) e não deve ser mesclado.

**Proteção da `main` (configuração do repositório, feita por quem o administra).** Para o merge exigir a suíte aprovada: *Settings → Branches → Branch protection rule* (ou *Rulesets*) para `main` → marcar *Require status checks to pass before merging* → selecionar as verificações `testes / suíte (...)`. Isso não pode ser feito por código do repositório; **está pendente** e é o último critério da issue #82. Os resultados das combinações de Windows e macOS são os primeiros para essa suíte (a portabilidade nesses sistemas ainda não foi verificada, em [`qualidade/portabilidade.md`](qualidade/portabilidade.md)): se alguma falhar na primeira execução, é um achado de portabilidade, e não um erro do fluxo.

## Teste de navegador (opcional)

O teste de ponta a ponta (`tests/ponta_a_ponta/`) só roda com o Playwright instalado; sem ele, aparece como pulado, e a suíte continua sem dependência (OPEN-29):

```
pip install playwright
python -m playwright install chromium
python3 -m unittest tests.ponta_a_ponta.test_navegador
```

## Restrição

A aplicação e a suíte de testes devem rodar sem credencial de serviço externo, com o canal de notificação e o serviço de IA simulados (RNF-23).
