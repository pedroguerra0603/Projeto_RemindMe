"""Persistência em SQLite: contrato do repositório, transação e auditoria somente inclusão."""

import sqlite3
import unittest
from datetime import datetime

from remindme.dominio.auditoria import RegistroAuditoria
from remindme.infraestrutura.sqlite import BancoSQLite, RepositorioTitulosSQLite, UnidadeDeTrabalhoSQLite
from tests.integracao.test_integracao import ContratoRepositorioTitulos


class RepositorioSQLiteCumpreOContrato(ContratoRepositorioTitulos, unittest.TestCase):
    def criar_repositorio(self):
        return RepositorioTitulosSQLite(BancoSQLite())


def registro():
    return RegistroAuditoria("u1", datetime(2026, 10, 20, 9), "cadastrar título", "titulo t1")


class Auditoria(unittest.TestCase):
    def setUp(self):
        self.banco = BancoSQLite()
        self.uow = UnidadeDeTrabalhoSQLite(self.banco)
        with self.uow as uow:
            uow.auditoria.registrar(registro())

    def test_RNF_06_banco_recusa_alterar_e_excluir_auditoria(self):
        for sql in ("UPDATE auditoria SET operacao = 'x'", "DELETE FROM auditoria"):
            with self.subTest(sql=sql), self.assertRaises(sqlite3.DatabaseError):
                self.banco.conexao.execute(sql)
        self.assertEqual(self.uow.auditoria.registros, [registro()])

    def test_RNF_09_erro_no_bloco_desfaz_tudo(self):
        with self.assertRaises(RuntimeError):
            with self.uow as uow:
                uow.auditoria.registrar(registro())
                raise RuntimeError("falha")
        self.assertEqual(len(self.uow.auditoria.registros), 1)

    def test_dados_sobrevivem_a_reabertura_do_arquivo(self):
        import os
        import tempfile

        pasta = tempfile.mkdtemp()
        caminho = os.path.join(pasta, "teste.db")
        banco = BancoSQLite(caminho)
        with UnidadeDeTrabalhoSQLite(banco) as uow:
            uow.auditoria.registrar(registro())
        banco.fechar()
        reaberto = BancoSQLite(caminho)
        self.assertEqual(UnidadeDeTrabalhoSQLite(reaberto).auditoria.registros, [registro()])
        reaberto.fechar()


if __name__ == "__main__":
    unittest.main()
