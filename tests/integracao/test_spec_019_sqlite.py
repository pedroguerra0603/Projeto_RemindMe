"""Spec 019 com SQLite real: a troca de senha persiste e é atômica (CA-19, RNF-09, INV-4)."""

import sqlite3
import tempfile
import unittest
from contextlib import closing
from datetime import datetime, timezone
from pathlib import Path
from unittest import mock

from remindme.aplicacao.servico_acesso import ServicoAcesso
from remindme.dominio.erros import OperacaoRecusada
from remindme.dominio.usuario import Perfil
from remindme.infraestrutura.memoria import RelogioFixo
from remindme.infraestrutura.sqlite import UnidadeDeTrabalhoSQLite, preparar_banco
from tests.apoio import CIFRADOR_DE_TESTE

ANTIGA = "senha-antiga-1"
NOVA = "senha-nova-123"


class Spec019Persistencia(unittest.TestCase):
    def setUp(self):
        self._pasta = tempfile.TemporaryDirectory()
        self.addCleanup(self._pasta.cleanup)
        self.caminho = str(Path(self._pasta.name) / "remindme.db")
        preparar_banco(self.caminho)

    def montar(self):
        relogio = RelogioFixo(datetime(2026, 11, 6, 12, 0, tzinfo=timezone.utc))
        uow = UnidadeDeTrabalhoSQLite(self.caminho)
        return uow, ServicoAcesso(uow, relogio, cifrador=CIFRADOR_DE_TESTE)

    def sql(self, comando, parametros=()):
        with closing(sqlite3.connect(self.caminho)) as conexao:
            return conexao.execute(comando, parametros).fetchall()

    def preparar_usuario(self):
        uow, acesso = self.montar()
        acesso.criar_primeiro_administrador("Admin", "admin@exemplo.com", "senha-admin-1")
        admin = acesso.entrar("admin@exemplo.com", "senha-admin-1").identificador
        diego = acesso.cadastrar_usuario(admin, "Diego", "diego@exemplo.com", Perfil.OPERADOR_FINANCEIRO, ANTIGA)
        outra = acesso.entrar("diego@exemplo.com", ANTIGA).identificador
        sessao = acesso.entrar("diego@exemplo.com", ANTIGA).identificador
        return uow, acesso, diego, sessao, outra

    def hash_no_banco(self, usuario_id):
        return self.sql("SELECT hash_da_senha FROM usuarios WHERE id = ?", (usuario_id,))

    def test_CA_19_troca_persiste_depois_de_reabrir_o_banco(self):
        _, acesso, diego, sessao, _ = self.preparar_usuario()
        acesso.trocar_senha(sessao, ANTIGA, NOVA, NOVA)

        _, acesso = self.montar()
        self.assertEqual(self.sql("SELECT COUNT(*) FROM sessoes WHERE usuario_id = ?", (diego.id,)), [(1,)])
        with self.assertRaises(OperacaoRecusada):
            acesso.entrar("diego@exemplo.com", ANTIGA)
        self.assertTrue(acesso.entrar("diego@exemplo.com", NOVA).identificador)

    def test_RNF_09_INV_4_falha_na_auditoria_desfaz_no_banco(self):
        uow, acesso, diego, sessao, _ = self.preparar_usuario()
        hash_antes = self.hash_no_banco(diego.id)
        sessoes_antes = self.sql("SELECT COUNT(*) FROM sessoes WHERE usuario_id = ?", (diego.id,))
        with mock.patch.object(uow.auditoria, "registrar", side_effect=RuntimeError):
            with self.assertRaises(RuntimeError):
                acesso.trocar_senha(sessao, ANTIGA, NOVA, NOVA)
        self.assertEqual(self.hash_no_banco(diego.id), hash_antes)
        self.assertEqual(self.sql("SELECT COUNT(*) FROM sessoes WHERE usuario_id = ?", (diego.id,)), sessoes_antes)


if __name__ == "__main__":
    unittest.main()
