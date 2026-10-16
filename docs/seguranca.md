# Segurança — RemindMe

Este documento tem duas partes: a segurança do produto ao longo do desenvolvimento (SSDLC) e a segurança no uso de agentes de codificação pela equipe.

## 1. Segurança do produto

### O que proteger

| Ativo | Ameaça principal | Controle | Requisito |
|---|---|---|---|
| Valores e estados de títulos | Alteração por perfil sem permissão | Negar por padrão; validação no servidor | RNF-02, RNF-03 |
| Pagamentos | Estorno indevido | Só o Dono estorna, com motivo | RB-02, RF-31 |
| Dados de um cliente | Acesso por outro cliente | Filtro por cliente dentro da consulta | RNF-25, RB-26 |
| Senhas | Vazamento do armazenamento | Hash com salt por algoritmo adaptativo | RNF-04 |
| Dados em trânsito | Interceptação | Somente HTTPS | RNF-05 |
| Trilha de auditoria | Adulteração | Somente inclusão | RNF-06, RB-30 |
| Dados enviados à IA | Exposição de dados pessoais | Envio apenas de descrição ou texto, sem identificação | RNF-22 |
| Decisões financeiras | Mensagem de cliente que tenta induzir a IA | Saída da IA validada por regra; a IA não decide | RB-27, ADR-003 |
| Importação CSV | Arquivo malformado ou malicioso | Validação por linha; tudo ou nada | RB-19, RF-84 |

### Práticas por etapa

| Etapa | Prática |
|---|---|
| Requisitos | Requisitos de segurança escritos como RNF verificáveis. |
| Design | Autorização em um único ponto da camada de aplicação. Regras no domínio. |
| Implementação | Nenhum segredo no repositório. Variáveis de ambiente fora do Git. Entradas validadas no servidor. |
| Testes | Um teste por perfil × operação sensível. Teste de acesso a dado de outro cliente. Teste de tentativa de alterar auditoria. |
| Revisão | Todo PR é revisado por um colega. A revisão pergunta se o código implementa a spec e se preserva as RB. |
| Entrega | Configuração por ambiente. Senhas e chaves fora do código. |

### Dados pessoais

O sistema guarda nome, documento e contato de clientes, e nome e e-mail de usuários. Esses dados servem apenas à operação de cobrança e ao controle de acesso. Não são enviados ao serviço de IA.

## 2. Segurança no uso de agentes de codificação

A spec limita o comportamento esperado do agente. A governança técnica limita as ações perigosas. Uma não substitui a outra, e nenhuma substitui a revisão humana.

### Ambiente da equipe

> **A preencher pela equipe.** Informar, para cada integrante, qual ferramenta usa. Disso depende quais camadas abaixo estão de fato ativas.

| Integrante | Ferramenta | Tem hook de agente? |
|---|---|---|
| João Pedro Silva Guerra | a informar | a informar |
| Bernardo Sanches | a informar | a informar |
| Renan Ribeiro Gandolpho | a informar | a informar |

Ferramentas possíveis: Cursor, Claude Code, VS Code com agente que possui hook, VS Code com Copilot sem hook.

### Defesa em camadas

| Camada | O que faz | Situação neste repositório |
|---|---|---|
| 1. Instrução no repositório | Orienta o agente antes de propor uma ação | Ativa: [`CLAUDE.md`](../CLAUDE.md) |
| 2. Hook de agente | Intercepta a ação e decide permitir, perguntar ou negar | Depende da ferramenta de cada integrante |
| 3. Git hook local | Bloqueia antes do commit | Não configurado |
| 4. CI e revisão | Bloqueia antes do merge | Revisão por PR em uso. CI não configurado, pois ainda não há código. |

Para quem usa VS Code sem hook de ferramenta, as camadas 3 e 4 são obrigatórias. Elas devem ser configuradas antes do início da implementação.

### Política de ações do agente

| Veredito | Ações | Exemplos |
|---|---|---|
| Permitir | Leitura, análise e verificação | Ler arquivos do repositório, rodar testes, rodar lint, `git status`, `git diff` |
| Perguntar | Ações legítimas com custo de reversão | `git commit`, `git push`, instalar dependência nova, criar ou alterar migração de banco |
| Negar | Ações destrutivas ou exposição de segredo | Ler `.env` ou `mcp.env`, `git push --force`, `DROP`, `TRUNCATE`, apagar histórico |

### Segredos

- Arquivos de variáveis de ambiente (`.env`, `mcp.env`) não entram no Git; ver [`.gitignore`](../.gitignore).
- Arquivos de configuração de ferramentas (`mcp.json`) entram no Git apenas com nomes de variáveis, sem valores.
- Senha, chave ou token nunca são colados no prompt do agente.

### Regras de governança

1. O agente não implementa sem uma spec aprovada.
2. O agente não preenche lacunas: decisão ausente vira `OPEN-nn` em [`.specify/open.md`](../.specify/open.md).
3. Conflito entre código, spec e baseline é registrado. Alterar a baseline exige decisão humana.
4. O uso do agente é declarado no PR.
