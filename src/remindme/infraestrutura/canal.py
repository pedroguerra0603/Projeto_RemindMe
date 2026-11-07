"""Canal de notificação simulado (ADR-002, RB-18, OPEN-62): a única implementação do canal.

Ele não entrega nada a ninguém: a mensagem fica na caixa de saída, gravada pelo serviço que a enviou.
"""


class CanalSimulado:
    def entregar(self, contato: str, assunto: str, texto: str) -> bool:
        return True
