# Como executar — RemindMe

O projeto ainda não tem interface. O que existe é a fundação da [Spec 001](../.specify/specs/001-fundacao-camadas-e-auditoria.md) (camadas, auditoria de operações e registro de erro não tratado) e o domínio e a camada de aplicação da [Spec 006](../.specify/specs/006-titulo-pagamento-baixa-e-estorno.md), verificados por testes.

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

## A definir

As instruções de configuração e de execução da aplicação serão escritas aqui quando houver interface. Dependem do framework web (OPEN-01), do banco de dados (OPEN-02) e da hospedagem (OPEN-12), em [`.specify/open.md`](../.specify/open.md).

## Restrição já definida

A aplicação e a suíte de testes devem rodar sem credencial de serviço externo, com o canal de notificação e o serviço de IA simulados (RNF-23).
