"""Integração entre os componentes da Spec 006: serviço, unidade de trabalho, repositórios, auditoria,
relógio e consulta de clientes.

Ainda não há banco, API nem serviço externo (OPEN-01, OPEN-02). `ContratoRepositorioTitulos` descreve o
que qualquer implementação de `RepositorioTitulos` deve cumprir; quando houver banco, basta criar uma
subclasse que devolva o repositório real.
"""

import unittest
from datetime import date, datetime, timedelta
from decimal import Decimal

from remindme.aplicacao.servico_titulos import FiltroTitulos, ServicoTitulos
from remindme.dominio.erros import OperacaoRecusada
from remindme.dominio.titulo import EstadoTitulo, Titulo
from remindme.dominio.usuario import Perfil, Usuario
from remindme.infraestrutura.memoria import (
    AuditoriaEmMemoria,
    ClientesEmMemoria,
    RelogioFixo,
    RepositorioTitulosEmMemoria,
    UnidadeDeTrabalhoEmMemoria,
)

HOJE = date(2026, 10, 3)
DONO = Usuario("dono", "Dono", Perfil.DONO)
OPERADOR = Usuario("operador", "Operador", Perfil.OPERADOR_FINANCEIRO)


class ContratoRepositorioTitulos:
    """Contrato da interface `RepositorioTitulos` (aplicacao/portas.py)."""

    def criar_repositorio(self):
        raise NotImplementedError

    def titulo(self, id):
        return Titulo.cadastrar_manual(id, "c1", Decimal("100.00"), HOJE)

    def test_contrato_salva_e_obtem_com_todos_os_dados(self):
        repositorio = self.criar_repositorio()
        t = self.titulo("t1")
        t.registrar_pagamento("p1", Decimal("40.00"), HOJE)
        t.estornar_pagamento("p1", "devolvido", HOJE)
        repositorio.salvar(t)
        obtido = repositorio.obter("t1")
        self.assertEqual(obtido, t)
        self.assertEqual(obtido.pagamentos[0].motivo_estorno, "devolvido")

    def test_contrato_obter_inexistente_devolve_nada(self):
        self.assertIsNone(self.criar_repositorio().obter("inexistente"))

    def test_contrato_listar_devolve_cada_titulo_uma_vez(self):
        repositorio = self.criar_repositorio()
        for id in ("t1", "t2", "t1"):
            repositorio.salvar(self.titulo(id))
        self.assertEqual(sorted(t.id for t in repositorio.listar()), ["t1", "t2"])

    def test_contrato_alteracao_sem_salvar_nao_persiste(self):
        repositorio = self.criar_repositorio()
        repositorio.salvar(self.titulo("t1"))
        repositorio.obter("t1").cancelar("motivo")
        self.assertIs(repositorio.obter("t1").estado, EstadoTitulo.ABERTO)


class RepositorioEmMemoriaCumpreOContrato(ContratoRepositorioTitulos, unittest.TestCase):
    def criar_repositorio(self):
        return RepositorioTitulosEmMemoria()


