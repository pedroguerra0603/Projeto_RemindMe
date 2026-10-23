"""Apoio comum aos testes que chamam os serviços: sessões abertas direto no dublê, sem passar pelo login.

Os testes da Spec 002 entram pelo login de verdade; os demais só precisam de uma sessão válida (INV-2).
"""

from dataclasses import replace
from datetime import datetime

from remindme.aplicacao.acesso import nova_sessao
from remindme.aplicacao.senhas import CifradorScrypt

# Custo baixo de `scrypt` para a suíte ficar rápida; a aplicação usa o custo padrão (OPEN-33).
CIFRADOR_DE_TESTE = CifradorScrypt(n=2**4)


def abrir_sessao(uow, usuario) -> str:
    """Cadastra o usuário no dublê, se preciso, e devolve o identificador de uma sessão sem vencimento."""
    if uow.usuarios.obter(usuario.id) is None:
        uow.usuarios.salvar(usuario)
    identificador, sessao = nova_sessao(usuario.id, datetime(2000, 1, 1))
    uow.sessoes.salvar(replace(sessao, expira_em=datetime.max))
    return identificador


class ComSessoes:
    """Mistura para `unittest.TestCase`: `self.sessao(usuario)` abre uma sessão na unidade `self.uow`."""

    def sessao(self, usuario) -> str:
        return abrir_sessao(self.uow, usuario)
