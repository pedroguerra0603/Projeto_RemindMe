"""Regras da conta a pagar (Spec 018), só com o domínio: RB-31, RB-32 e as invariantes INV-1 a INV-4."""

import unittest
from datetime import date, timedelta
from decimal import Decimal

from remindme.dominio.conta_pagar import ContaPagar, EstadoContaPagar
from remindme.dominio.erros import OperacaoRecusada
from remindme.dominio.titulo import PedidoDePagamentoRepetido

HOJE = date(2026, 10, 3)


def conta(valor="1200.00", vencimento=HOJE + timedelta(days=10)) -> ContaPagar:
    return ContaPagar.cadastrar("c1", "f1", "20 pneus aro 14", Decimal(valor), vencimento, "Boleto")


class Cadastro(unittest.TestCase):
    def test_RF_88_nasce_aberta_com_saldo_igual_ao_valor(self):
        c = conta()
        self.assertEqual((c.estado, c.saldo, c.descricao), (EstadoContaPagar.ABERTA, Decimal("1200.00"), "20 pneus aro 14"))

    def test_estados_sao_os_da_RB_31(self):
        self.assertEqual([e.value for e in EstadoContaPagar], ["Aberta", "Vencida", "Paga", "Cancelada"])

    def test_E2_descricao_vazia_vencimento_ausente_e_valor_invalido_sao_recusados(self):
        casos = [
            ("descricao", dict(descricao="  ")),
            ("vencimento", dict(vencimento=None)),
            ("valor", dict(valor=Decimal("0.00"))),
            ("valor", dict(valor=Decimal("10.001"))),
            ("valor", dict(valor=Decimal("1" + "0" * 15))),
            ("valor", dict(valor=1200.0)),
        ]
        for campo, troca in casos:
            dados = dict(descricao="Pneus", valor=Decimal("100.00"), vencimento=HOJE)
            dados.update(troca)
            with self.subTest(troca=troca), self.assertRaises(OperacaoRecusada) as ctx:
                ContaPagar.cadastrar("c1", "f1", dados["descricao"], dados["valor"], dados["vencimento"])
            self.assertIn(campo, ctx.exception.campos)


class Pagamentos(unittest.TestCase):
    def test_RB_31_pagamento_parcial_mantem_aberta_e_o_que_zera_o_saldo_a_torna_paga(self):
        c = conta()
        c.registrar_pagamento("p1", Decimal("500.00"), HOJE, hoje=HOJE)
        self.assertEqual((c.estado, c.saldo), (EstadoContaPagar.ABERTA, Decimal("700.00")))
        c.registrar_pagamento("p2", Decimal("700.00"), HOJE, hoje=HOJE)
        self.assertEqual((c.estado, c.saldo), (EstadoContaPagar.PAGA, Decimal("0.00")))

    def test_RB_32_pagamento_maior_que_o_saldo_zero_ou_negativo_e_recusado(self):
        c = conta()
        c.registrar_pagamento("p1", Decimal("500.00"), HOJE, hoje=HOJE)
        for valor in ("700.01", "0.00", "-1.00"):
            with self.subTest(valor=valor), self.assertRaises(OperacaoRecusada):
                c.registrar_pagamento("p2", Decimal(valor), HOJE, hoje=HOJE)
        self.assertEqual(c.saldo, Decimal("700.00"))

    def test_E3_data_futura_e_recusada(self):
        with self.assertRaises(OperacaoRecusada) as ctx:
            conta().registrar_pagamento("p1", Decimal("1.00"), HOJE + timedelta(days=1), hoje=HOJE)
        self.assertIn("data", ctx.exception.campos)

    def test_RB_31_paga_e_cancelada_nao_aceitam_pagamento(self):
        paga = conta("10.00")
        paga.registrar_pagamento("p1", Decimal("10.00"), HOJE, hoje=HOJE)
        cancelada = conta()
        cancelada.cancelar("Compra desfeita")
        for c in (paga, cancelada):
            with self.subTest(estado=c.estado.value), self.assertRaisesRegex(OperacaoRecusada, c.estado.value):
                c.registrar_pagamento("p9", Decimal("1.00"), HOJE, hoje=HOJE)

    def test_OPEN_25_pedido_repetido_e_reconhecido(self):
        c = conta()
        c.registrar_pagamento("p1", Decimal("100.00"), HOJE, hoje=HOJE, pedido_id="pedido-1")
        with self.assertRaises(PedidoDePagamentoRepetido):
            c.registrar_pagamento("p2", Decimal("100.00"), HOJE, hoje=HOJE, pedido_id="pedido-1")
        self.assertEqual(c.saldo, Decimal("1100.00"))


