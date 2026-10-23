"""Critérios de aceitação da Spec 013: consulta de auditoria (UC-12, RF-64)."""

import unittest
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal

from remindme.aplicacao.servico_auditoria import RESPONSAVEL_SISTEMA, FiltroAuditoria, ServicoAuditoria
from remindme.aplicacao.servico_titulos import ServicoTitulos
from remindme.dominio.erros import OperacaoNegada, OperacaoRecusada
from remindme.dominio.usuario import Perfil, Usuario
from remindme.infraestrutura.memoria import ClientesEmMemoria, RelogioFixo, UnidadeDeTrabalhoEmMemoria
from tests.apoio import ComSessoes

HOJE = date(2026, 10, 3)
DONO = Usuario("dono", "Carla Menezes", Perfil.DONO)
OPERADOR = Usuario("operador", "Diego Ramos", Perfil.OPERADOR_FINANCEIRO)
CONTADOR = Usuario("contador", "Helena Prado", Perfil.CONTADOR)
ADMIN = Usuario("admin", "Administração", Perfil.ADMINISTRADOR)


class Base(ComSessoes, unittest.TestCase):
    def setUp(self):
        self.uow = UnidadeDeTrabalhoEmMemoria()
        self.relogio = RelogioFixo(datetime(2026, 10, 3, 9, 0))
        self.titulos = ServicoTitulos(self.uow, ClientesEmMemoria({"c1", "c2"}), self.relogio)
        self.auditoria = ServicoAuditoria(self.uow, self.relogio)
        self.dono, self.operador = self.sessao(DONO), self.sessao(OPERADOR)

    def consultar(self, sessao=None, **filtro):
        return self.auditoria.consultar(sessao or self.dono, FiltroAuditoria(**filtro))


