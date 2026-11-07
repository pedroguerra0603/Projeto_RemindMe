"""Regras de domínio do título, testadas sem banco e sem interface (RNF-19)."""

import unittest
from datetime import date
from decimal import Decimal

from remindme.dominio.erros import OperacaoRecusada
from remindme.dominio.operacoes import Operacao
from remindme.dominio.permissoes import MatrizPermissoes
from remindme.dominio.titulo import EstadoTitulo, Titulo
from remindme.dominio.usuario import Perfil, Usuario

HOJE = date(2026, 10, 3)
DONO = Usuario("u1", "Dono", Perfil.DONO)


def titulo(valor="1000.00", vencimento=date(2026, 10, 10)):
    return Titulo.cadastrar_manual("t1", "c1", Decimal(valor), vencimento)


class RB21EstadosDoTitulo(unittest.TestCase):
    def test_RB_21_titulo_nasce_aberto(self):
        self.assertIs(titulo().estado, EstadoTitulo.ABERTO)

    def test_RB_21_recusa_pagamento_em_titulo_baixado(self):
        t = titulo()
        t.registrar_pagamento("p1", Decimal("1000.00"), HOJE)
        with self.assertRaisesRegex(OperacaoRecusada, "Baixado"):
            t.registrar_pagamento("p2", Decimal("1.00"), HOJE)

    def test_RB_21_recusa_pagamento_em_titulo_cancelado(self):
        t = titulo()
        t.cancelar("cliente desistiu")
        with self.assertRaisesRegex(OperacaoRecusada, "Cancelado"):
            t.registrar_pagamento("p1", Decimal("1.00"), HOJE)

    def test_RB_21_recusa_cancelamento_de_titulo_baixado(self):
        t = titulo()
        t.registrar_pagamento("p1", Decimal("1000.00"), HOJE)
        with self.assertRaises(OperacaoRecusada):
            t.cancelar("motivo")
        self.assertIs(t.estado, EstadoTitulo.BAIXADO)

    def test_RB_21_recusa_cancelamento_de_titulo_ja_cancelado(self):
        t = titulo()
        t.cancelar("motivo")
        with self.assertRaises(OperacaoRecusada):
            t.cancelar("motivo")

    def test_RB_21_vencido_pode_ser_cancelado(self):
        t = titulo(vencimento=date(2026, 10, 1))
        t.marcar_vencido(HOJE)
        t.cancelar("motivo")
        self.assertIs(t.estado, EstadoTitulo.CANCELADO)

    def test_RB_21_vencimento_so_afeta_titulo_aberto(self):
        t = titulo(vencimento=date(2026, 10, 1))
        t.registrar_pagamento("p1", Decimal("1000.00"), HOJE)
        self.assertFalse(t.marcar_vencido(HOJE))
        self.assertIs(t.estado, EstadoTitulo.BAIXADO)

    def test_RB_21_valor_do_titulo_nao_muda_com_pagamentos(self):
        t = titulo()
        t.registrar_pagamento("p1", Decimal("400.00"), HOJE)
        self.assertEqual(t.valor, Decimal("1000.00"))


class RB22Baixa(unittest.TestCase):
    def test_RB_22_baixa_quando_soma_dos_pagamentos_iguala_o_valor(self):
        t = titulo()
        t.registrar_pagamento("p1", Decimal("400.00"), HOJE)
        self.assertIs(t.estado, EstadoTitulo.ABERTO)
        t.registrar_pagamento("p2", Decimal("600.00"), HOJE)
        self.assertEqual(t.saldo, Decimal("0.00"))
        self.assertIs(t.estado, EstadoTitulo.BAIXADO)

    def test_RB_22_pagamento_estornado_nao_conta_no_saldo(self):
        t = titulo()
        t.registrar_pagamento("p1", Decimal("1000.00"), HOJE)
        t.estornar_pagamento("p1", "pagamento devolvido", HOJE)
        self.assertEqual(t.saldo, Decimal("1000.00"))
        self.assertIsNot(t.estado, EstadoTitulo.BAIXADO)


class RB23ValorDoPagamento(unittest.TestCase):
    def test_RB_23_recusa_pagamento_maior_que_o_saldo(self):
        t = titulo()
        with self.assertRaises(OperacaoRecusada):
            t.registrar_pagamento("p1", Decimal("1000.01"), HOJE)
        self.assertEqual(t.saldo, Decimal("1000.00"))
        self.assertEqual(t.pagamentos, [])

    def test_RB_23_recusa_pagamento_zero(self):
        with self.assertRaises(OperacaoRecusada):
            titulo().registrar_pagamento("p1", Decimal("0.00"), HOJE)

    def test_RB_23_recusa_pagamento_negativo(self):
        with self.assertRaises(OperacaoRecusada):
            titulo().registrar_pagamento("p1", Decimal("-1.00"), HOJE)

    def test_RB_23_aceita_pagamento_igual_ao_saldo(self):
        t = titulo()
        t.registrar_pagamento("p1", Decimal("1000.00"), HOJE)
        self.assertEqual(t.saldo, Decimal("0.00"))


