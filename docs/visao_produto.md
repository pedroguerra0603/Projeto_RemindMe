# Visão do Produto: RemindMe

## 1. O Problema: A Ausência de Back-Office em Pequenas Empresas
No contexto das micro e pequenas empresas, a gestão financeira e administrativa frequentemente sofre com a falta de um back-office estruturado. Na prática, o proprietário acumula funções operacionais, táticas e estratégicas — como vendas, cobranças e gestão geral. Paralelamente, a contabilidade costuma ser terceirizada para escritórios que entregam apenas o mínimo obrigatório exigido pela legislação, sem acompanhar a rotina e o fluxo de caixa em tempo real.

O resultado dessa desconexão é um ciclo vicioso de falhas operacionais:
* Orçamentos aprovados que nunca são convertidos em faturas.
* Títulos vencidos que não recebem o devido acompanhamento de cobrança.
* Prazos fiscais e contratuais perdidos por ausência de um calendário centralizado.
* Resultados financeiros obscuros, gerados por lançamentos classificados de forma arbitrária ou incorreta.

A raiz do problema não está na ausência de um sistema contábil complexo, mas sim na falta de uma **rotina amparada por regras de negócio sistêmicas**. Falta um mecanismo que garanta que cada obrigação e recebível avance no prazo correto, mantendo o registro de rastreabilidade (quem fez, o que fez e quando fez).

## 2. A Solução: Gestão Ativa do Ciclo de Recebíveis e Obrigações
O **RemindMe** (anteriormente concebido como Fluxo) foi arquitetado para ocupar a lacuna entre a operação diária e a contabilidade final. Ele atua como o motor de regras que acompanha o fluxo financeiro de ponta a ponta. 

O sistema transforma processos informais em mudanças de estado explícitas, registradas e controladas por permissões. O ciclo de vida do dinheiro é tratado com rigor: o orçamento é gerado, enviado, aprovado dentro de alçadas pré-definidas, convertido em título a receber, cobrado por réguas automáticas de relacionamento, renegociado (se necessário) e, por fim, baixado.

### 2.1. Frentes de Apoio do Sistema
Em torno do núcleo de recebíveis, o RemindMe opera com dois pilares de apoio fundamentais:
* **Calendário de Obrigações:** Um concentrador de compromissos fiscais e contratuais recorrentes. O sistema age proativamente avisando sobre prazos, exigindo a anexação de evidências de cumprimento e escalonando alertas para a diretoria quando os limites de tempo são rompidos.
* **Apuração de Resultado em Tempo Real:** Uma DRE (Demonstração do Resultado do Exercício) dinâmica, montada a partir dos próprios lançamentos gerados pelo ciclo de cobrança. O relatório financeiro deixa de ser um documento póstumo de meses anteriores e passa a ser o reflexo exato da operação diária.

## 3. Perfis, Tensões e Resolução de Conflitos
O ecossistema do RemindMe atende a quatro perfis de usuários primários. Como seus interesses frequentemente entram em conflito (ex: a empresa quer receber rápido, o cliente quer diluir prazos, o contador exige precisão classificatória), o sistema atua como o árbitro dessas tensões por meio de regras estritas, não de negociações informais.

* **O Dono:** Focado na saúde do negócio. Intervém apenas no tratamento de exceções, aprovações fora de alçada e responde aos alertas escalonados de quebras de prazo.
* **O Operador Financeiro:** Focado na execução. Toca a rotina diária de validações e cobranças, operando estritamente dentro dos limites e alçadas que lhe foram delegados.
* **O Cliente:** Focado em flexibilidade. Consome a visualização de seus títulos pendentes, recebe os lembretes automáticos e tem um canal para propor termos de renegociação.
* **O Contador:** Focado em conformidade. Consome os resultados financeiros consolidados e a classificação dos lançamentos em modo de leitura (Read-Only) para exportação ou conciliação.

## 4. O Papel e os Limites da Inteligência Artificial
A integração de modelos de linguagem (LLMs) no RemindMe segue um princípio arquitetural imutável: **O modelo extrai e classifica; o sistema decide.** 
Nenhum dado financeiro é inventado pela IA e nenhuma saída bruta do modelo é enviada como texto livre para o cliente final. A inteligência atua em dois domínios delimitados:

1. **Classificação Inteligente de Lançamentos:** O modelo analisa a descrição textual de um lançamento e sugere o enquadramento no plano de contas da empresa, anexando um "grau de confiança". O sistema aprova automaticamente apenas scores altos. Sugestões de baixa confiança são enviadas para uma fila de revisão humana. A correção humana alimenta métricas de qualidade.
2. **Processamento de Intenções de Renegociação:** O modelo atua sobre as respostas enviadas por clientes, extraindo dados estruturados de intenção (título alvo, valor proposto e data da promessa). Com o dado estruturado em mãos, o sistema processa a aprovação ou recusa utilizando regras e templates pré-aprovados.

## 5. Delimitação de Escopo (O que o sistema NÃO faz)
Para garantir a entrega de um MVP (Minimum Viable Product) funcional e robusto, o projeto estabelece limites claros de atuação, evitando domínios paralelos que diluiriam o valor central:
* **Não emite Nota Fiscal Eletrônica (NFe):** O sistema registra o dever de emissão e guarda a evidência, mas exclui a integração direta com a SEFAZ para evitar dependência de certificados digitais e homologações morosas.
* **Não gerencia Folha de Pagamento ou RH:** Rotinas trabalhistas constituem um domínio à parte e não fazem parte do MVP.
* **Não atua como Conselheiro Financeiro:** O sistema não emite recomendações de investimentos ou cortes de gastos.
* **Integrações Externas Simuladas:** A comunicação por canais de mensageria (ex: WhatsApp) é arquitetada através de portas substituíveis com implementações simuladas. Isso permite que toda a suíte de testes do projeto rode sem dependência de APIs terceiras, deixando a arquitetura pronta para plugar o canal real no futuro. A interoperabilidade com planilhas se dá via importação/exportação padronizada de arquivos CSV.