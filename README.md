# Projeto_RemindMe

# Fluxo

Sistema de gestão do ciclo de recebíveis e obrigações para micro e pequenas empresas.

Projeto Final da disciplina de Modelagem de Software · Semestre 2026-2 · Turma 04I

---

## Sobre o projeto

Empresas de pequeno porte raramente têm um back-office. Na prática, o dono acumula vendas, cobrança e administração, e terceiriza a contabilidade para um escritório que entrega o mínimo obrigatório, sem acompanhar a operação do dia a dia. O resultado é sempre o mesmo: orçamento aprovado que nunca virou fatura, título vencido que ninguém cobrou, prazo perdido porque não existia calendário, e um resultado financeiro que ninguém apura porque os lançamentos estão classificados de qualquer jeito.

O problema não é falta de sistema contábil — é falta de rotina com regra. Falta algo que garanta que cada cobrança e cada obrigação avancem no prazo certo, com registro de quem fez o quê e por quê.

O **Fluxo** foi pensado para ocupar exatamente esse espaço. Ele acompanha o dinheiro que a empresa tem a receber do começo ao fim: o orçamento é criado e enviado ao cliente, aprovado dentro das alçadas de desconto, convertido em título, cobrado por uma sequência automática de lembretes, renegociado quando necessário e finalmente baixado. Cada passo é uma mudança de estado explícita, registrada e reversível apenas por quem tem permissão para isso.

Em torno desse núcleo, o sistema mantém duas frentes de apoio. A primeira é o calendário de obrigações, que concentra os compromissos fiscais e contratuais recorrentes da empresa, avisa com antecedência, cobra a evidência de cumprimento e escala o alerta para o dono quando o prazo estoura. A segunda é a apuração do resultado, montada a partir dos próprios lançamentos que o ciclo de cobrança já gerou — o que significa que a demonstração de resultado deixa de ser um relatório que chega meses depois e passa a ser um reflexo direto da operação.

## Perfis e interesses

O sistema atende quatro perfis com interesses que nem sempre coincidem, e é justamente aí que ele agrega valor: o dono, que responde pelas exceções e pelos alertas escalonados; o operador financeiro, que toca a rotina diária dentro dos limites que lhe foram dados; o cliente, que acompanha seus títulos e pode propor renegociação; e o contador, que consome o resultado consolidado em modo de leitura. A empresa quer receber rápido, o cliente quer prazo, o contador quer classificação correta. O Fluxo arbitra essas tensões por regra, não por conversa.

## O papel da inteligência artificial

O sistema usa um modelo de linguagem em dois pontos bem delimitados, sempre sob o mesmo princípio: **o modelo extrai e classifica, o sistema decide.**

No primeiro, o modelo lê a descrição de um lançamento financeiro e sugere em qual conta ele se encaixa, junto com um grau de confiança. O sistema valida essa sugestão contra o plano de contas da empresa e só a aceita automaticamente quando a confiança é alta; abaixo disso, o lançamento vai para uma fila de revisão humana e fica de fora da apuração até alguém confirmar. No segundo, o modelo lê uma mensagem recebida do cliente e extrai dela a intenção, o título mencionado, o valor e a data prometida — dados estruturados que o sistema então processa por regra, respondendo por template.

Nenhum número financeiro é produzido por inteligência artificial, e nenhuma saída do modelo chega ao cliente como texto livre. Toda vez que uma pessoa corrige uma sugestão, a divergência fica registrada, o que dá ao grupo uma medida concreta da qualidade da classificação ao longo do tempo.

## Escopo

O projeto foi deliberadamente recortado para caber no semestre sem virar uma coleção de módulos rasos. Ele não emite nota fiscal — registra a obrigação de emitir e guarda a evidência, mas fica fora da integração com SEFAZ, que exigiria certificado digital e homologação. Também não cobre folha de pagamento nem rotinas de RH, que formam um domínio inteiro e independente, e não faz recomendação de investimento, que seria opinião disfarçada de regra.

A integração com WhatsApp e com planilhas, que motivou a ideia original, aparece de uma forma mais interessante do ponto de vista de arquitetura: o canal de notificação é uma peça substituível do sistema, com uma implementação simulada como padrão. Isso permite que o MVP inteiro — e toda a suíte de testes — rode sem nenhuma credencial externa, e deixa a porta aberta para plugar um canal real como diferencial. A troca de dados com planilhas acontece por importação e exportação de CSV, que entrega o mesmo valor prático com uma fração do risco.

## Documentação

A especificação do sistema é a fonte de verdade do projeto e vive em [`.specify/spec.md`](.specify/spec.md), acompanhada do plano técnico e das tarefas derivadas dela. As decisões de arquitetura estão registradas em [`docs/adr/`](docs/adr/), e o restante da documentação — glossário do domínio, estratégia de testes, considerações de segurança e achados de revisão — está em [`docs/`](docs/).

## Como executar

As instruções de instalação e execução estão em [`docs/execucao.md`](docs/execucao.md).

## Equipe

| Integrante |Tarefas|
|---|---|
| *João Pedro Silva Guerra* | |
| *Bernardo Sanches* | |
| *Renan Ribeiro Gandolpho* | | 

Professor: Nilton Mack · `niltonmack@mackenzie.br`
