# Estratégia de Testes e Qualidade — RemindMe

> Os testes usam `unittest`, da biblioteca padrão do Python, pela decisão de OPEN-01 (2026-10-03). A Spec 006 é a primeira implementada: a suíte está em [`tests/`](../tests/README.md), e a avaliação de qualidade, em [`qualidade/`](qualidade/README.md). Ainda não há interface nem API, porque o framework web está em aberto (OPEN-01); os testes desses níveis estão apenas planejados, abaixo. Como executar: [`execucao.md`](execucao.md).

## Princípios

1. **Cada cláusula obrigatória vira ao menos um teste.** Todo RF com SHALL e toda RB têm teste.
2. **O teste leva o identificador no nome.** Exemplo: `RB-23_recusa_pagamento_maior_que_o_saldo`.
3. **Regra de domínio é testada sem banco e sem interface.**
4. **A suíte roda sem credencial externa**, com canal de notificação e serviço de IA simulados (RNF-23).
5. **O critério de aceite é binário.** Cada critério de uma spec, no formato Dado, Quando, Então, corresponde a um teste que passa ou não passa.

## Níveis

| Nível | O que cobre | Depende de |
|---|---|---|
| Unidade de domínio | Regras de negócio, cálculos e transições de estado | Nada externo |
| Aplicação | Casos de uso: permissão, transação, auditoria | Repositórios em memória; canal e IA simulados |
| Integração | Persistência, atomicidade, unicidade | Banco de dados de teste |
| Aceite | Critérios Dado, Quando, Então de cada spec | Sistema completo com simuladores |

## Pirâmide de testes

Aplicação da Pirâmide de Testes (Martin Fowler; Ham Vocke, *The Practical Test Pyramid*): muitos testes de unidade, menos de integração e poucos de ponta a ponta, para evitar o "cone de sorvete" (Hartanto), em que quase tudo é testado pela interface, de forma lenta e frágil. Issue #80.

### Proporção-alvo

| Nível | Pasta | Alvo | Justificativa |
|---|---|---|---|
| Unidade de domínio e de infraestrutura | `tests/dominio/`, `tests/infraestrutura/` | 50% a 60% | As regras de negócio vivem no domínio, sem banco e sem interface (ADR-001, RNF-19). São os testes mais rápidos e os que mais localizam um defeito. Cada RB tem teste nomeado pelo identificador |
| Aplicação | `tests/aplicacao/`, exceto o aceite | 20% a 30% | Permissão, transação, auditoria e falha injetada (RNF-02, RNF-09) só existem na camada de aplicação. Usa repositórios em memória, então continua rápido |
| Integração | `tests/integracao/` | 5% a 10% | Poucos, porque cada um exige banco real. Verificam o que a unidade não alcança: atomicidade, unicidade e contrato do repositório |
| Aceite | `tests/aplicacao/test_spec_006_aceite.py` | 10% a 15% | Um teste por critério Dado, Quando, Então de cada spec. O número é dado pela spec, e não escolhido |
| Interface e API | — (planejado, seção abaixo) | no máximo 5% | Lentos e frágeis. Só os fluxos críticos |

Os testes de arquitetura (`tests/arquitetura/`) e de desempenho (`tests/desempenho/`) são transversais: guardam a regra de dependência (ADR-001) e o limite de RNF-11. Ficam fora da proporção.

### Contagem atual

Suíte de 2026-10-16: 199 testes (9 pulados por dependerem de specs não aprovadas e 1 falha esperada do defeito D-06, ambos contados). Comando: carregar a suíte com `unittest.defaultTestLoader.discover` e contar por módulo.

| Nível | Testes | Participação | Alvo | Situação |
|---|---|---|---|---|
| Unidade de domínio | 86 | 44,6% | — | — |
| Unidade de infraestrutura | 11 | 5,7% | — | — |
| **Unidade, total** | **97** | **50,3%** | 50% a 60% | No alvo, no limite inferior |
| Aplicação (sem o aceite) | 58 | 30,1% | 20% a 30% | Marginalmente acima do limite |
| Integração | 9 | 4,7% | 5% a 10% | Um pouco abaixo; ver lacuna 2 |
| Aceite (Spec 006) | 29 | 15,0% | 10% a 15% | No alvo, no limite superior |
| Interface e API | 0 | 0% | até 5% | Não existe (OPEN-01) |
| Transversais (arquitetura e desempenho) | 6 | — | fora da proporção | — |

Percentuais sobre os 193 testes dos quatro níveis (199 menos os 6 transversais).

### Lacunas