class Vencimento(unittest.TestCase):
    def test_RF_90_aberta_com_vencimento_passado_vira_vencida_e_a_de_hoje_nao(self):
        ontem, de_hoje = conta(vencimento=HOJE - timedelta(days=1)), conta(vencimento=HOJE)
        self.assertTrue(ontem.marcar_vencida(HOJE))
        self.assertFalse(de_hoje.marcar_vencida(HOJE))
        self.assertEqual((ontem.estado, de_hoje.estado), (EstadoContaPagar.VENCIDA, EstadoContaPagar.ABERTA))
        self.assertFalse(ontem.marcar_vencida(HOJE))  # idempotente

    def test_vencida_paga_integralmente_vira_paga(self):
        c = conta("50.00", HOJE - timedelta(days=3))
        c.marcar_vencida(HOJE)
        c.registrar_pagamento("p1", Decimal("50.00"), HOJE, hoje=HOJE)
        self.assertIs(c.estado, EstadoContaPagar.PAGA)


class EstornoECancelamento(unittest.TestCase):
    def test_RF_92_estorno_de_conta_paga_volta_a_aberta_ou_vencida_conforme_o_vencimento(self):
        for vencimento, esperado in ((HOJE, EstadoContaPagar.ABERTA), (HOJE - timedelta(days=1), EstadoContaPagar.VENCIDA)):
            c = conta("80.00", vencimento)
            pagamento = c.registrar_pagamento("p1", Decimal("80.00"), HOJE, hoje=HOJE)
            c.estornar_pagamento(pagamento.id, "Boleto pago em duplicidade", HOJE)
            with self.subTest(vencimento=vencimento):
                self.assertEqual((c.estado, c.saldo), (esperado, Decimal("80.00")))
                self.assertTrue(c.pagamentos[0].estornado)  # INV-4: não é apagado

    def test_E4_E5_estorno_sem_motivo_repetido_ou_em_conta_cancelada_e_recusado(self):
        c = conta()
        pagamento = c.registrar_pagamento("p1", Decimal("100.00"), HOJE, hoje=HOJE)
        with self.assertRaisesRegex(OperacaoRecusada, "motivo"):
            c.estornar_pagamento(pagamento.id, " ", HOJE)
        c.estornar_pagamento(pagamento.id, "Erro de digitação", HOJE)
        with self.assertRaises(OperacaoRecusada):
            c.estornar_pagamento(pagamento.id, "De novo", HOJE)
        outra = conta()
        p = outra.registrar_pagamento("p1", Decimal("100.00"), HOJE, hoje=HOJE)
        outra.cancelar("Compra desfeita")
        with self.assertRaisesRegex(OperacaoRecusada, "Cancelada"):
            outra.estornar_pagamento(p.id, "Motivo", HOJE)

    def test_RF_93_cancelamento_exige_motivo_e_nao_vale_para_conta_paga(self):
        c = conta()
        with self.assertRaisesRegex(OperacaoRecusada, "motivo"):
            c.cancelar("")
        c.cancelar("Compra desfeita")
        self.assertIs(c.estado, EstadoContaPagar.CANCELADA)
        paga = conta("10.00")
        paga.registrar_pagamento("p1", Decimal("10.00"), HOJE, hoje=HOJE)
        with self.assertRaisesRegex(OperacaoRecusada, "Estorne"):
            paga.cancelar("Motivo")

    def test_INV_1_saldo_e_valor_menos_pagamentos_nao_estornados(self):
        c = conta("300.00")
        p1 = c.registrar_pagamento("p1", Decimal("100.00"), HOJE, hoje=HOJE)
        c.registrar_pagamento("p2", Decimal("50.00"), HOJE, hoje=HOJE)
        c.estornar_pagamento(p1.id, "Erro", HOJE)
        self.assertEqual(c.saldo, Decimal("250.00"))
        self.assertEqual(c.valor, Decimal("300.00"))


if __name__ == "__main__":
    unittest.main()
