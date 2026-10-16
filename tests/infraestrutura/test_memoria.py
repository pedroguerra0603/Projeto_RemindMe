"""Testes unitários das implementações em memória das interfaces da aplicação."""

import unittest
from datetime import date, datetime
from decimal import Decimal

from remindme.aplicacao.portas import RegistroErro
from remindme.dominio.auditoria import RegistroAuditoria
from remindme.dominio.titulo import EstadoTitulo, Titulo
from remindme.infraestrutura.memoria import (
    AuditoriaEmMemoria,
    ClientesEmMemoria,
    RegistroErrosEmMemoria,
    RelogioFixo,
    RepositorioTitulosEmMemoria,
    UnidadeDeTrabalhoEmMemoria,
)


def titulo(id="t1"):
    return Titulo.cadastrar_manual(id, "c1", Decimal("100.00"), date(2026, 10, 10))


class RepositorioDeTitulos(unittest.TestCase):
    def setUp(self):
        self.repositorio = RepositorioTitulosEmMemoria()

    def test_obter_titulo_inexistente_devolve_nada(self):
        self.assertIsNone(self.repositorio.obter("x"))

    def test_salvar_e_obter_devolvem_copias(self):
        original = titulo()
        self.repositorio.salvar(original)
        original.estado = EstadoTitulo.CANCELADO
        obtido = self.repositorio.obter("t1")
        self.assertIs(obtido.estado, EstadoTitulo.ABERTO)
        obtido.estado = EstadoTitulo.BAIXADO
        self.assertIs(self.repositorio.obter("t1").estado, EstadoTitulo.ABERTO)

    def test_salvar_de_novo_substitui(self):
        t = titulo()
        self.repositorio.salvar(t)
        t.cancelar("motivo")
        self.repositorio.salvar(t)
        self.assertEqual(len(self.repositorio.listar()), 1)
        self.assertIs(self.repositorio.obter("t1").estado, EstadoTitulo.CANCELADO)

    def test_listar_devolve_todos_como_copias(self):
        self.repositorio.salvar(titulo("t1"))
        self.repositorio.salvar(titulo("t2"))
        listados = self.repositorio.listar()
        self.assertEqual(sorted(t.id for t in listados), ["t1", "t2"])
        listados[0].estado = EstadoTitulo.CANCELADO
        self.assertTrue(all(t.estado is EstadoTitulo.ABERTO for t in self.repositorio.listar()))


class Auditoria(unittest.TestCase):
    def test_ADR_004_registros_sao_acrescentados_em_ordem(self):
        auditoria = AuditoriaEmMemoria()
        r1 = RegistroAuditoria("u", datetime(2026, 10, 3), "a", "titulo t1")
        r2 = RegistroAuditoria("u", datetime(2026, 10, 3), "b", "titulo t1")
        auditoria.registrar(r1)
        auditoria.registrar(r2)
        self.assertEqual(auditoria.registros, [r1, r2])

    def test_falha_simulada_nao_grava(self):
        auditoria = AuditoriaEmMemoria()
        auditoria.falhar = True
        with self.assertRaises(RuntimeError):
            auditoria.registrar(RegistroAuditoria("u", datetime(2026, 10, 3), "a", "x"))
        self.assertEqual(auditoria.registros, [])

    def test_RB_30_so_grava_registro_de_auditoria(self):
        auditoria = AuditoriaEmMemoria()
        with self.assertRaises(TypeError):
            auditoria.registrar({"operacao": "a"})
        self.assertEqual(auditoria.registros, [])

    def test_RB_30_leitura_devolve_copias_em_lista_nova(self):
        auditoria = AuditoriaEmMemoria()
        r1 = RegistroAuditoria("u", datetime(2026, 10, 3), "a", "titulo t1")
        auditoria.registrar(r1)
        lida = auditoria.registros
        self.assertIsNot(lida, auditoria.registros)
        self.assertIsNot(lida[0], r1)
        lida.append(r1)
        self.assertEqual(auditoria.registros, [r1])


class RegistroErros(unittest.TestCase):
    def test_RNF_21_registros_de_erro_sao_acrescentados_em_ordem(self):
        erros = RegistroErrosEmMemoria()
        e1 = RegistroErro(datetime(2026, 10, 16), "a", "u", "c1", "RuntimeError: x")
        e2 = RegistroErro(datetime(2026, 10, 16), "b", None, "c2", "RuntimeError: y")
        erros.registrar(e1)
        erros.registrar(e2)
        self.assertEqual(erros.registros, [e1, e2])


class UnidadeDeTrabalho(unittest.TestCase):
    def setUp(self):
        self.titulos = RepositorioTitulosEmMemoria()
        self.auditoria = AuditoriaEmMemoria()
        self.uow = UnidadeDeTrabalhoEmMemoria(self.titulos, self.auditoria)

    def test_RNF_09_sem_falha_mantem_as_alteracoes(self):
        with self.uow as uow:
            uow.titulos.salvar(titulo())
        self.assertIsNotNone(self.titulos.obter("t1"))

    def test_RNF_09_falha_desfaz_titulos_e_auditoria(self):
        with self.assertRaises(ValueError):
            with self.uow as uow:
                uow.titulos.salvar(titulo())
                uow.auditoria.registrar(RegistroAuditoria("u", datetime(2026, 10, 3), "a", "x"))
                raise ValueError("falha")
        self.assertIsNone(self.titulos.obter("t1"))
        self.assertEqual(self.auditoria.registros, [])

    def test_RNF_09_falha_desfaz_so_os_registros_da_transacao(self):
        """Spec 001, E3: registro de auditoria gravado e depois falha na gravação; o anterior permanece."""
        anterior = RegistroAuditoria("u", datetime(2026, 10, 3), "anterior", "titulo t0")
        with self.uow as uow:
            uow.auditoria.registrar(anterior)
        with self.assertRaises(ValueError):
            with self.uow as uow:
                uow.auditoria.registrar(RegistroAuditoria("u", datetime(2026, 10, 3), "a", "titulo t1"))
                uow.titulos.salvar(titulo())
                raise ValueError("falha na gravação do título")
        self.assertEqual(self.auditoria.registros, [anterior])
        self.assertIsNone(self.titulos.obter("t1"))

    def test_RNF_09_falha_nao_e_engolida(self):
        with self.assertRaisesRegex(ValueError, "original"):
            with self.uow:
                raise ValueError("original")


class ClientesERelogio(unittest.TestCase):
    def test_clientes_existentes(self):
        ids = {"c1"}
        clientes = ClientesEmMemoria(ids)
        ids.add("c2")
        self.assertTrue(clientes.existe("c1"))
        self.assertFalse(clientes.existe("c2"))

    def test_relogio_fixo(self):
        momento = datetime(2026, 10, 3, 10, 0)
        self.assertEqual(RelogioFixo(momento).agora(), momento)


if __name__ == "__main__":
    unittest.main()
