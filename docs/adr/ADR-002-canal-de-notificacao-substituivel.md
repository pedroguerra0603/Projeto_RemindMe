# ADR-002 — Canal de notificação substituível, simulado por padrão

- **Situação:** Proposto, aguardando aprovação da equipe
- **Data:** 2026-10-03
- **Decisores:** a definir pela equipe
- **Drivers:** DA-07
- **Requisitos e regras:** RB-18, RF-71, RNF-23

## Contexto

A ideia original do projeto era cobrar por WhatsApp. Integrar um canal real exige conta comercial, credenciais e aprovação de modelos de mensagem, e tornaria os testes dependentes de um serviço externo.

O que o sistema decide é quando e o que cobrar. O meio de entrega é intercambiável.

## Decisão

O sistema envia orçamentos, cobranças e alertas por uma interface de canal de notificação. A implementação padrão é um canal simulado, que registra a mensagem em vez de enviá-la. Um canal real, como o WhatsApp, é outra implementação da mesma interface, habilitada por configuração.

## Alternativas consideradas

| Alternativa | Por que não |
|---|---|
| Integrar o WhatsApp diretamente | Testes passariam a exigir credencial; risco de prazo. |
| Enviar somente por e-mail | Resolve a credencial em parte, mas mantém o acoplamento a um único canal. |

## Consequências

- Positivas: o MVP e toda a suíte de testes rodam sem credencial externa; novos canais não alteram o domínio.
- Negativas: o MVP não entrega mensagens reais ao cliente.
- O que passa a ser obrigatório: nenhum código fora da infraestrutura conhece um canal específico; o resultado de cada envio é registrado como tentativa de cobrança.
