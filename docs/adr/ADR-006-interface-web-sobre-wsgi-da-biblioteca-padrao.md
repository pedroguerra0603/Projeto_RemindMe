# ADR-006 — Interface web sobre o WSGI da biblioteca padrão

- **Situação:** Aceito
- **Data:** 2026-10-23
- **Decisores:** João Pedro Silva Guerra, por delegação ao agente; a confirmar na revisão do PR
- **Drivers:** DA-01, DA-04, DA-07
- **Requisitos e regras:** RNF-01, RNF-02, RNF-03, RNF-05, RNF-14, RNF-23; OPEN-01, OPEN-12, OPEN-29

## Contexto

O projeto usa Python 3.11 somente com a biblioteca padrão (OPEN-01), e a suíte roda sem instalar nada (RNF-23). A primeira interface precisa de páginas, formulários, sessão e autenticação, para uma apresentação executada na máquina de quem apresenta (OPEN-12). As regras de acesso já ficam na camada de aplicação (DT-06), e não na interface.

## Decisão

A interface web é uma aplicação WSGI escrita sobre a biblioteca padrão (`wsgiref`, `http.cookies`, `html`, `urllib.parse`), sem framework de terceiros. Roteamento, páginas, cookies e proteção de formulário ficam na camada de apresentação, em `src/remindme/apresentacao/web/`.

## Alternativas consideradas

| Alternativa | Por que não |
|---|---|
| Flask | Dependência a instalar em cada máquina e na integração contínua; a suíte deixaria de rodar sem instalação (RNF-23). |
| Django | Traz ORM, autenticação e administração próprios, que duplicam as camadas de aplicação e de infraestrutura e puxam regra para fora do domínio (ADR-001). |
| FastAPI | Exige servidor ASGI e várias dependências; o foco em API não ajuda as telas. |

## Consequências

- Positivas: nenhuma dependência nova; a aplicação roda com `python3 -m remindme` em qualquer máquina com Python 3.11; os testes de API chamam a aplicação WSGI no próprio processo (OPEN-29).
- Negativas: o projeto mantém o próprio roteamento, as páginas e a proteção contra falsificação de requisição (CSRF), que um framework traria prontos. O servidor `wsgiref` atende uma requisição por vez, o que basta para a apresentação, mas não para produção.
- O que passa a ser obrigatório: todo valor exibido passa pelo escape de HTML; todo formulário que altera dados leva o token de proteção da sessão; nenhuma regra de negócio ou de permissão fica na apresentação.
