"""Testes unitários das implementações em memória das interfaces da aplicação."""

import unittest
from datetime import date, datetime
from decimal import Decimal

from remindme.dominio.auditoria import RegistroAuditoria
from remindme.dominio.titulo import EstadoTitulo, Titulo
from remindme.infraestrutura.memoria import (
    AuditoriaEmMemoria,
    ClientesEmMemoria,
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


class Mensagens(unittest.TestCase):
    """Spec 005: a caixa de saída participa da transação (RNF-09)."""

    def mensagem(self, id="m1"):
        from remindme.aplicacao.portas import Mensagem

        return Mensagem(id, "c1", "a@b.com", "Assunto", "Texto", datetime(2026, 11, 7, 12, 0), "enviada", "orcamento o1")

    def test_mensagens_registradas_e_listadas_em_ordem(self):
        from remindme.infraestrutura.memoria import UnidadeDeTrabalhoEmMemoria

        uow = UnidadeDeTrabalhoEmMemoria()
        with uow:
            uow.mensagens.registrar(self.mensagem("m1"))
            uow.mensagens.registrar(self.mensagem("m2"))
        self.assertEqual([m.id for m in uow.mensagens.listar()], ["m1", "m2"])

    def test_mensagens_sao_desfeitas_com_a_transacao(self):
        from remindme.infraestrutura.memoria import UnidadeDeTrabalhoEmMemoria

        uow = UnidadeDeTrabalhoEmMemoria()
        with self.assertRaises(RuntimeError):
            with uow:
                uow.mensagens.registrar(self.mensagem())
                raise RuntimeError("falha depois de registrar")
        self.assertEqual(uow.mensagens.listar(), [])


class Obrigacoes(unittest.TestCase):
    """Spec 010: obrigações e o conteúdo das evidências participam da transação (RNF-09)."""

    def obrigacao(self, id="o1"):
        from remindme.dominio.obrigacao import Obrigacao
        from remindme.dominio.usuario import Perfil, Usuario

        operador = Usuario("operador", "Diego Ramos", Perfil.OPERADOR_FINANCEIRO, "d@demo.example")
        agora = datetime(2026, 11, 20, 9, 0)
        return Obrigacao.cadastrar(id, "DAS", "Fiscal", "Mensal", date(2026, 12, 20), operador, False, agora.date(), "operador", agora)

    def test_mensagem_aceita_usuario_como_destinatario(self):
        from remindme.aplicacao.portas import Mensagem

        uow = UnidadeDeTrabalhoEmMemoria()
        with uow:
            uow.mensagens.registrar(
                Mensagem("m1", None, "d@demo.example", "A", "T", datetime(2026, 11, 20, 9, 0), "enviada", "obrigacao o1", "u1")
            )
        self.assertEqual([(m.cliente_id, m.usuario_id) for m in uow.mensagens.listar()], [(None, "u1")])

    def test_obrigacao_e_conteudo_gravados_e_devolvidos_como_copias(self):
        uow = UnidadeDeTrabalhoEmMemoria()
        with uow:
            uow.obrigacoes.salvar(self.obrigacao())
            uow.obrigacoes.guardar_conteudo("e1", b"%PDF-1.4")
        lida = uow.obrigacoes.obter("o1")
        lida.nome = "outro"
        self.assertEqual(uow.obrigacoes.obter("o1").nome, "DAS")
        self.assertEqual([o.id for o in uow.obrigacoes.listar()], ["o1"])
        self.assertEqual(uow.obrigacoes.conteudo_de("e1"), b"%PDF-1.4")
        self.assertIsNone(uow.obrigacoes.conteudo_de("e2"))
        self.assertIsNone(uow.obrigacoes.obter("o2"))

    def test_RNF_09_obrigacoes_em_memoria_desfazem_com_a_transacao(self):
        uow = UnidadeDeTrabalhoEmMemoria()
        with self.assertRaises(RuntimeError):
            with uow:
                uow.obrigacoes.salvar(self.obrigacao())
                uow.obrigacoes.guardar_conteudo("e1", b"%PDF-1.4")
                raise RuntimeError("falha depois de gravar")
        self.assertEqual(uow.obrigacoes.listar(), [])
        self.assertIsNone(uow.obrigacoes.conteudo_de("e1"))


if __name__ == "__main__":
    unittest.main()
