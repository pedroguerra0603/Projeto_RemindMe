"""Regras do orçamento no domínio (Spec 004): RF-07, RB-15, RB-24, RF-13 e as transições de estado."""

import unittest
from datetime import date
from decimal import Decimal

from remindme.dominio.erros import OperacaoRecusada
from remindme.dominio.orcamento import EstadoOrcamento, Orcamento, alcada_do_perfil
from remindme.dominio.usuario import Perfil

HOJE = date(2026, 10, 29)
ALCADA = Decimal("10.00")


def orcamento(*itens):
    o = Orcamento.criar("o1", "c1", "operador", HOJE, "Pix")
    for numero, (quantidade, unitario) in enumerate(itens):
        o.incluir_item(f"i{numero}", f"Item {numero}", Decimal(quantidade), Decimal(unitario))
    return o


class Valores(unittest.TestCase):
    def test_RF_06_nasce_em_rascunho_sem_itens_e_sem_desconto(self):
        o = orcamento()
        self.assertIs(o.estado, EstadoOrcamento.RASCUNHO)
        self.assertEqual((o.valor_bruto, o.percentual_desconto, o.valor_liquido), (Decimal("0.00"),) * 3)

    def test_RF_07_bruto_desconto_e_liquido_sao_recalculados(self):
        o = orcamento(("2.5", "120.00"), ("1", "99.99"))
        self.assertEqual(o.valor_bruto, Decimal("399.99"))
        o.informar_desconto(Decimal("7.5"), "operador", ALCADA)
        self.assertEqual(o.valor_desconto, Decimal("30.00"))  # 29,99925 arredonda para cima (OPEN-51)
        self.assertEqual(o.valor_liquido, Decimal("369.99"))
        o.remover_item("i1")
        self.assertEqual((o.valor_bruto, o.valor_desconto, o.valor_liquido), (Decimal("300.00"), Decimal("22.50"), Decimal("277.50")))

    def test_OPEN_51_total_do_item_arredonda_ao_centavo_metade_para_cima(self):
        o = orcamento(("0.33", "10.05"))
        self.assertEqual(o.itens[0].total, Decimal("3.32"))  # 3,3165

    def test_RNF_14_item_invalido_informa_todos_os_campos(self):
        o = orcamento()
        with self.assertRaises(OperacaoRecusada) as ctx:
            o.incluir_item("i", " ", Decimal("0"), Decimal("1.001"))
        self.assertEqual(set(ctx.exception.campos), {"descricao", "quantidade", "valor_unitario"})
        self.assertEqual(o.itens, [])

    def test_valor_que_nao_e_decimal_e_recusado(self):
        for invalido in (1.5, "10", None, Decimal("NaN"), Decimal("Infinity")):
            with self.subTest(valor=invalido):
                with self.assertRaises(OperacaoRecusada):
                    orcamento().incluir_item("i", "Serviço", Decimal("1"), invalido)

    def test_OPEN_24_valor_do_orcamento_tem_no_maximo_15_digitos_inteiros(self):
        o = orcamento(("1", "999999999999999.00"))
        with self.assertRaises(OperacaoRecusada):
            o.incluir_item("x", "Mais um", Decimal("1"), Decimal("1.00"))
        self.assertEqual(len(o.itens), 1)

    def test_alterar_item_que_estoura_o_limite_nao_altera_nada(self):
        o = orcamento(("1", "10.00"), ("1", "20.00"))
        with self.assertRaises(OperacaoRecusada):
            o.alterar_item("i0", "Item 0", Decimal("1"), Decimal("999999999999999.00"))
        self.assertEqual([i.valor_unitario for i in o.itens], [Decimal("10.00"), Decimal("20.00")])


class Alcada(unittest.TestCase):
    def test_RB_15_desconto_dentro_da_alcada_e_aplicado(self):
        o = orcamento(("1", "100.00"))
        self.assertFalse(o.informar_desconto(Decimal("10"), "operador", ALCADA))
        self.assertIs(o.estado, EstadoOrcamento.RASCUNHO)
        self.assertEqual(o.percentual_desconto, Decimal("10.00"))

    def test_RB_15_RF_16_desconto_acima_da_alcada_fica_pendente_sem_mudar_o_vigente(self):
        o = orcamento(("1", "100.00"))
        o.informar_desconto(Decimal("5"), "operador", ALCADA)
        self.assertTrue(o.informar_desconto(Decimal("15"), "operador", ALCADA))
        self.assertIs(o.estado, EstadoOrcamento.PENDENTE_DE_ALCADA)
        self.assertEqual(o.percentual_desconto, Decimal("5.00"))
        self.assertEqual(o.pendencia.percentual_solicitado, Decimal("15.00"))

    def test_RB_15_o_dono_nao_tem_limite(self):
        self.assertIsNone(alcada_do_perfil(Perfil.DONO))
        o = orcamento(("1", "100.00"))
        self.assertFalse(o.informar_desconto(Decimal("60"), "dono", alcada_do_perfil(Perfil.DONO)))
        self.assertEqual(o.percentual_desconto, Decimal("60.00"))

    def test_OPEN_49_alcadas_padrao(self):
        self.assertEqual(alcada_do_perfil(Perfil.OPERADOR_FINANCEIRO), Decimal("10.00"))
        self.assertEqual(alcada_do_perfil(Perfil.CONTADOR), Decimal("0.00"))

    def test_OPEN_51_percentual_entre_0_e_100_com_duas_casas(self):
        for invalido in (Decimal("-1"), Decimal("100.01"), Decimal("5.555"), 5):
            with self.subTest(percentual=invalido):
                with self.assertRaises(OperacaoRecusada) as ctx:
                    orcamento().informar_desconto(invalido, "dono", None)
                self.assertEqual(set(ctx.exception.campos), {"percentual"})

    def test_RF_07_pendente_de_alcada_nao_aceita_alteracao(self):
        o = orcamento(("1", "100.00"))
        o.informar_desconto(Decimal("30"), "operador", ALCADA)
        for alterar in (
            lambda: o.incluir_item("x", "Outro", Decimal("1"), Decimal("1.00")),
            lambda: o.remover_item("i0"),
            lambda: o.informar_desconto(Decimal("5"), "operador", ALCADA),
            lambda: o.alterar_condicao("Boleto"),
        ):
            with self.assertRaises(OperacaoRecusada):
                alterar()