1. **Base no limite inferior, aplicação no superior.** A forma é de pirâmide, mas sem folga: a unidade está em 50,3% (limite inferior) e a aplicação em 30,1% (um décimo acima do limite). Os testes de qualidade (confiabilidade, exceções, idempotência, segurança de acesso) foram escritos na camada de aplicação porque exercitam o serviço com falha injetada e perfil; é o lugar certo para eles. O risco é a proporção se inverter conforme as próximas specs entrarem. Proposta: pôr cada regra nova no domínio e testá-la ali primeiro, deixando na aplicação só o que depende de perfil, transação e auditoria.
2. **Integração só com repositório em memória e um pouco abaixo do alvo.** Os 9 testes de integração rodam contra a implementação em memória. Atomicidade, unicidade e concorrência reais só são verificáveis com o banco (OPEN-02); o contrato do repositório de títulos foi escrito para ser reaplicado. Quando houver banco, este nível cresce e passa da faixa mínima.
3. **Topo da pirâmide inexistente.** Não há teste de API nem de interface. É esperado: não há interface (OPEN-01). O plano está na seção "Testes de API e de ponta a ponta".
4. **Sem medição de cobertura.** A pirâmide mede quantidade de testes, e não o que eles exercitam. A decisão sobre medir cobertura é OPEN-24.
5. **Não há cone de sorvete.** Nenhum teste passa pela interface, e os testes de aceite usam o serviço com repositórios em memória, rápidos (a suíte inteira roda em cerca de 3,5 s).

Esta seção é proposta de alteração da baseline (regra 4 do CLAUDE.md) e aguarda aprovação da equipe no PR.

## Testes de API e de ponta a ponta (planejamento)

Issue #83. Esta seção **planeja**; não implementa. Nenhum código de teste é escrito antes de existir spec aprovada com interface (regra 1 do CLAUDE.md). Todo o plano está **condicionado à decisão de OPEN-01** (framework web) e, para o ambiente de execução, de OPEN-12 (hospedagem).

### Fluxos críticos candidatos a ponta a ponta

Poucos, como manda a pirâmide: só o que, se quebrar, impede o uso do produto. Cada um é testado de ponta a ponta uma vez, pelo caminho feliz; as variações ficam nos níveis de baixo.

| Fluxo | Caso de uso | Por que é crítico | Requisitos |
|---|---|---|---|
| Entrar no sistema e ver o painel do perfil | UC-01 | Sem entrar, nada funciona; falha de autenticação ou de painel afeta todos os perfis | RNF-01, RNF-17 |
| Elaborar um orçamento, aprovar e ver o título gerado | UC-04 | Gera o recebível, que é o centro do produto (RB-05) | RF-11, RF-19, RNF-16 |
| Registrar pagamento integral e ver o título Baixado | UC-06 | É o momento em que o dinheiro entra; erro aqui falseia o saldo | RF-25, RF-26, RNF-14, RNF-16 |

Fora do ponta a ponta de propósito: régua de cobrança (UC-08), por depender de tempo e do canal simulado, testada na aplicação com relógio injetado; importação CSV (UC-14), testada com arquivos de exemplo na aplicação.

### Testes de API (quando houver API)

| Verificação | Requisito |
|---|---|
| Toda rota, exceto o login, recusa requisição sem sessão | RNF-01 |
| Cada operação sensível recusa o perfil sem permissão, chamada direto na API | RNF-02, RNF-03 |
| Cliente não lê título de outro cliente pela API | RNF-25 |
| Entrada inválida devolve o campo e o motivo | RNF-14 |
| Requisição sem TLS é recusada ou redirecionada | RNF-05 |
| Resposta de consulta e cadastro em menos de 2 s no P95 | RNF-11 |

### Ferramentas candidatas

Comparação para subsidiar a decisão; **a escolha é da equipe** (OPEN-26). As informações são de conhecimento geral e devem ser conferidas na documentação oficial no momento da decisão.

| Uso | Candidata | Pontos a favor | Pontos contra |
|---|---|---|---|
| API | Postman com Newman (citadas na aula) | Coleções com interface gráfica; Newman roda no terminal e na integração contínua | Ferramenta externa ao repositório de código; coleções em JSON são difíceis de revisar em PR; exige Node.js |
| API | Testes em Python com a biblioteca padrão (`urllib`, `unittest`) | Sem dependência nova (RNF-23); versionado junto do código | Mais verboso; sem recursos prontos de coleção |
| API | Testes em Python com `requests` ou o cliente de teste do framework | Concisos; o cliente de teste do framework dispensa subir o servidor | Instala dependência (pergunta antes, CLAUDE.md); o cliente de teste depende da escolha de OPEN-01 |
| Navegador | Selenium (citado na aula) | Maduro; vários navegadores; documentação ampla | Esperas explícitas e testes mais frágeis; exige driver do navegador |
| Navegador | Playwright | Espera automática de elementos; Chromium já disponível neste ambiente de agente | Dependência nova; ecossistema menos conhecido pela equipe, a confirmar |
| Navegador | Cypress | Boa experiência de depuração | Exige Node.js; limitações com várias abas |

### Condições para sair do planejamento

1. OPEN-01 decidida e uma spec aprovada com interface (a primeira provavelmente é a Spec 001 ou a 002).
2. OPEN-26 decidida: ferramentas de API e de navegador.
3. Ambiente de execução definido (OPEN-12), com o canal de notificação e a IA simulados (RNF-23).
4. Os testes de ponta a ponta entram na integração contínua (OPEN-25) em etapa separada da suíte rápida, para não atrasar o retorno dos testes de unidade.

