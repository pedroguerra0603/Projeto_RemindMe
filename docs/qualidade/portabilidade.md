# Avaliação de Portabilidade — RemindMe

Issue #63. Característica **Portabilidade** da ISO/IEC 25010: adaptabilidade, capacidade de instalação e capacidade de substituição.

- **Data:** 2026-10-09.
- **O que se instala hoje:** o domínio e a camada de aplicação da Spec 006, com a suíte de testes. Não há interface, banco nem serviço externo (OPEN-01, OPEN-02, OPEN-12).
- **Requisitos de referência:** RNF-23 (suíte sem credencial externa), `docs/execucao.md` (Python 3.11 ou mais recente, sem dependência externa).
- **Critério de aprovação:** a suíte inteira passa, sem instalar nada além do interpretador.

## 1. Capacidade de instalação

| Passo | Resultado |
|---|---|
| Pré-requisito | Somente Python 3.11 ou mais recente. Nenhum pacote a instalar, verificado pelo teste `test_OPEN_01_codigo_usa_somente_a_biblioteca_padrao` |
| Instalação | `git clone` do repositório. Não há `pip install`, `pyproject.toml` nem script de instalação |
| Configuração | Nenhuma: não há variável de ambiente, arquivo `.env` nem credencial (RNF-23) |
| Verificação | `python3 -m unittest discover -s tests -t .` na raiz |

## 2. Registro dos testes de ambiente

Executados em 2026-10-09, sobre a branch desta avaliação (64 testes no momento da execução). Máquina: Linux x86_64 (glibc 2.39), Intel Xeon 2,80 GHz.

| ID | Ambiente | Comando ou condição | Resultado |
|---|---|---|---|
| P-01 | Python 3.11.17 | `python3.11 -m unittest discover -s tests -t .` | Passou, 64 testes |
| P-02 | Python 3.12.3 | `python3.12 ...` | Passou, 64 testes |
| P-03 | Python 3.13.16 | `python3.13 ...` | Passou, 64 testes |
| P-04 | Modo isolado, sem variáveis `PYTHON*` nem pacotes do usuário | `python3 -I ...` | Passou |
| P-05 | Avisos tratados como erro, modo de desenvolvimento | `python3 -W error -X dev ...` | Passou, nenhum aviso |
| P-06 | Locale mínimo, sem UTF-8 no ambiente | `LC_ALL=C LANG=C` | Passou; os fontes são lidos como UTF-8 |
| P-07 | Semente de hash diferente | `PYTHONHASHSEED=12345` | Passou; nenhum teste depende da ordem de conjuntos |
| P-08 | Fuso horário distante (UTC+14) | `TZ=Pacific/Kiritimati` | Passou; datas são injetadas e não dependem do relógio da máquina |
| P-09 | Executado a partir de outro diretório | `cd / && python3 -m unittest discover -s <repo>/tests -t <repo>` | Passou |
| P-10 | Clone novo em caminho com espaço e acento | `.../Área de Trabalho/RemindMe` | Passou |
| P-11 | Clone sem permissão de escrita, sem gerar bytecode | `chmod -R a-w` e `PYTHONDONTWRITEBYTECODE=1` | Passou, com ressalva: a execução foi como `root`, que ignora a permissão. Repetir com usuário comum |

## 3. Não testado

| Ambiente | Motivo | Risco |
|---|---|---|
| Windows e macOS | Indisponíveis no ambiente da avaliação | Baixo: o código não usa caminho de arquivo, processo nem recurso do sistema operacional. O teste de arquitetura lê arquivos com `pathlib` e `encoding="utf-8"` |
| Python 3.10 ou anterior | Fora do pré-requisito de `docs/execucao.md` | `sys.stdlib_module_names`, usado no teste de arquitetura, exige 3.10 |
| Python 3.14 e PyPy | Não instalados; instalar interpretador exige aprovação (CLAUDE.md) | Baixo |
| Contêiner | Docker indisponível na máquina | — |

Os integrantes podem completar a tabela rodando o mesmo comando em suas máquinas e anotando sistema, versão do Python e resultado.

## 4. Adaptabilidade e substituição

| Aspecto | Avaliação |
|---|---|
| Troca da persistência | Preparada: o serviço depende das interfaces de `aplicacao/portas.py`, e a implementação em memória pode ser substituída pela de um banco sem alterar o domínio (OPEN-02) |
| Troca do relógio | Preparada: interface `Relogio`; datas de referência são parâmetros |
| Canal de notificação e IA | Previstos por interface (ADR-002, ADR-003); ainda não implementados |
| Interface web | Não existe; o domínio não depende de framework (verificado por `test_ADR_001_*`) |

## 5. Recomendações

| Recomendação | Onde tratar |
|---|---|
| Declarar a versão mínima em um arquivo do projeto (por exemplo, `.python-version` ou `pyproject.toml`) | Decisão da equipe; não exige dependência |
| Rodar a suíte em Linux, Windows e macOS a cada PR | Issue de integração contínua |
| Repetir P-01 a P-11 quando houver banco e interface, incluindo a instalação deles | Specs 001 e primeira spec com interface |