class DecisaoDoDono(unittest.TestCase):
    def pendente(self, solicitado="20", vigente="5"):
        o = orcamento(("1", "1000.00"))
        o.informar_desconto(Decimal(vigente), "operador", ALCADA)
        o.informar_desconto(Decimal(solicitado), "operador", ALCADA)
        return o

    def test_RF_17_aprovacao_registra_e_volta_a_rascunho_com_o_desconto(self):
        o = self.pendente()
        decisao = o.decidir_desconto(True, "dono", HOJE)
        self.assertIs(o.estado, EstadoOrcamento.RASCUNHO)
        self.assertEqual(o.percentual_desconto, Decimal("20.00"))
        self.assertEqual((decisao.aprovado, decisao.decidido_por, decisao.data), (True, "dono", HOJE))
        self.assertIsNone(o.pendencia)

    def test_UC_05_A1_rejeicao_mantem_o_desconto_anterior(self):
        o = self.pendente()
        o.decidir_desconto(False, "dono", HOJE)
        self.assertEqual((o.estado, o.percentual_desconto), (EstadoOrcamento.RASCUNHO, Decimal("5.00")))

    def test_UC_05_A2_aprovar_um_desconto_menor_guarda_solicitado_e_aprovado(self):
        o = self.pendente()
        decisao = o.decidir_desconto(True, "dono", HOJE, Decimal("12"))
        self.assertEqual((decisao.percentual_solicitado, decisao.percentual_aprovado), (Decimal("20.00"), Decimal("12.00")))
        self.assertEqual(o.percentual_desconto, Decimal("12.00"))

    def test_UC_05_A2_nao_aprova_mais_que_o_solicitado(self):
        o = self.pendente()
        with self.assertRaises(OperacaoRecusada):
            o.decidir_desconto(True, "dono", HOJE, Decimal("25"))
        self.assertIs(o.estado, EstadoOrcamento.PENDENTE_DE_ALCADA)

    def test_UC_05_E2_sem_pendencia_nao_ha_decisao(self):
        o = self.pendente()
        o.cancelar("Cliente desistiu")
        with self.assertRaises(OperacaoRecusada) as ctx:
            o.decidir_desconto(True, "dono", HOJE)
        self.assertIn("Cancelado", ctx.exception.motivo)

    def test_desconto_ja_aprovado_nao_gera_nova_pendencia(self):
        o = self.pendente()
        o.decidir_desconto(True, "dono", HOJE)
        self.assertFalse(o.informar_desconto(Decimal("20"), "operador", ALCADA))
        self.assertIs(o.estado, EstadoOrcamento.RASCUNHO)


class EnvioECancelamento(unittest.TestCase):
    def test_RB_24_sem_item_nao_e_enviado(self):
        with self.assertRaises(OperacaoRecusada) as ctx:
            orcamento().exigir_envio()
        self.assertIn("RB-24", ctx.exception.motivo)
        orcamento(("1", "10.00")).exigir_envio()

    def test_RB_15_pendente_de_alcada_nao_e_enviado(self):
        o = orcamento(("1", "100.00"))
        o.informar_desconto(Decimal("50"), "operador", ALCADA)
        self.assertIn("RB-15", o.motivo_para_nao_enviar())

    def test_RF_13_cancelamento_exige_motivo_e_e_final(self):
        o = orcamento(("1", "100.00"))
        with self.assertRaises(OperacaoRecusada) as ctx:
            o.cancelar("  ")
        self.assertEqual(set(ctx.exception.campos), {"motivo"})
        o.cancelar("Cliente desistiu")
        self.assertEqual((o.estado, o.motivo_cancelamento), (EstadoOrcamento.CANCELADO, "Cliente desistiu"))
        with self.assertRaises(OperacaoRecusada):
            o.cancelar("De novo")
        with self.assertRaises(OperacaoRecusada):
            o.incluir_item("x", "Outro", Decimal("1"), Decimal("1.00"))

    def test_RF_13_pendente_de_alcada_pode_ser_cancelado(self):
        o = orcamento(("1", "100.00"))
        o.informar_desconto(Decimal("50"), "operador", ALCADA)
        o.cancelar("Preço não fechou")
        self.assertIsNone(o.pendencia)


if __name__ == "__main__":
    unittest.main()
