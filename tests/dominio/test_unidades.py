"""Testes unitários das classes do domínio, uma unidade por vez, sem aplicação nem infraestrutura."""

import dataclasses
import unittest
from datetime import date, datetime, timedelta
from decimal import Decimal

from remindme.dominio.auditoria import RegistroAuditoria
from remindme.dominio.erros import OperacaoRecusada
from remindme.dominio.titulo import EstadoTitulo, Pagamento, Titulo
from remindme.dominio.usuario import Perfil, Usuario

HOJE = date(2026, 10, 3)
ONTEM = HOJE - timedelta(days=1)
AMANHA = HOJE + timedelta(days=1)


def titulo(valor="1000.00", vencimento=AMANHA):
    return Titulo.cadastrar_manual("t1", "c1", Decimal(valor), vencimento, "30 dias")


class CadastroManual(unittest.TestCase):
    def test_RF_21_armazena_todos_os_dados_do_titulo(self):
        t = titulo()
        self.assertEqual(
            (t.id, t.cliente_id, t.valor, t.vencimento, t.origem, t.condicao_pagamento, t.estado),
            ("t1", "c1", Decimal("1000.00"), AMANHA, "manual", "30 dias", EstadoTitulo.ABERTO),
        )
        self.assertEqual(t.pagamentos, [])

    def test_RF_20_condicao_de_pagamento_e_opcional(self):
        t = Titulo.cadastrar_manual("t1", "c1", Decimal("1.00"), AMANHA)
        self.assertIsNone(t.condicao_pagamento)

    def test_E7_recusa_valor_negativo(self):
        with self.assertRaisesRegex(OperacaoRecusada, "valor"):
            titulo(valor="-0.01")

    def test_E7_aceita_menor_valor_positivo(self):
        self.assertEqual(titulo(valor="0.01").saldo, Decimal("0.01"))

    def test_E7_vencimento_pode_ser_passado(self):
        """A Spec 006 não restringe o vencimento do cadastro manual; o título nasce Aberto."""
        self.assertIs(titulo(vencimento=ONTEM).estado, EstadoTitulo.ABERTO)

    def test_titulos_nao_compartilham_a_lista_de_pagamentos(self):
        a, b = titulo(), titulo()
        a.registrar_pagamento("p1", Decimal("1.00"), HOJE)
        self.assertEqual(b.pagamentos, [])


class Saldo(unittest.TestCase):
    def test_INV_1_saldo_inicial_e_o_valor(self):
        self.assertEqual(titulo().saldo, Decimal("1000.00"))

    def test_INV_1_saldo_desconta_somente_pagamentos_validos(self):
        t = titulo()
        t.registrar_pagamento("p1", Decimal("100.00"), HOJE)
        t.registrar_pagamento("p2", Decimal("200.00"), HOJE)
        t.estornar_pagamento("p1", "devolvido", HOJE)
        self.assertEqual(t.saldo, Decimal("800.00"))

    def test_INV_1_saldo_e_exato_em_centavos(self):
        t = titulo(valor="100.00")
        for i in range(3):
            t.registrar_pagamento(f"p{i}", Decimal("33.33"), HOJE)
        self.assertEqual(t.saldo, Decimal("0.01"))
        self.assertIs(t.estado, EstadoTitulo.ABERTO)


class RegistroDePagamento(unittest.TestCase):
    def test_RF_25_devolve_o_pagamento_registrado(self):
        t = titulo()
        pagamento = t.registrar_pagamento("p1", Decimal("10.00"), ONTEM)
        self.assertEqual(pagamento, Pagamento("p1", Decimal("10.00"), ONTEM))
        self.assertFalse(pagamento.estornado)
        self.assertIsNone(pagamento.motivo_estorno)
        self.assertIs(t.pagamentos[0], pagamento)

    def test_RF_27_pagamento_parcial_de_titulo_vencido_mantem_vencido(self):
        t = titulo(vencimento=ONTEM)
        t.marcar_vencido(HOJE)
        t.registrar_pagamento("p1", Decimal("10.00"), HOJE)
        self.assertIs(t.estado, EstadoTitulo.VENCIDO)


