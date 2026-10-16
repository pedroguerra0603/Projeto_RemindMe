# Como executar — RemindMe

O projeto ainda não tem interface. O que existe é o domínio e a camada de aplicação da [Spec 006](../.specify/specs/006-titulo-pagamento-baixa-e-estorno.md), verificados por testes.

## Pré-requisitos

- Python 3.11 ou mais recente.
- Nenhuma dependência externa: o código e os testes usam apenas a biblioteca padrão.

## Executar os testes

Na raiz do repositório:

```
python3 -m unittest discover -s tests -t .
```

## A definir

As instruções de configuração e de execução da aplicação serão escritas aqui quando houver interface. Dependem do framework web (OPEN-01), do banco de dados (OPEN-02) e da hospedagem (OPEN-12), em [`.specify/open.md`](../.specify/open.md).

## Restrição já definida

A aplicação e a suíte de testes devem rodar sem credencial de serviço externo, com o canal de notificação e o serviço de IA simulados (RNF-23).