## Simuladores do canal de notificação e do serviço de IA

Issue #79. Dublês de teste para que a suíte rode sem credencial externa (RNF-23) e cubra os casos de borda. Lições: Nubank (2021), e-mails de encerramento de conta enviados por engano, e Taco Bell (2025), falhas de IA em casos de borda. **Ainda não há código**: a regra 1 do CLAUDE.md manda escrevê-lo junto da primeira spec aprovada que usar a porta (Specs 008, 009 e 011). O que esta seção fixa é o contrato que cada simulador deve cumprir.

Comum aos dois:

- Ficam em `src/remindme/infraestrutura/` e implementam a **mesma porta** que o adaptador real, declarada em `src/remindme/aplicacao/portas.py` (ADR-001, ADR-002, ADR-003). O domínio não os conhece.
- Não leem variável de ambiente nem abrem conexão. Os testes de arquitetura (`tests/arquitetura/`) já impedem o domínio de importar infraestrutura e exigem só a biblioteca padrão.
- Os testes que os usam ficam em `tests/` e passam em ambiente limpo, sem nenhuma variável de credencial (RNF-23).

| Simulador | Comportamento obrigatório | Critério que o exige |
|---|---|---|
| Canal de notificação | Registra cada mensagem "enviada" (destinatário, conteúdo, momento pelo relógio injetado) em uma lista que o teste consulta. Pode ser configurado para falhar. Nunca envia nada de verdade | RB-18, ADR-002; Specs 008 e 009 |
| Serviço de IA | Devolve a resposta configurada pelo teste: confiança abaixo, igual e acima do limiar; categoria inexistente no plano de contas; erro; tempo excedido (RNF-24). Guarda o payload recebido para o teste conferir que não há nome, documento nem contato (RNF-22) | RB-08, RB-14, RNF-22, RNF-24, RNF-26; Specs 009 e 011 |

Casos de teste que os simuladores habilitam, a escrever com as specs:

| Caso | Requisito |
|---|---|
| Mensagem da régua vai ao destinatário certo, com o conteúdo certo | RF-34, RF-71 |
| Falha do canal não repete etapa nem perde o registro de tentativa | DA-08 |
| Confiança exatamente igual ao limiar é aceita; um centésimo abaixo é decidida por pessoa | RB-08, RB-14, OPEN-05 |
| Categoria que não existe no plano de contas é recusada | RB-08 |
| Resposta de IA fora do prazo é tratada como falha | RNF-24 |
| Payload da IA não contém dado pessoal | RNF-22 |

## O que não pode faltar

| Assunto | Teste |
|---|---|
| Estados | Toda transição válida das [tabelas de estados](uml/estados.md) e ao menos uma transição inválida por entidade |
| Alçada | Desconto igual à alçada, um ponto acima e um ponto abaixo (RB-15) |
| Pagamento | Valor zero, negativo, igual ao saldo, maior que o saldo (RB-23) |
| Autorização | Cada perfil × cada operação sensível (RNF-02) |
| Isolamento do cliente | Cliente tenta acessar título de outro cliente (RNF-25) |
| Atomicidade | Falha injetada no meio de uma operação financeira (RNF-09) |
| IA | Confiança igual, acima e abaixo do limiar; categoria inexistente; falha; tempo excedido (RB-08, RB-14) |
| Régua | Execução repetida do agendador não repete etapa (DA-08) |
| Auditoria | Toda mudança de estado gera registro; tentativa de alteração é recusada (RB-01, RB-30) |

## Definição de pronto

Uma issue de implementação está pronta quando:

1. o código implementa a spec aprovada, sem comportamento além dela;
2. todos os critérios de aceite da spec têm teste passando;
3. a suíte inteira passa;
4. spec e código foram alterados no mesmo PR, quando o comportamento mudou;
5. o PR foi revisado por um colega e fecha a issue com `Closes #N`.

## Registro da verificação

A verificação de cada spec é registrada na seção 8 da própria spec, com um resultado por critério de aceite: passou, não passou ou não verificado (passo 6 do fluxo do [`CLAUDE.md`](../CLAUDE.md)). Critério que não puder ser automatizado é verificado manualmente e registrado no mesmo lugar.

A [matriz de critérios](qualidade/matriz-criterios-de-aceite.md) liga cada critério ao teste.

A suíte roda a cada PR e a cada push na `main` (`.github/workflows/testes.yml`), sem credencial externa. A ferramenta de integração contínua é provisória, até a decisão de OPEN-25. Como ler o resultado: [`execucao.md`](execucao.md).

## Ferramentas de teste

O executor é o `unittest` da biblioteca padrão e a cobertura não é medida. Se a equipe adotar pytest ou coverage.py, esta seção, o `CLAUDE.md` e `execucao.md` mudam no mesmo PR da decisão (OPEN-24).

## Rastreabilidade

Cláusula EARS → Issue → PR → commits → teste. A ligação é feita pelo identificador: ele aparece no título da issue, na descrição do PR e no nome do teste.
