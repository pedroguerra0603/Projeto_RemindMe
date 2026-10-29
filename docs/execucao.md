# Como executar — RemindMe

O RemindMe é uma aplicação web que roda com Python e nada mais: servidor WSGI e banco SQLite da biblioteca padrão ([Spec 017](../.specify/specs/017-interface-web.md)).

## Pré-requisitos

- Python 3.11 ou mais recente.
- Nenhuma dependência externa: o código e os testes usam apenas a biblioteca padrão.

## Executar os testes

Na raiz do repositório:

```
python3 -m unittest discover -s tests -t .
```

## Integração contínua

A suíte roda sozinha a cada PR e a cada push na `main`, pelo fluxo [`.github/workflows/testes.yml`](../.github/workflows/testes.yml). A ferramenta (GitHub Actions) é provisória, até a decisão da equipe em OPEN-28. O fluxo não usa segredo nem instala dependência (RNF-23).

| Item | Valor |
|---|---|
| Quando | Em todo PR e em todo push na `main` |
| Matriz | Python 3.11, 3.12 e 3.13, em Ubuntu, Windows e macOS (9 combinações) |
| Comando | O mesmo do desenvolvimento: `python -m unittest discover -s tests -t . -v` |

**Como ler o resultado.** Na página do PR, a seção de verificações lista uma linha por combinação, no formato `testes / suíte (Python 3.12, ubuntu-latest)`. Verde significa que a suíte inteira passou. Vermelho significa que algum teste falhou: abra a linha, depois o passo "Executar a suíte", e procure `FAIL:` ou `ERROR:`, que trazem o nome do teste, com o identificador da regra, e o motivo. Teste com `skipped` está pendente de uma spec e não é falha. `expected failures` é defeito conhecido e registrado em [`qualidade/defeitos.md`](qualidade/defeitos.md); `unexpected successes` quer dizer que o defeito foi corrigido e a marcação deve ser retirada.

**Um PR com teste falhando aparece como reprovado** (marca vermelha) e não deve ser mesclado.

**Proteção da `main` (configuração do repositório, feita por quem o administra).** Para o merge exigir a suíte aprovada: *Settings → Branches → Branch protection rule* (ou *Rulesets*) para `main` → marcar *Require status checks to pass before merging* → selecionar as verificações `testes / suíte (...)`. Isso não pode ser feito por código do repositório; **está pendente** e é o último critério da issue #82. Os resultados das combinações de Windows e macOS são os primeiros para essa suíte (a portabilidade nesses sistemas ainda não foi verificada, em [`qualidade/portabilidade.md`](qualidade/portabilidade.md)): se alguma falhar na primeira execução, é um achado de portabilidade, e não um erro do fluxo.

## Executar a aplicação

Todos os comandos rodam na raiz do repositório. `executar.py` só acrescenta `src/` ao caminho do Python; com `src/` no `PYTHONPATH`, `python3 -m remindme` faz o mesmo.

### Demonstração

```bash
python3 executar.py demo --senha demo12345
python3 executar.py servir
```

`demo` cria, num banco vazio, um usuário de cada perfil (`admin@`, `dona@`, `operador@` e `contador@remindme.local`), quatro clientes e sete títulos em estados variados. Sem `--senha`, a senha é gerada e mostrada na tela. Abra <http://127.0.0.1:8000>.

### Instalação real

```bash
python3 executar.py --banco /caminho/remindme.db criar-admin --nome "Ana" --email ana@empresa.com.br
python3 executar.py --banco /caminho/remindme.db servir --host 0.0.0.0 --porta 8000 --https
```

O Administrador cadastra os demais usuários pela tela **Usuários**. A senha do `criar-admin` é digitada sem aparecer na tela; numa instalação automatizada, pode ser passada pela entrada padrão (`echo "$SENHA" | python3 executar.py criar-admin ...`).

### Opções

| Opção | Padrão | Uso |
|---|---|---|
| `--banco` (antes do comando) | `remindme.db` | Arquivo SQLite. É criado na primeira execução |
| `servir --host` | `127.0.0.1` | `0.0.0.0` para aceitar conexões de outras máquinas ou de um contêiner |
| `servir --porta` | `8000` | Porta HTTP |
| `servir --https` | desligado | Marca os cookies como `Secure`. Use quando houver HTTPS na frente (RNF-05) |
| `servir --antecedencia-dias` | `5` | Dias para sinalizar "próximo do vencimento" (RF-23, OPEN-21) |
| `servir --intervalo-agendador` | `60` | Minutos entre as verificações automáticas de vencimento (OPEN-13) |

O sistema não lê variáveis de ambiente (Spec 001, CA-13). A chave que assina os formulários é gerada na primeira execução e guardada no próprio banco.

### Publicação

A hospedagem continua em aberto (OPEN-12). Qualquer serviço que rode um processo Python serve: o comando de início é `python3 executar.py --banco <disco persistente>/remindme.db servir --host 0.0.0.0 --porta <porta do serviço> --https`. O TLS (RNF-05) fica no proxy do serviço. `GET /saude` responde `ok`, para verificação de saúde. O arquivo do banco precisa ficar num disco persistente, com cópia de segurança (RNF-08, OPEN-09).

### Agendador

O servidor verifica os vencimentos ao iniciar e depois a cada intervalo, numa thread separada, fora do caminho das requisições (DT-07). Cada mudança aparece na auditoria como operação automática da rotina "verificação de vencimento" (OPEN-30). Usuários com permissão também podem disparar a verificação pela tela de títulos.

## Restrição já definida

A aplicação e a suíte de testes devem rodar sem credencial de serviço externo, com o canal de notificação e o serviço de IA simulados (RNF-23).
