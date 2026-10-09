"""Cenários de erro e exceção: entradas inválidas, referências inexistentes e situações inesperadas.

Regra da Spec 006 (seção 4): toda recusa informa o motivo e não altera nenhum dado.
Catálogo dos cenários e defeitos encontrados em docs/qualidade/excecoes.md.
"""

import copy
import unittest
from datetime import date, datetime, timedelta
from decimal import Decimal

from remindme.aplicacao.servico_titulos import ServicoTitulos
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
FUTURO = HOJE + timedelta(days=30)
DONO = Usuario("dono", "Dono", Perfil.DONO)
OPERADOR = Usuario("operador", "Operador", Perfil.OPERADOR_FINANCEIRO)

VALORES_INVALIDOS = {
    "NaN": Decimal("NaN"),
    "sNaN": Decimal("sNaN"),
    "infinito": Decimal("Infinity"),
    "float": 100.0,
    "texto": "100.00",
    "nada": None,
}


def titulo():
    return Titulo.cadastrar_manual("t1", "c1", Decimal("100.00"), FUTURO)


class ReferenciasInexistentes(unittest.TestCase):
    def setUp(self):
        self.titulos = RepositorioTitulosEmMemoria()
        self.auditoria = AuditoriaEmMemoria()
        self.servico = ServicoTitulos(
            UnidadeDeTrabalhoEmMemoria(self.titulos, self.auditoria),
            ClientesEmMemoria({"c1"}),
            RelogioFixo(datetime(2026, 10, 3, 10, 0)),
        )

    def test_titulo_inexistente_e_recusado_em_toda_operacao(self):
        for nome, operacao in {
            "pagamento": lambda: self.servico.registrar_pagamento(OPERADOR, "x", Decimal("1"), HOJE),
            "estorno": lambda: self.servico.estornar_pagamento(DONO, "x", "p", "motivo", HOJE),
            "cancelamento": lambda: self.servico.cancelar_titulo(DONO, "x", "motivo"),
        }.items():
            with self.subTest(operacao=nome):
                with self.assertRaisesRegex(OperacaoRecusada, "Título não encontrado"):
                    operacao()
        self.assertEqual(self.auditoria.registros, [])

    def test_E5_pagamento_de_outro_titulo_nao_e_estornado(self):
        a = self.servico.cadastrar_titulo(OPERADOR, "c1", Decimal("100.00"), FUTURO)
        b = self.servico.cadastrar_titulo(OPERADOR, "c1", Decimal("100.00"), FUTURO)
        a = self.servico.registrar_pagamento(OPERADOR, a.id, Decimal("10.00"), HOJE)
        with self.assertRaisesRegex(OperacaoRecusada, "Pagamento não encontrado"):
            self.servico.estornar_pagamento(DONO, b.id, a.pagamentos[0].id, "motivo", HOJE)
        self.assertFalse(self.titulos.obter(a.id).pagamentos[0].estornado)

    def test_E7_cliente_vazio_e_recusado(self):
        for cliente in ("", None):
            with self.subTest(cliente=cliente), self.assertRaises(OperacaoRecusada):
                self.servico.cadastrar_titulo(OPERADOR, cliente, Decimal("1.00"), FUTURO)


class ValoresInvalidos(unittest.TestCase):
    """E1 e E7: valor que não é um número decimal finito é recusado, com motivo, sem alterar dados."""

    def assertRecusaSemAlterar(self, t, operacao):
        antes = copy.deepcopy(t)
        with self.assertRaises(OperacaoRecusada) as recusa:
            operacao()
        self.assertTrue(recusa.exception.motivo)
        self.assertEqual(t, antes)

    @unittest.expectedFailure  # D-01, D-02, D-04 em docs/qualidade/excecoes.md
    def test_E7_cadastro_com_valor_invalido_e_recusado(self):
        for nome, valor in VALORES_INVALIDOS.items():
            with self.subTest(valor=nome), self.assertRaises(OperacaoRecusada):
                Titulo.cadastrar_manual("t1", "c1", valor, FUTURO)

    @unittest.expectedFailure  # D-01, D-03, D-04
    def test_E1_pagamento_com_valor_invalido_e_recusado_sem_alterar_o_titulo(self):
        for nome, valor in VALORES_INVALIDOS.items():
            with self.subTest(valor=nome):
                t = titulo()
                self.assertRecusaSemAlterar(t, lambda: t.registrar_pagamento("p1", valor, HOJE))

    @unittest.expectedFailure  # D-05
    def test_E4_motivo_que_nao_e_texto_e_recusado(self):
        for motivo in (123, ["motivo"]):
            with self.subTest(motivo=motivo):
                t = titulo()
                self.assertRecusaSemAlterar(t, lambda: t.cancelar(motivo))

    def test_E4_motivo_so_com_espacos_e_quebras_de_linha_e_recusado(self):
        t = titulo()
        t.registrar_pagamento("p1", Decimal("10.00"), HOJE)
        for motivo in (" ", "\n\t"):
            with self.subTest(motivo=repr(motivo)):
                self.assertRecusaSemAlterar(t, lambda: t.estornar_pagamento("p1", motivo, HOJE))
                self.assertRecusaSemAlterar(t, lambda: t.cancelar(motivo))

    def test_E1_valor_com_mais_de_duas_casas_e_aceito_ate_decisao_de_OPEN_20(self):
        """Comportamento atual, sem regra na baseline: registrado como OPEN-20."""
        t = titulo()
        t.registrar_pagamento("p1", Decimal("0.001"), HOJE)
        self.assertEqual(t.saldo, Decimal("99.999"))

    def test_E1_valor_alto_nao_perde_precisao(self):
        t = Titulo.cadastrar_manual("t1", "c1", Decimal("123456789012.34"), FUTURO)
        t.registrar_pagamento("p1", Decimal("123456789012.33"), HOJE)
        self.assertEqual(t.saldo, Decimal("0.01"))
        t.registrar_pagamento("p2", Decimal("0.01"), HOJE)
        self.assertIs(t.estado, EstadoTitulo.BAIXADO)


class DatasInesperadas(unittest.TestCase):
    def test_OPEN_17_pagamento_com_data_futura_e_aceito_ate_a_decisao(self):
        t = titulo()
        t.registrar_pagamento("p1", Decimal("10.00"), HOJE + timedelta(days=365))
        self.assertEqual(t.saldo, Decimal("90.00"))

    def test_RF_24_verificacao_com_data_anterior_nao_desfaz_vencimento(self):
        t = Titulo.cadastrar_manual("t1", "c1", Decimal("100.00"), HOJE)
        t.marcar_vencido(HOJE + timedelta(days=1))
        self.assertFalse(t.marcar_vencido(HOJE - timedelta(days=10)))
        self.assertIs(t.estado, EstadoTitulo.VENCIDO)


if __name__ == "__main__":
    unittest.main()
