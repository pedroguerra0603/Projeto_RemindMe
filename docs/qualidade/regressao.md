# Relatório de Regressão — RemindMe

Issue #69. Verifica se as alterações feitas no sistema quebraram o que já funcionava.

- **Linha de base:** commit `b17b1ed` (merge da Spec 006 em `main`), com 48 testes, todos passando, conforme a seção 8 da Spec 006.
- **Suíte de regressão:** a suíte inteira, `python3 -m unittest discover -s tests -t .`. Todo teste que passou uma vez entra na regressão.
- **Ambiente:** Linux x86_64, Python 3.13.16.

## 1. Procedimento

1. Executar a suíte inteira em **cada commit** da branch, em uma cópia limpa (`git worktree`), para saber em que commit uma falha teria entrado.
2. Executar os **48 testes da linha de base**, copiados de `b17b1ed`, contra o código mais recente, para provar que o comportamento verificado da Spec 006 não mudou.
3. Comparar o número de testes: ele só pode crescer. Teste removido ou renomeado precisa de justificativa.
4. Falha esperada (`expectedFailure`) só é aceita para defeito registrado, com issue de correção.

Comando usado no passo 1, na raiz do repositório:

```
for c in $(git rev-list --reverse b17b1ed^..HEAD); do
  git worktree add -q --detach /tmp/rm-wt $c
  (cd /tmp/rm-wt && python3 -m unittest discover -s tests -t . 2>&1 | tail -1)
  git worktree remove --force /tmp/rm-wt
done
```

## 2. Execução por commit

Executada em 2026-10-09.

| Commit | Alteração | Testes | Resultado |
|---|---|---|---|
| `02d2c8d` | Implementação da Spec 006 | 48 | Passou |
| `b17b1ed` | Merge da Spec 006 (linha de base) | 48 | Passou |
| `8f66c9e` | #41 Documentação final | 48 | Passou |
| `09572a0` | #48 Confiabilidade | 54 | Passou |
| `1b592c7` | #52 Usabilidade | 58 | Passou |
| `5338e21` | #58 Eficiência | 61 | Passou |
| `5a3290e` | #61 Manutenibilidade | 64 | Passou |
| `220ccd8` | #63 Portabilidade | 64 | Passou |
| `16a27d1` | #64 Testes unitários | 102 | Passou |
| `5e35046` | #65 Testes de integração | 111 | Passou |
| `e01d6ee` | #66 Matriz de critérios | 111 | Passou |
| `0fca159` | #67 Regras de negócio e invariantes | 121 | Passou |
| `019fa45` | #68 Exceções | 132 | Passou, com 3 falhas esperadas (D-01 a D-05) |

Nenhum teste foi removido nem renomeado. Até `019fa45` nenhuma alteração tocou em `src/`: o código de produção é o mesmo da linha de base.

## 3. Linha de base contra o código atual

A seção é refeita sempre que `src/` muda. A primeira alteração de código desta rodada é a correção de defeitos (#70); o resultado está em [defeitos](defeitos.md#regressão-depois-da-correção).

## 4. Conclusão

Nenhuma regressão até `019fa45`. A suíte cresceu de 48 para 132 testes, e as três falhas esperadas correspondem a defeitos registrados e com correção planejada.
