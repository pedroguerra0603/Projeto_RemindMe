# Visão de Produto - RemindMe (Fluxo)

## 1. Visão do Produto

O **RemindMe** (nome do projeto), é uma plataforma de gestão do ciclo de recebíveis e obrigações que substitui processos manuais e desorganizados de pequenas empresas por rotinas automáticas, auditáveis e orientadas por regra.

**Propósito:**  
Garantir que cada cobrança e cada obrigação avancem no prazo certo, com registro completo de quem fez o quê, por quê e quando, transformando a operação financeira de micro e pequenas empresas de algo caótico em algo previsível e mensurável.

---

## 2. O Problema

### Contexto
Empresas de pequeno porte raramente possuem um back-office estruturado. O dono acumula as funções de vendas, cobrança e administração, terceirizando apenas a contabilidade para um escritório que entrega o mínimo obrigatório.

### Sintomas
- Orçamentos aprovados que nunca viram fatura
- Títulos vencidos que ninguém cobrou
- Prazos perdidos porque não existe calendário de compromissos
- Resultado financeiro desconhecido porque os lançamentos estão classificados de forma inconsistente
- Falta de rastreabilidade: ninguém sabe quem fez o quê, quando e por quê
- Contador que chega meses depois com um relatório desconectado da operação

### Raiz
O problema não é falta de sistema contábil, mas falta de **rotina com regra** — processos com sequência clara, prioridades automáticas, alertas escalonados e uma auditoria nativa.

---

## 3. A Solução

### Núcleo: Ciclo de Recebíveis
O sistema acompanha o dinheiro que a empresa tem a receber do começo ao fim, passando por estados explícitos e controlados:

1. **Orçamento** criado e enviado ao cliente
2. **Aprovação** dentro das alçadas de desconto definidas
3. **Conversão** em título (documento de cobrança)
4. **Sequência de lembretes** automáticos ao cliente
5. **Renegociação** quando necessária, com rastro completo
6. **Baixa** quando recebido ou cancelado

Cada mudança de estado é **registrada, reversível apenas por autorizado, e explícita** — não há ambiguidade sobre o que aconteceu.

### Frente 1: Calendário de Obrigações
Concentra compromissos fiscais e contratuais recorrentes da empresa:
- Avisa com antecedência sobre vencimentos
- Cobra a evidência de cumprimento
- Escala o alerta para o dono quando o prazo estoura
- Mantém histórico de cumprimento

### Frente 2: Resultado em Tempo Real
A apuração é montada a partir dos próprios lançamentos que o ciclo de cobrança gera:
- Deixa de ser um relatório que chega meses depois
- Vira um reflexo direto e contínuo da operação
- Sempre consistente com os registros de cobrança

---

## 4. Perfis de Usuário e Interesses

| Perfil | Interesse Principal | Responsabilidade |
|--------|-------------------|------------------|
| **Dono** | Alertas críticos e exceções | Responder pelos desvios; autorizar operações fora da rotina |
| **Operador Financeiro** | Rotina diária; produtividade | Executar o fluxo dentro dos limites dados; cumprir sequência |
| **Cliente** | Transparência; prazo negociado | Acompanhar seus títulos; propor renegociação |
| **Contador** | Dados estruturados e auditáveis | Validar classificação; consolidar para fisco e gestão |

### Tensões Arbitradas por Regra
- Empresa quer receber rápido ↔ Cliente quer prazo  
- Operador quer rapidez ↔ Dono quer controle  
- Sistema quer padronização ↔ Negócio quer flexibilidade  

O Fluxo resolve essas tensões por **regra automática**, não por conversa informal.

---

## 5. Funcionalidades Principais

### 5.1 Gestão de Recebíveis
- [ ] Criar, aprovar e controlar orçamentos
- [ ] Converter orçamentos em títulos
- [ ] Sequência automática de lembretes
- [ ] Registro de tentativas de cobrança
- [ ] Negociação e renegociação de prazos
- [ ] Baixa de títulos (recebido, cancelado, prejuízo)
- [ ] Relatório de faturamento vs. recebimento

### 5.2 Calendário de Obrigações
- [ ] Registro de compromissos fiscais e contratuais
- [ ] Alertas com antecedência configurável
- [ ] Gestão de evidências de cumprimento
- [ ] Escalonamento de alertas não cumpridos
- [ ] Histórico de cumprimento

### 5.3 Apuração de Resultado
- [ ] Dashboard com resultado em tempo real
- [ ] Demonstração de resultado integrada aos lançamentos
- [ ] Rastreabilidade de cada linha de receita
- [ ] Exportação para contador/gestor

### 5.4 Auditoria e Controle
- [ ] Log completo de mudanças de estado
- [ ] Reversibilidade controlada por permissão
- [ ] Histórico de quem fez o quê e quando
- [ ] Rastreamento de divergências

---

## 6. O Papel da Inteligência Artificial

O sistema usa um modelo de linguagem em **dois pontos bem delimitados**, seguindo o princípio:  
**O modelo extrai e classifica; o sistema decide.**

### Ponto 1: Classificação de Lançamentos
- O modelo lê a descrição de um lançamento financeiro
- Sugere a conta contábil apropriada com grau de confiança
- Se confiança alta → aceita automaticamente
- Se confiança baixa → envia para fila de revisão humana (não entra na apuração até confirmação)
- Toda correção fica registrada para medir qualidade ao longo do tempo

