"""Usabilidade: toda recusa informa o campo ou a condição e o motivo (RNF-14; Spec 006, seção 4).

Checklist e cenários em docs/qualidade/usabilidade.md.
"""

import unittest
from datetime import date, datetime, timedelta
from decimal import Decimal

from remindme.aplicacao.servico_titulos import FiltroTitulos, ServicoTitulos
from remindme.dominio.erros import OperacaoRecusada
from remindme.dominio.titulo import EstadoTitulo
from remindme.dominio.usuario import Perfil, Usuario
from remindme.infraestrutura.memoria import (
    AuditoriaEmMemoria,
    ClientesEmMemoria,
    RelogioFixo,
    RepositorioTitulosEmMemoria,
    UnidadeDeTrabalhoEmMemoria,
)
from tests.apoio import ComSessoes

HOJE = date(2026, 10, 3)
FUTURO = HOJE + timedelta(days=30)
DONO = Usuario("dono", "Dono", Perfil.DONO)
OPERADOR = Usuario("operador", "Operador", Perfil.OPERADOR_FINANCEIRO)


class Usabilidade(ComSessoes, unittest.TestCase):
    def setUp(self):
        self.uow = UnidadeDeTrabalhoEmMemoria(RepositorioTitulosEmMemoria(), AuditoriaEmMemoria())
        self.servico = ServicoTitulos(
            self.uow,
            ClientesEmMemoria({"c1"}),
            RelogioFixo(datetime(2026, 10, 3, 10, 0)),
        )

    def novo(self, valor="1000.00"):
        return self.servico.cadastrar_titulo(self.sessao(OPERADOR), "c1", Decimal(valor), FUTURO)

    def baixado(self):
        t = self.novo()
        return self.servico.registrar_pagamento(self.sessao(OPERADOR), t.id, Decimal("1000.00"), HOJE)

    def test_RNF_14_cada_recusa_informa_o_campo_ou_a_condicao(self):
        s = self.servico
        cenarios = [
            ("cadastro com valor zero", lambda: s.cadastrar_titulo(self.sessao(OPERADOR), "c1", Decimal("0"), FUTURO), "valor"),
            ("cadastro sem vencimento", lambda: s.cadastrar_titulo(self.sessao(OPERADOR), "c1", Decimal("1"), None), "vencimento"),
            ("cadastro com cliente inexistente", lambda: s.cadastrar_titulo(self.sessao(OPERADOR), "x", Decimal("1"), FUTURO), "cliente"),
            ("pagamento zero", lambda: s.registrar_pagamento(self.sessao(OPERADOR), self.novo().id, Decimal("0"), HOJE), "valor"),
            ("pagamento maior que o saldo", lambda: s.registrar_pagamento(self.sessao(OPERADOR), self.novo().id, Decimal("1000.01"), HOJE), "saldo"),
            ("pagamento em título Baixado", lambda: s.registrar_pagamento(self.sessao(OPERADOR), self.baixado().id, Decimal("1"), HOJE), "Baixado"),
            ("pagamento em título inexistente", lambda: s.registrar_pagamento(self.sessao(OPERADOR), "x", Decimal("1"), HOJE), "Título"),
            ("estorno pelo Operador Financeiro", lambda: s.estornar_pagamento(self.sessao(OPERADOR), "x", "p", "m", HOJE), "Dono"),
            ("estorno sem motivo", lambda: s.estornar_pagamento(self.sessao(DONO), self.baixado().id, "p", None, HOJE), "motivo"),
            ("estorno de pagamento inexistente", lambda: s.estornar_pagamento(self.sessao(DONO), self.baixado().id, "x", "m", HOJE), "Pagamento"),
            ("cancelamento pelo Operador Financeiro", lambda: s.cancelar_titulo(self.sessao(OPERADOR), "x", "m"), "Dono"),
            ("cancelamento sem motivo", lambda: s.cancelar_titulo(self.sessao(DONO), self.novo().id, " "), "motivo"),
            ("cancelamento de título Baixado", lambda: s.cancelar_titulo(self.sessao(DONO), self.baixado().id, "m"), "Estorne"),
        ]
        for nome, operacao, termo in cenarios:
            with self.subTest(cenario=nome):
                with self.assertRaises(OperacaoRecusada) as recusa:
                    operacao()
                self.assertIn(termo.lower(), recusa.exception.motivo.lower())
                self.assertEqual(recusa.exception.motivo, str(recusa.exception))

    def test_RNF_14_recusa_por_saldo_informa_o_saldo_disponivel(self):
        t = self.novo()
        self.servico.registrar_pagamento(self.sessao(OPERADOR), t.id, Decimal("400.00"), HOJE)
        with self.assertRaisesRegex(OperacaoRecusada, "600.00"):
            self.servico.registrar_pagamento(self.sessao(OPERADOR), t.id, Decimal("600.01"), HOJE)

    def test_RF_27_pagamento_parcial_devolve_o_saldo_restante(self):
        t = self.novo()
        resultado = self.servico.registrar_pagamento(self.sessao(OPERADOR), t.id, Decimal("250.00"), HOJE)
        self.assertEqual(resultado.saldo, Decimal("750.00"))

    def test_A6_consulta_apresenta_o_que_o_operador_precisa_para_decidir(self):
        self.novo()
        [visao] = self.servico.consultar_titulos(self.sessao(OPERADOR), FiltroTitulos(), HOJE, 5)
        for campo in ("valor", "saldo", "vencimento", "estado", "proximo_do_vencimento"):
            with self.subTest(campo=campo):
                self.assertTrue(hasattr(visao, campo))
        self.assertIs(visao.estado, EstadoTitulo.ABERTO)
        self.assertEqual(visao.estado.value, "Aberto")


if __name__ == "__main__":
    unittest.main()