class Spec013(Base):
    def test_CA_01_INV_1_consulta_sem_filtro_em_ordem_cronologica_com_o_nome_do_responsavel(self):
        t = self.titulos.cadastrar_titulo(self.operador, "c1", Decimal("100.00"), HOJE)
        self.relogio.momento += timedelta(minutes=5)
        self.titulos.cancelar_titulo(self.dono, t.id, "desistência")
        visoes = self.consultar()
        self.assertEqual(
            [(v.responsavel, v.data_hora.minute, v.operacao, v.registro_afetado) for v in visoes],
            [
                ("Diego Ramos", 0, "cadastrar título", f"titulo {t.id}"),
                ("Carla Menezes", 5, "mudar estado", f"titulo {t.id}"),
            ],
        )

    def test_CA_02_filtro_por_usuario(self):
        self.titulos.cadastrar_titulo(self.operador, "c1", Decimal("100.00"), HOJE)
        self.titulos.cadastrar_titulo(self.dono, "c2", Decimal("200.00"), HOJE)
        self.assertEqual({v.responsavel for v in self.consultar(usuario_id=DONO.id)}, {"Carla Menezes"})

    def test_CA_03_OPEN_26_filtro_por_periodo_pela_data_do_fuso_de_referencia(self):
        """23:30 em São Paulo do dia 3 já é dia 4 em UTC: vale o dia 3."""
        self.relogio.momento = datetime(2026, 10, 4, 2, 30, tzinfo=timezone.utc)
        primeiro = self.titulos.cadastrar_titulo(self.operador, "c1", Decimal("100.00"), HOJE)
        self.relogio.momento = datetime(2026, 10, 4, 15, 0, tzinfo=timezone.utc)
        segundo = self.titulos.cadastrar_titulo(self.operador, "c2", Decimal("100.00"), HOJE)
        self.assertEqual(
            [v.registro_afetado for v in self.consultar(inicio=HOJE, fim=HOJE)], [f"titulo {primeiro.id}"]
        )
        dia_seguinte = HOJE + timedelta(days=1)
        self.assertEqual(
            [v.registro_afetado for v in self.consultar(inicio=dia_seguinte)], [f"titulo {segundo.id}"]
        )

    def test_CA_04_filtro_por_tipo_de_operacao(self):
        t = self.titulos.cadastrar_titulo(self.operador, "c1", Decimal("100.00"), HOJE)
        self.titulos.registrar_pagamento(self.operador, t.id, Decimal("40.00"), HOJE)
        visoes = self.consultar(operacao="registrar pagamento")
        self.assertEqual({v.operacao for v in visoes}, {"registrar pagamento"})
        self.assertEqual(len(visoes), 1)

    def test_CA_05_A1_historico_de_um_titulo_inclui_os_pagamentos_dele(self):
        a = self.titulos.cadastrar_titulo(self.operador, "c1", Decimal("100.00"), HOJE)
        b = self.titulos.cadastrar_titulo(self.operador, "c2", Decimal("100.00"), HOJE)
        a = self.titulos.registrar_pagamento(self.operador, a.id, Decimal("100.00"), HOJE)
        self.titulos.registrar_pagamento(self.operador, b.id, Decimal("10.00"), HOJE)
        afetados = [v.registro_afetado for v in self.consultar(registro=f"titulo {a.id}")]
        self.assertEqual(
            afetados,
            [f"titulo {a.id}", f"titulo {a.id}, pagamento {a.pagamentos[0].id}", f"titulo {a.id}"],
        )

    def test_CA_06_estorno_mostra_campo_valor_anterior_novo_e_motivo(self):
        t = self.titulos.cadastrar_titulo(self.operador, "c1", Decimal("100.00"), HOJE)
        t = self.titulos.registrar_pagamento(self.operador, t.id, Decimal("100.00"), HOJE)
        self.titulos.estornar_pagamento(self.dono, t.id, t.pagamentos[0].id, "cheque devolvido", HOJE)
        [estorno] = self.consultar(operacao="estornar pagamento")
        self.assertEqual(
            (estorno.campo, estorno.valor_anterior, estorno.valor_novo, estorno.motivo),
            ("estornado", "não", "sim", "cheque devolvido"),
        )

    def test_CA_07_A2_operacao_automatica_aparece_como_sistema_com_a_rotina(self):
        self.titulos.cadastrar_titulo(self.operador, "c1", Decimal("100.00"), HOJE - timedelta(days=1))
        self.titulos.verificar_vencimentos_automaticamente(HOJE)
        [vencimento] = self.consultar(usuario_id=RESPONSAVEL_SISTEMA)
        self.assertEqual(vencimento.responsavel, "Sistema (verificação de vencimento)")
        self.assertTrue(vencimento.automatica)

    def test_CA_08_E1_sem_registros_no_periodo_o_resultado_e_vazio(self):
        self.titulos.cadastrar_titulo(self.operador, "c1", Decimal("100.00"), HOJE)
        self.assertEqual(self.consultar(inicio=HOJE + timedelta(days=10)), [])

    def test_CA_09_INV_3_operador_e_negado_contador_e_administrador_sao_atendidos(self):
        self.titulos.cadastrar_titulo(self.operador, "c1", Decimal("100.00"), HOJE)
        with self.assertRaises(OperacaoNegada):
            self.consultar(self.operador)
        for usuario in (CONTADOR, ADMIN):
            with self.subTest(perfil=usuario.perfil.value):
                self.assertEqual(len(self.consultar(self.sessao(usuario))), 1)

    def test_CA_10_INV_2_a_consulta_nao_grava_nem_altera_registros(self):
        self.titulos.cadastrar_titulo(self.operador, "c1", Decimal("100.00"), HOJE)
        antes = self.uow.auditoria.registros
        for _ in range(3):
            self.consultar()
        self.assertEqual(self.uow.auditoria.registros, antes)

    def test_CA_11_E3_periodo_invertido_e_recusado_no_campo(self):
        with self.assertRaises(OperacaoRecusada) as ctx:
            self.consultar(inicio=HOJE, fim=HOJE - timedelta(days=1))
        self.assertEqual(set(ctx.exception.campos), {"fim"})

    def test_CA_12_A3_opcoes_de_filtro_sao_os_responsaveis_e_as_operacoes_presentes(self):
        t = self.titulos.cadastrar_titulo(self.operador, "c1", Decimal("100.00"), HOJE - timedelta(days=1))
        self.titulos.cancelar_titulo(self.dono, t.id, "desistência")
        self.titulos.cadastrar_titulo(self.operador, "c2", Decimal("100.00"), HOJE - timedelta(days=1))
        self.titulos.verificar_vencimentos_automaticamente(HOJE)
        opcoes = self.auditoria.opcoes_de_filtro(self.dono)
        self.assertEqual(
            opcoes.responsaveis,
            {DONO.id: "Carla Menezes", OPERADOR.id: "Diego Ramos", RESPONSAVEL_SISTEMA: "Sistema (operação automática)"},
        )
        self.assertEqual(opcoes.operacoes, ["cadastrar título", "mudar estado"])


if __name__ == "__main__":
    unittest.main()
