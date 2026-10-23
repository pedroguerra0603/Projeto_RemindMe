"""Datas na camada de aplicação: verificação de vencimentos, hora da auditoria e filtro por período.
Issue #77. As regras de data do domínio estão em tests/dominio/test_datas.py.
Catálogo em docs/qualidade/datas-e-fuso.md.
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
OPERADOR = Usuario("operador", "Operador", Perfil.OPERADOR_FINANCEIRO)


class DatasNaAplicacao(ComSessoes, unittest.TestCase):
    def setUp(self):
        self.titulos = RepositorioTitulosEmMemoria()
        self.auditoria = AuditoriaEmMemoria()
        self.relogio = RelogioFixo(datetime(2026, 10, 3, 23, 59, 59))
        self.uow = UnidadeDeTrabalhoEmMemoria(self.titulos, self.auditoria)
        self.servico = ServicoTitulos(
            self.uow,
            ClientesEmMemoria({"c1"}),
            self.relogio,
        )

    def test_RF_24_verificacao_de_vencimentos_na_borda_do_dia_afeta_so_o_que_venceu(self):
        hoje = self.servico.cadastrar_titulo(self.sessao(OPERADOR), "c1", Decimal("10.00"), HOJE)
        ontem = self.servico.cadastrar_titulo(self.sessao(OPERADOR), "c1", Decimal("10.00"), HOJE - timedelta(days=1))
        vencidos = self.servico.verificar_vencimentos(self.sessao(OPERADOR), HOJE)
        self.assertEqual(vencidos, [ontem.id])
        self.assertIs(self.titulos.obter(hoje.id).estado, EstadoTitulo.ABERTO)

    def test_RF_62_a_hora_do_registro_de_auditoria_vem_do_relogio_injetado(self):
        self.servico.cadastrar_titulo(self.sessao(OPERADOR), "c1", Decimal("10.00"), HOJE)
        self.relogio.momento = datetime(2026, 10, 4, 0, 0, 1)
        self.servico.cadastrar_titulo(self.sessao(OPERADOR), "c1", Decimal("10.00"), HOJE)
        self.assertEqual(
            [r.data_hora for r in self.auditoria.registros],
            [datetime(2026, 10, 3, 23, 59, 59), datetime(2026, 10, 4, 0, 0, 1)],
        )

    def test_OPEN_17_o_servico_recusa_pagamento_com_data_posterior_ao_dia_do_relogio(self):
        t = self.servico.cadastrar_titulo(self.sessao(OPERADOR), "c1", Decimal("10.00"), HOJE)
        antes = self.auditoria.registros
        with self.assertRaisesRegex(OperacaoRecusada, "posterior a hoje"):
            self.servico.registrar_pagamento(self.sessao(OPERADOR), t.id, Decimal("10.00"), HOJE + timedelta(days=1))
        self.assertEqual(self.auditoria.registros, antes)
        self.servico.registrar_pagamento(self.sessao(OPERADOR), t.id, Decimal("10.00"), HOJE)
        self.assertIs(self.titulos.obter(t.id).estado, EstadoTitulo.BAIXADO)

    def test_RF_22_filtro_de_periodo_inclui_os_dois_extremos(self):
        for dias in (-1, 0, 1, 2):
            self.servico.cadastrar_titulo(self.sessao(OPERADOR), "c1", Decimal("10.00"), HOJE + timedelta(days=dias))
        filtro = FiltroTitulos(vencimento_de=HOJE, vencimento_ate=HOJE + timedelta(days=1))
        vencimentos = sorted(v.vencimento for v in self.servico.consultar_titulos(self.sessao(OPERADOR), filtro, HOJE, 5))
        self.assertEqual(vencimentos, [HOJE, HOJE + timedelta(days=1)])

    def test_RF_20_cadastro_sem_vencimento_e_recusado(self):
        with self.assertRaises(OperacaoRecusada):
            self.servico.cadastrar_titulo(self.sessao(OPERADOR), "c1", Decimal("10.00"), None)


if __name__ == "__main__":
    unittest.main()