class Vencimento(unittest.TestCase):
    def test_RF_24_marcar_vencido_informa_se_mudou(self):
        t = titulo(vencimento=ONTEM)
        self.assertTrue(t.marcar_vencido(HOJE))
        self.assertFalse(t.marcar_vencido(HOJE))
        self.assertIs(t.estado, EstadoTitulo.VENCIDO)

    def test_RF_24_titulo_cancelado_nao_vence(self):
        t = titulo(vencimento=ONTEM)
        t.cancelar("motivo")
        self.assertFalse(t.marcar_vencido(HOJE))
        self.assertIs(t.estado, EstadoTitulo.CANCELADO)

    def test_RF_23_titulo_vencido_nao_e_sinalizado_como_proximo(self):
        t = titulo(vencimento=ONTEM)
        t.marcar_vencido(HOJE)
        self.assertFalse(t.proximo_do_vencimento(HOJE, 5))


class Estorno(unittest.TestCase):
    def test_A4_estorno_com_vencimento_igual_a_data_de_referencia_volta_a_aberto(self):
        t = titulo(vencimento=HOJE)
        t.registrar_pagamento("p1", Decimal("1000.00"), HOJE)
        t.estornar_pagamento("p1", "devolvido", HOJE)
        self.assertIs(t.estado, EstadoTitulo.ABERTO)

    def test_A4_estorno_parcial_nao_muda_estado_aberto(self):
        t = titulo()
        t.registrar_pagamento("p1", Decimal("10.00"), HOJE)
        t.estornar_pagamento("p1", "devolvido", HOJE)
        self.assertIs(t.estado, EstadoTitulo.ABERTO)

    def test_A4_estorno_parcial_nao_muda_estado_vencido(self):
        t = titulo(vencimento=ONTEM)
        t.marcar_vencido(HOJE)
        t.registrar_pagamento("p1", Decimal("10.00"), HOJE)
        t.estornar_pagamento("p1", "devolvido", HOJE)
        self.assertIs(t.estado, EstadoTitulo.VENCIDO)

    def test_RF_30_estorno_guarda_o_motivo(self):
        t = titulo()
        t.registrar_pagamento("p1", Decimal("10.00"), HOJE)
        pagamento = t.estornar_pagamento("p1", "cheque devolvido", HOJE)
        self.assertTrue(pagamento.estornado)
        self.assertEqual(pagamento.motivo_estorno, "cheque devolvido")

    def test_E5_estorno_de_pagamento_inexistente_e_recusado(self):
        with self.assertRaisesRegex(OperacaoRecusada, "não encontrado"):
            titulo().estornar_pagamento("x", "motivo", HOJE)

    def test_OPEN_18_estorno_em_titulo_cancelado_e_recusado(self):
        t = titulo()
        t.registrar_pagamento("p1", Decimal("10.00"), HOJE)
        t.cancelar("motivo")
        with self.assertRaisesRegex(OperacaoRecusada, "OPEN-18"):
            t.estornar_pagamento("p1", "motivo", HOJE)
        self.assertFalse(t.pagamentos[0].estornado)


class Cancelamento(unittest.TestCase):
    def test_E6_recusa_de_cancelamento_de_baixado_orienta_o_estorno(self):
        t = titulo()
        t.registrar_pagamento("p1", Decimal("1000.00"), HOJE)
        with self.assertRaisesRegex(OperacaoRecusada, "Estorne"):
            t.cancelar("motivo")

    def test_E4_motivo_e_verificado_antes_do_estado(self):
        t = titulo()
        t.cancelar("motivo")
        with self.assertRaisesRegex(OperacaoRecusada, "motivo"):
            t.cancelar(None)


class ObjetosDeValor(unittest.TestCase):
    def test_usuario_e_imutavel(self):
        with self.assertRaises(dataclasses.FrozenInstanceError):
            Usuario("u", "Nome", Perfil.DONO).perfil = Perfil.CLIENTE

    def test_RB_30_registro_de_auditoria_e_imutavel(self):
        registro = RegistroAuditoria("u", datetime(2026, 10, 3), "operação", "titulo t1")
        with self.assertRaises(dataclasses.FrozenInstanceError):
            registro.operacao = "outra"

    def test_perfis_sao_os_cinco_da_baseline(self):
        self.assertEqual(
            {p.value for p in Perfil},
            {"Dono", "Operador Financeiro", "Contador", "Cliente", "Administrador"},
        )

    def test_RB_21_estados_implementados_na_spec_006(self):
        self.assertEqual(
            [e.value for e in EstadoTitulo], ["Aberto", "Vencido", "Baixado", "Cancelado"]
        )

    def test_recusa_guarda_o_motivo(self):
        recusa = OperacaoRecusada("motivo da recusa")
        self.assertEqual(recusa.motivo, "motivo da recusa")
        self.assertEqual(str(recusa), "motivo da recusa")


if __name__ == "__main__":
    unittest.main()
