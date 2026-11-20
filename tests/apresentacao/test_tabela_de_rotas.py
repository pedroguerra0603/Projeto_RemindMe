"""Tabela de rotas da interface web fixada antes da divisão de `aplicacao_web.py` por módulo (OPEN-65).

A refatoração não muda comportamento: as rotas, a ordem em que são testadas, a exigência de sessão e o
manipulador de cada uma continuam os mesmos. Uma rota nova entra aqui junto com a spec que a cria.
"""

import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path

from remindme.inicializacao import montar
from remindme.infraestrutura.memoria import RegistroErrosEmMemoria, RelogioFixo
from tests.apoio import CIFRADOR_DE_TESTE

ROTAS = [
    ('GET', '/', '_inicio', False),
    ('GET', '/favicon.ico', '_favicon', False),
    ('GET', '/estatico/(?P<nome>[a-z0-9.-]+)', '_estatico', False),
    ('GET', '/entrar', '_entrar_pagina', False),
    ('POST', '/entrar', '_entrar', False),
    ('GET', '/criar-conta', '_criar_conta_pagina', False),
    ('POST', '/criar-conta', '_criar_conta', False),
    ('GET', '/robots.txt', '_robots', False),
    ('POST', '/sair', '_sair', True),
    ('GET', '/trocar-senha', '_trocar_senha_pagina', True),
    ('POST', '/trocar-senha', '_trocar_senha', True),
    ('GET', '/painel', '_painel', True),
    ('GET', '/clientes', '_clientes', True),
    ('GET', '/clientes/novo', '_cliente_novo_pagina', True),
    ('POST', '/clientes/novo', '_cliente_novo', True),
    ('GET', '/clientes/(?P<cliente_id>[0-9a-f]{32})', '_cliente', True),
    ('GET', '/clientes/(?P<cliente_id>[0-9a-f]{32})/editar', '_cliente_editar_pagina', True),
    ('POST', '/clientes/(?P<cliente_id>[0-9a-f]{32})/editar', '_cliente_editar', True),
    ('GET', '/titulos', '_titulos', True),
    ('GET', '/titulos/novo', '_titulo_novo_pagina', True),
    ('POST', '/titulos/novo', '_titulo_novo', True),
    ('POST', '/titulos/verificar-vencimentos', '_verificar_vencimentos', True),
    ('GET', '/titulos/(?P<titulo_id>[0-9a-f]{32})', '_titulo', True),
    ('POST', '/titulos/(?P<titulo_id>[0-9a-f]{32})/pagamentos', '_pagamento', True),
    ('GET', '/titulos/(?P<titulo_id>[0-9a-f]{32})/pagamentos/(?P<pagamento_id>[0-9a-f]{32})/estorno', '_estorno_pagina', True),
    ('POST', '/titulos/(?P<titulo_id>[0-9a-f]{32})/pagamentos/(?P<pagamento_id>[0-9a-f]{32})/estorno', '_estorno', True),
    ('GET', '/titulos/(?P<titulo_id>[0-9a-f]{32})/cancelamento', '_cancelamento_pagina', True),
    ('POST', '/titulos/(?P<titulo_id>[0-9a-f]{32})/cancelamento', '_cancelamento', True),
    ('GET', '/orcamentos', '_orcamentos', True),
    ('GET', '/orcamentos/novo', '_orcamento_novo_pagina', True),
    ('POST', '/orcamentos/novo', '_orcamento_novo', True),
    ('GET', '/orcamentos/(?P<orcamento_id>[0-9a-f]{32})', '_orcamento', True),
    ('POST', '/orcamentos/(?P<orcamento_id>[0-9a-f]{32})/itens', '_item_novo', True),
    ('GET', '/orcamentos/(?P<orcamento_id>[0-9a-f]{32})/itens/(?P<item_id>[0-9a-f]{32})', '_item_pagina', True),
    ('POST', '/orcamentos/(?P<orcamento_id>[0-9a-f]{32})/itens/(?P<item_id>[0-9a-f]{32})', '_item_alterar', True),
    ('POST', '/orcamentos/(?P<orcamento_id>[0-9a-f]{32})/itens/(?P<item_id>[0-9a-f]{32})/remocao', '_item_remover', True),
    ('POST', '/orcamentos/(?P<orcamento_id>[0-9a-f]{32})/desconto', '_desconto', True),
    ('POST', '/orcamentos/(?P<orcamento_id>[0-9a-f]{32})/condicao', '_condicao', True),
    ('POST', '/orcamentos/(?P<orcamento_id>[0-9a-f]{32})/decisao', '_decisao', True),
    ('POST', '/orcamentos/(?P<orcamento_id>[0-9a-f]{32})/envio', '_envio', True),
    ('POST', '/orcamentos/(?P<orcamento_id>[0-9a-f]{32})/resposta-do-cliente', '_resposta_do_cliente', True),
    ('GET', '/mensagens', '_mensagens', True),
    ('GET', '/orcamentos/(?P<orcamento_id>[0-9a-f]{32})/cancelamento', '_orcamento_cancelamento_pagina', True),
    ('POST', '/orcamentos/(?P<orcamento_id>[0-9a-f]{32})/cancelamento', '_orcamento_cancelamento', True),
    ('GET', '/fornecedores', '_fornecedores', True),
    ('GET', '/fornecedores/novo', '_fornecedor_novo_pagina', True),
    ('POST', '/fornecedores/novo', '_fornecedor_novo', True),
    ('GET', '/fornecedores/(?P<fornecedor_id>[0-9a-f]{32})', '_fornecedor', True),
    ('GET', '/fornecedores/(?P<fornecedor_id>[0-9a-f]{32})/editar', '_fornecedor_editar_pagina', True),
    ('POST', '/fornecedores/(?P<fornecedor_id>[0-9a-f]{32})/editar', '_fornecedor_editar', True),
    ('GET', '/contas-a-pagar', '_contas', True),
    ('GET', '/contas-a-pagar/nova', '_conta_nova_pagina', True),
    ('POST', '/contas-a-pagar/nova', '_conta_nova', True),
    ('GET', '/contas-a-pagar/(?P<conta_id>[0-9a-f]{32})', '_conta', True),
    ('POST', '/contas-a-pagar/(?P<conta_id>[0-9a-f]{32})/pagamentos', '_conta_pagamento', True),
    ('GET', '/contas-a-pagar/(?P<conta_id>[0-9a-f]{32})/pagamentos/(?P<pagamento_id>[0-9a-f]{32})/estorno', '_conta_estorno_pagina', True),
    ('POST', '/contas-a-pagar/(?P<conta_id>[0-9a-f]{32})/pagamentos/(?P<pagamento_id>[0-9a-f]{32})/estorno', '_conta_estorno', True),
    ('GET', '/contas-a-pagar/(?P<conta_id>[0-9a-f]{32})/cancelamento', '_conta_cancelamento_pagina', True),
    ('POST', '/contas-a-pagar/(?P<conta_id>[0-9a-f]{32})/cancelamento', '_conta_cancelamento', True),
    ('GET', '/obrigacoes', '_obrigacoes', True),
    ('GET', '/obrigacoes/nova', '_obrigacao_nova_pagina', True),
    ('POST', '/obrigacoes/nova', '_obrigacao_nova', True),
    ('GET', '/obrigacoes/(?P<obrigacao_id>[0-9a-f]{32})', '_obrigacao', True),
    ('POST', '/obrigacoes/(?P<obrigacao_id>[0-9a-f]{32})/prazo', '_obrigacao_prazo', True),
    ('POST', '/obrigacoes/(?P<obrigacao_id>[0-9a-f]{32})/responsavel', '_obrigacao_responsavel', True),
    ('POST', '/obrigacoes/(?P<obrigacao_id>[0-9a-f]{32})/cumprimento', '_obrigacao_cumprimento', True),
    ('POST', '/obrigacoes/(?P<obrigacao_id>[0-9a-f]{32})/evidencias', '_obrigacao_evidencia', True),
    ('GET', '/obrigacoes/(?P<obrigacao_id>[0-9a-f]{32})/evidencias/(?P<evidencia_id>[0-9a-f]{32})', '_evidencia', True),
    ('GET', '/empresa', '_empresa', True),
    ('POST', '/empresa', '_empresa_salvar', True),
    ('GET', '/auditoria', '_auditoria', True),
    ('GET', '/usuarios', '_usuarios', True),
    ('GET', '/usuarios/novo', '_usuario_novo_pagina', True),
    ('POST', '/usuarios/novo', '_usuario_novo', True),
    ('GET', '/usuarios/(?P<usuario_id>[0-9a-f]{32})', '_usuario', True),
    ('POST', '/usuarios/(?P<usuario_id>[0-9a-f]{32})/perfil', '_usuario_perfil', True),
    ('POST', '/usuarios/(?P<usuario_id>[0-9a-f]{32})/inativacao', '_usuario_inativacao', True),
    ('POST', '/usuarios/(?P<usuario_id>[0-9a-f]{32})/ativacao', '_usuario_ativacao', True),
    ('GET', '/permissoes', '_permissoes', True),
    ('POST', '/permissoes', '_permissao', True),
]


class TabelaDeRotas(unittest.TestCase):
    def test_OPEN_65_a_tabela_de_rotas_nao_muda_com_a_refatoracao(self):
        with tempfile.TemporaryDirectory() as pasta:
            relogio = RelogioFixo(datetime(2026, 11, 19, 15, 0, tzinfo=timezone.utc))
            sistema = montar(str(Path(pasta, "remindme.db")), relogio, CIFRADOR_DE_TESTE, RegistroErrosEmMemoria())
            atual = [(m, p.pattern, f.__name__, protegida) for m, p, f, protegida in sistema.web._rotas]
        self.assertEqual(atual, ROTAS)


if __name__ == "__main__":
    unittest.main()