### Ponto 2: Extração de Intenção de Cliente
- O modelo lê mensagem recebida do cliente
- Extrai: intenção, título mencionado, valor, data prometida
- Transforma em dados estruturados
- Sistema processa por regra e responde por template (nunca texto livre da IA)

### Garantias
- ✅ Nenhum número financeiro é produzido por IA
- ✅ Nenhuma saída de IA chega ao cliente como texto livre
- ✅ Auditoria sobre qualidade das sugestões do modelo

---

## 7. Diferencial Competitivo

| Aspecto | Diferencial |
|--------|-----------|
| **Automatização** | Rotina segue regra, não depende de lembrete manual do dono |
| **Rastreabilidade** | Cada mudança é registrada, auditável, reversível |
| **Decisão descentralizada** | Operador executa dentro de alçada; exceção escala pro dono |
| **Integração nativa** | Resultado financeiro é subproduto direto da operação, não relatório paralelo |
| **Inteligência auxiliar** | IA recomenda; sistema decide; pessoa confirma — não há "caixa preta" |
| **Canal plug-and-play** | Notificação por WhatsApp/SMS/Email é um módulo substituível |

---

## 8. Escopo do MVP

### Incluso
✅ Ciclo completo de recebíveis (orçamento → cobrança → baixa)  
✅ Calendário de obrigações com alertas  
✅ Apuração de resultado em tempo real  
✅ Auditoria completa  
✅ Classificação com IA (sem emissão de NF)  
✅ Canais de notificação simulados (pronto para plugar real)  
✅ Importação/exportação CSV  

### Fora do Escopo (v2+)
❌ Emissão de Nota Fiscal (integração SEFAZ)  
❌ Folha de Pagamento e RH  
❌ Recomendação de Investimento  
❌ Integração direta com WhatsApp Business (arquitetura preparada, implementação futura)  

**Justificativa:** Manter o escopo focado, viável em um semestre, sem perder valor para o usuário final.

---

## 9. Métricas de Sucesso

| Métrica | Meta | Medição |
|---------|------|---------|
| **Prazo de cobrança** | Reduzir em 30% | Dias médios entre fatura e recebimento |
| **Taxa de títulos cobrados** | Aumentar para 95%+ | % títulos com baixa vs. total |
| **Consistência contábil** | 100% | Divergências corrigidas / total de lançamentos |
| **Tempo de apuração** | Diário (não mensal) | Resultado disponível T+1 |
| **Confiança nas alçadas** | Aceitar 100% dos vencimentos | Operator não precisa escalar para aprovações rotineiras |

---

## 10. Roadmap de Fases

### Fase 1 (MVP - Semestre 2026-2)
- Ciclo de recebíveis completo
- Calendário de obrigações
- Apuração de resultado
- Classificação com IA (básica)
- Testes automatizados

### Fase 2 (v1.1)
- Integração com canal de notificação real (WhatsApp/SMS)
- Relatórios gerenciais avançados
- Mobile para operador

### Fase 3 (v2.0)
- Emissão de NF integrada com SEFAZ
- Previsão de fluxo de caixa
- Recomendação de priorização de cobrança

---

## 11. Público-Alvo

**Persona Principal:**  
Pequeno empresário (faturamento R$ 500k - R$ 5M/ano) que hoje usa planilhas desorganizadas ou nenhuma ferramenta estruturada, quer crescer sem contratar CFO, e precisar saber em tempo real quanto vai receber.

**Personas Secundárias:**
- Operador/Gerente de Cobrança em empresa pequena
- Contador que quer cliente usando sistema que gera dados estruturados
- Cliente final que quer saber o status de seu pedido/título

---

## 12. Premissas e Riscos

### Premissas
1. Empresa tem clientes recorrentes e ciclo de recebimento previsível
2. Dono está disposto a mudar processo manual para automatizado
3. Classificação contábil da empresa é passível de ser regras (não totalmente idiossincrática)

### Riscos
| Risco | Impacto | Mitigação |
|-------|--------|----------|
| Resistência do dono em usar sistema novo | Alto | Ganho em visibilidade + alertas; não restringe ação |
| IA classifica errado repetidamente | Médio | Revisão humana obrigatória + feedback ao modelo |
| Integração com SEFAZ atrasa | Médio | MVP não emite NF; fila de revisão suficiente |
| Dados confusos no histórico | Alto | Limpeza inicial + validação na importação CSV |

---

## 13. Considerações de Design

- **Simplicidade Visual:** Interface focada em fluxo, não em formulários complexos
- **Mobile First:** Operador precisa de acesso rápido em campo
- **Auditoria Invisível:** Log completo, mas não sobrecarrega UI
- **Regra Clara:** Não há exceção que não passe por regra e autorização
- **Feedback Imediato:** Operador sabe se ação foi aceita ou foi pra fila

---

## Documento Preparado Por

**Projeto:** RemindMe (Fluxo)  
**Disciplina:** Modelagem de Software · 2026-2 · Turma 04I  
**Data:** Semestre 2026-2

**Equipe:**
- João Pedro Silva Guerra
- Bernardo Sanches
- Renan Ribeiro Gandolpho

**Professor:** Nilton Mack (niltonmack@mackenzie.br)

---

## Referências Internas

- Especificação completa: [`.specify/spec.md`]
- Arquitetura: [`docs/adr/`]
- Instruções de execução: [`docs/execucao.md`]
- Documentação geral: [`docs/`]