class RB02Estorno(unittest.TestCase):
    def test_RB_02_somente_o_dono_estorna(self):
        matriz = MatrizPermissoes.inicial()
        matriz.exigir(Perfil.DONO, Operacao.ESTORNAR_PAGAMENTO)
        matriz.exigir(Perfil.ADMINISTRADOR, Operacao.ESTORNAR_PAGAMENTO)  # OPEN-53: o Administrador pode tudo
        for perfil in Perfil:
            if perfil not in (Perfil.DONO, Perfil.ADMINISTRADOR):
                with self.subTest(perfil=perfil), self.assertRaisesRegex(OperacaoRecusada, "RB-02"):
                    matriz.exigir(perfil, Operacao.ESTORNAR_PAGAMENTO)


class OPEN16Cancelamento(unittest.TestCase):
    def test_OPEN_16_somente_o_dono_cancela(self):
        matriz = MatrizPermissoes.inicial()
        matriz.exigir(Perfil.DONO, Operacao.CANCELAR_TITULO)
        matriz.exigir(Perfil.ADMINISTRADOR, Operacao.CANCELAR_TITULO)  # OPEN-53: o Administrador pode tudo
        for perfil in Perfil:
            if perfil not in (Perfil.DONO, Perfil.ADMINISTRADOR):
                with self.subTest(perfil=perfil), self.assertRaisesRegex(OperacaoRecusada, "OPEN-16"):
                    matriz.exigir(perfil, Operacao.CANCELAR_TITULO)


class RF31Motivo(unittest.TestCase):
    def test_RF_31_motivo_em_branco_equivale_a_ausente(self):
        t = titulo()
        with self.assertRaises(OperacaoRecusada):
            t.cancelar("   ")
        self.assertIs(t.estado, EstadoTitulo.ABERTO)


class RF23ProximoDoVencimento(unittest.TestCase):
    def test_RF_23_limites_da_antecedencia(self):
        casos = [(5, True), (6, False), (0, True), (-1, False)]
        for dias, esperado in casos:
            with self.subTest(dias=dias):
                t = titulo(vencimento=date.fromordinal(HOJE.toordinal() + dias))
                self.assertEqual(t.proximo_do_vencimento(HOJE, 5), esperado)

    def test_RF_23_so_titulo_aberto_e_sinalizado(self):
        t = titulo(vencimento=date(2026, 10, 5))
        t.cancelar("motivo")
        self.assertFalse(t.proximo_do_vencimento(HOJE, 5))


class GeradoDeOrcamento(unittest.TestCase):
    """Spec 005: o título gerado na aprovação do orçamento (RF-11, RF-19, RB-05)."""

    def orcamento(self, aprovar=True):
        from remindme.dominio.orcamento import Orcamento

        o = Orcamento.criar("o1", "c1", "operador", date(2026, 11, 2), "Boleto")
        o.incluir_item("i1", "Revisão", Decimal("1"), Decimal("1000.00"))
        o.informar_desconto(Decimal("10"), "operador", Decimal("10"))
        o.alterar_prazo(30)
        o.marcar_enviado(date(2026, 11, 2))
        if aprovar:
            o.registrar_decisao(True, date(2026, 11, 7), date(2026, 11, 7))
        return o

    def test_RF_19_gerar_de_orcamento_copia_cliente_valor_liquido_condicao_e_vencimento(self):
        t = Titulo.gerar_de_orcamento("t9", self.orcamento())
        self.assertEqual(
            (t.id, t.cliente_id, t.valor, t.condicao_pagamento, t.vencimento, t.origem, t.orcamento_id, t.estado),
            ("t9", "c1", Decimal("900.00"), "Boleto", date(2026, 12, 7), "orcamento", "o1", EstadoTitulo.ABERTO),
        )
        self.assertEqual(t.saldo, Decimal("900.00"))

    def test_RF_12_gerar_de_orcamento_nao_aprovado_e_recusado(self):
        with self.assertRaises(OperacaoRecusada) as ctx:
            Titulo.gerar_de_orcamento("t9", self.orcamento(aprovar=False))
        self.assertEqual(ctx.exception.motivo, "Só orçamento Aprovado vira título; este está Enviado (RF-12).")

    def test_titulo_manual_nao_tem_orcamento(self):
        self.assertIsNone(titulo().orcamento_id)


if __name__ == "__main__":
    unittest.main()