class ServicoComInfraestrutura(unittest.TestCase):
    def setUp(self):
        self.titulos = RepositorioTitulosEmMemoria()
        self.auditoria = AuditoriaEmMemoria()
        self.clientes = ClientesEmMemoria({"c1"})
        self.relogio = RelogioFixo(datetime(2026, 10, 3, 9, 0))
        self.servico = self.novo_servico()

    def novo_servico(self):
        return ServicoTitulos(
            UnidadeDeTrabalhoEmMemoria(self.titulos, self.auditoria), self.clientes, self.relogio
        )

    def avancar(self, minutos):
        self.relogio.momento += timedelta(minutes=minutos)

    def test_UC_06_ciclo_completo_grava_estado_e_trilha_de_auditoria(self):
        s = self.servico
        t = s.cadastrar_titulo(OPERADOR, "c1", Decimal("1000.00"), HOJE - timedelta(days=5))
        self.avancar(1)
        s.registrar_pagamento(OPERADOR, t.id, Decimal("300.00"), HOJE)
        self.avancar(1)
        self.assertEqual(s.verificar_vencimentos(OPERADOR, HOJE), [t.id])
        self.avancar(1)
        t = s.registrar_pagamento(OPERADOR, t.id, Decimal("700.00"), HOJE)
        segundo = t.pagamentos[1].id
        self.avancar(1)
        s.estornar_pagamento(DONO, t.id, segundo, "cheque devolvido", HOJE)
        self.avancar(1)
        s.cancelar_titulo(DONO, t.id, "acordo comercial")

        salvo = self.titulos.obter(t.id)
        self.assertIs(salvo.estado, EstadoTitulo.CANCELADO)
        self.assertEqual(salvo.saldo, Decimal("700.00"))
        self.assertEqual(salvo.valor, Decimal("1000.00"))

        trilha = [
            (r.data_hora.minute, r.usuario_id, r.operacao, r.valor_anterior, r.valor_novo, r.motivo)
            for r in self.auditoria.registros
        ]
        self.assertEqual(
            trilha,
            [
                (0, "operador", "cadastrar título", None, "Aberto", None),
                (1, "operador", "registrar pagamento", None, f"pagamento {salvo.pagamentos[0].id}: 300.00", None),
                (2, "operador", "mudar estado", "Aberto", "Vencido", None),
                (3, "operador", "registrar pagamento", None, f"pagamento {segundo}: 700.00", None),
                (3, "operador", "mudar estado", "Vencido", "Baixado", None),
                (4, "dono", "estornar pagamento", f"pagamento {segundo}", "estornado", "cheque devolvido"),
                (4, "dono", "mudar estado", "Baixado", "Vencido", "cheque devolvido"),
                (5, "dono", "mudar estado", "Vencido", "Cancelado", "acordo comercial"),
            ],
        )
        self.assertTrue(all(r.registro_afetado == f"titulo {t.id}" for r in self.auditoria.registros))

    def test_dois_servicos_sobre_o_mesmo_armazenamento_veem_as_mesmas_gravacoes(self):
        outro = self.novo_servico()
        t = self.servico.cadastrar_titulo(OPERADOR, "c1", Decimal("100.00"), HOJE)
        outro.registrar_pagamento(OPERADOR, t.id, Decimal("100.00"), HOJE)
        [visao] = self.servico.consultar_titulos(FiltroTitulos(), HOJE, 5)
        self.assertIs(visao.estado, EstadoTitulo.BAIXADO)
        with self.assertRaises(OperacaoRecusada):
            self.servico.registrar_pagamento(OPERADOR, t.id, Decimal("1.00"), HOJE)

    def test_consulta_de_clientes_e_feita_a_cada_cadastro(self):
        self.servico.cadastrar_titulo(OPERADOR, "c1", Decimal("100.00"), HOJE)
        self.clientes.ids.discard("c1")
        with self.assertRaisesRegex(OperacaoRecusada, "Cliente"):
            self.servico.cadastrar_titulo(OPERADOR, "c1", Decimal("100.00"), HOJE)
        self.clientes.ids.add("c2")
        self.servico.cadastrar_titulo(OPERADOR, "c2", Decimal("100.00"), HOJE)
        self.assertEqual(len(self.titulos.listar()), 2)

    def test_recusa_nao_grava_auditoria(self):
        t = self.servico.cadastrar_titulo(OPERADOR, "c1", Decimal("100.00"), HOJE)
        antes = list(self.auditoria.registros)
        for operacao in (
            lambda: self.servico.registrar_pagamento(OPERADOR, t.id, Decimal("100.01"), HOJE),
            lambda: self.servico.cancelar_titulo(OPERADOR, t.id, "motivo"),
            lambda: self.servico.cancelar_titulo(DONO, t.id, ""),
            lambda: self.servico.cadastrar_titulo(OPERADOR, "c1", Decimal("0"), HOJE),
        ):
            with self.subTest(), self.assertRaises(OperacaoRecusada):
                operacao()
        self.assertEqual(self.auditoria.registros, antes)

    def test_verificacao_de_vencimentos_sem_mudanca_nao_grava(self):
        self.servico.cadastrar_titulo(OPERADOR, "c1", Decimal("100.00"), HOJE + timedelta(days=1))
        antes = list(self.auditoria.registros)
        self.assertEqual(self.servico.verificar_vencimentos(OPERADOR, HOJE), [])
        self.assertEqual(self.auditoria.registros, antes)


if __name__ == "__main__":
    unittest.main()
