"""Critérios de aceitação da Spec 006. Um teste por critério, nomeado pelo identificador."""

import random
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

HOJE = date(2026, 10, 3)
ONTEM = HOJE - timedelta(days=1)
FUTURO = HOJE + timedelta(days=30)
PASSADO = HOJE - timedelta(days=30)
DONO = Usuario("dono", "Dono", Perfil.DONO)
OPERADOR = Usuario("operador", "Operador", Perfil.OPERADOR_FINANCEIRO)


def R(valor: str) -> Decimal:
    return Decimal(valor)


class Spec006(unittest.TestCase):
    def setUp(self):
        self.titulos = RepositorioTitulosEmMemoria()
        self.auditoria = AuditoriaEmMemoria()
        self.servico = ServicoTitulos(
            UnidadeDeTrabalhoEmMemoria(self.titulos, self.auditoria),
            ClientesEmMemoria({"c1", "c2"}),
            RelogioFixo(datetime(2026, 10, 3, 10, 0)),
        )

    def novo_titulo(self, valor="1000.00", vencimento=FUTURO, cliente="c1"):
        return self.servico.cadastrar_titulo(OPERADOR, cliente, R(valor), vencimento)

    def baixado_por_pagamento(self, vencimento):
        t = self.novo_titulo(vencimento=vencimento)
        t = self.servico.registrar_pagamento(OPERADOR, t.id, R("1000.00"), HOJE)
        return t, t.pagamentos[0].id

    def armazenado(self, titulo_id):
        return self.titulos.obter(titulo_id)

    def test_CA_01_cadastro_manual_cria_titulo_aberto(self):
        t = self.novo_titulo()
        salvo = self.armazenado(t.id)
        self.assertIs(salvo.estado, EstadoTitulo.ABERTO)
        self.assertEqual(salvo.saldo, R("1000.00"))
        self.assertEqual(salvo.origem, "manual")

    def test_CA_02_recusa_cadastro_com_valor_zero(self):
        with self.assertRaises(OperacaoRecusada):
            self.novo_titulo(valor="0.00")
        self.assertEqual(self.titulos.listar(), [])

    def test_CA_02_E7_recusa_cadastro_com_cliente_inexistente_ou_sem_vencimento(self):
        with self.assertRaises(OperacaoRecusada):
            self.novo_titulo(cliente="inexistente")
        with self.assertRaises(OperacaoRecusada):
            self.novo_titulo(vencimento=None)
        self.assertEqual(self.titulos.listar(), [])

    def test_CA_03_pagamento_integral_baixa_o_titulo(self):
        t = self.novo_titulo()
        self.servico.registrar_pagamento(OPERADOR, t.id, R("1000.00"), HOJE)
        salvo = self.armazenado(t.id)
        self.assertEqual(salvo.saldo, R("0.00"))
        self.assertIs(salvo.estado, EstadoTitulo.BAIXADO)

    def test_CA_04_pagamento_parcial_mantem_aberto(self):
        t = self.novo_titulo()
        resultado = self.servico.registrar_pagamento(OPERADOR, t.id, R("400.00"), HOJE)
        self.assertEqual(resultado.saldo, R("600.00"))
        self.assertIs(self.armazenado(t.id).estado, EstadoTitulo.ABERTO)

    def test_CA_05_pagamento_do_saldo_restante_baixa_o_titulo(self):
        t = self.novo_titulo()
        self.servico.registrar_pagamento(OPERADOR, t.id, R("400.00"), HOJE)
        self.servico.registrar_pagamento(OPERADOR, t.id, R("600.00"), HOJE)
        salvo = self.armazenado(t.id)
        self.assertEqual(salvo.saldo, R("0.00"))
        self.assertIs(salvo.estado, EstadoTitulo.BAIXADO)

    def test_CA_06_recusa_pagamento_maior_que_o_saldo(self):
        t = self.novo_titulo()
        self.servico.registrar_pagamento(OPERADOR, t.id, R("400.00"), HOJE)
        with self.assertRaises(OperacaoRecusada):
            self.servico.registrar_pagamento(OPERADOR, t.id, R("600.01"), HOJE)
        self.assertEqual(self.armazenado(t.id).saldo, R("600.00"))

    def test_CA_07_recusa_pagamento_zero_ou_negativo(self):
        t = self.novo_titulo()
        for valor in ("0.00", "-10.00"):
            with self.subTest(valor=valor), self.assertRaises(OperacaoRecusada):
                self.servico.registrar_pagamento(OPERADOR, t.id, R(valor), HOJE)
        self.assertEqual(self.armazenado(t.id).pagamentos, [])

    def test_CA_08_recusa_pagamento_em_titulo_baixado_informando_o_estado(self):
        t, _ = self.baixado_por_pagamento(FUTURO)
        with self.assertRaisesRegex(OperacaoRecusada, "Baixado"):
            self.servico.registrar_pagamento(OPERADOR, t.id, R("1.00"), HOJE)

    def test_CA_09_recusa_pagamento_em_titulo_cancelado(self):
        t = self.novo_titulo()
        self.servico.cancelar_titulo(DONO, t.id, "cliente desistiu")
        with self.assertRaises(OperacaoRecusada):
            self.servico.registrar_pagamento(OPERADOR, t.id, R("1.00"), HOJE)

    def test_CA_10_titulo_com_vencimento_ontem_passa_a_vencido(self):
        t = self.novo_titulo(vencimento=ONTEM)
        self.assertEqual(self.servico.verificar_vencimentos(OPERADOR, HOJE), [t.id])
        self.assertIs(self.armazenado(t.id).estado, EstadoTitulo.VENCIDO)

    def test_CA_11_titulo_com_vencimento_hoje_continua_aberto(self):
        t = self.novo_titulo(vencimento=HOJE)
        self.servico.verificar_vencimentos(OPERADOR, HOJE)
        self.assertIs(self.armazenado(t.id).estado, EstadoTitulo.ABERTO)

    def test_CA_12_pagamento_integral_de_titulo_vencido_baixa(self):
        t = self.novo_titulo(vencimento=ONTEM)
        self.servico.verificar_vencimentos(OPERADOR, HOJE)
        self.servico.registrar_pagamento(OPERADOR, t.id, R("1000.00"), HOJE)
        self.assertIs(self.armazenado(t.id).estado, EstadoTitulo.BAIXADO)

    def test_CA_13_estorno_com_vencimento_futuro_volta_a_aberto(self):
        t, pagamento_id = self.baixado_por_pagamento(FUTURO)
        self.servico.estornar_pagamento(DONO, t.id, pagamento_id, "cheque devolvido", HOJE)
        salvo = self.armazenado(t.id)
        self.assertTrue(salvo.pagamentos[0].estornado)
        self.assertEqual(salvo.saldo, R("1000.00"))
        self.assertIs(salvo.estado, EstadoTitulo.ABERTO)

    def test_CA_14_estorno_com_vencimento_passado_vai_a_vencido(self):
        t, pagamento_id = self.baixado_por_pagamento(PASSADO)
        self.servico.estornar_pagamento(DONO, t.id, pagamento_id, "cheque devolvido", HOJE)
        self.assertIs(self.armazenado(t.id).estado, EstadoTitulo.VENCIDO)

    def test_CA_15_operador_financeiro_nao_estorna(self):
        t, pagamento_id = self.baixado_por_pagamento(FUTURO)
        with self.assertRaises(OperacaoRecusada):
            self.servico.estornar_pagamento(OPERADOR, t.id, pagamento_id, "motivo", HOJE)
        salvo = self.armazenado(t.id)
        self.assertFalse(salvo.pagamentos[0].estornado)
        self.assertIs(salvo.estado, EstadoTitulo.BAIXADO)

    def test_CA_16_recusa_estorno_sem_motivo(self):
        t, pagamento_id = self.baixado_por_pagamento(FUTURO)
        for motivo in (None, ""):
            with self.subTest(motivo=motivo), self.assertRaises(OperacaoRecusada):
                self.servico.estornar_pagamento(DONO, t.id, pagamento_id, motivo, HOJE)
        self.assertFalse(self.armazenado(t.id).pagamentos[0].estornado)

    def test_CA_17_recusa_segundo_estorno_do_mesmo_pagamento(self):
        t, pagamento_id = self.baixado_por_pagamento(FUTURO)
        self.servico.estornar_pagamento(DONO, t.id, pagamento_id, "motivo", HOJE)
        with self.assertRaises(OperacaoRecusada):
            self.servico.estornar_pagamento(DONO, t.id, pagamento_id, "motivo", HOJE)
        self.assertEqual(self.armazenado(t.id).saldo, R("1000.00"))

    def test_CA_18_dono_cancela_titulo_aberto_com_motivo(self):
        t = self.novo_titulo()
        self.servico.cancelar_titulo(DONO, t.id, "cliente desistiu")
        self.assertIs(self.armazenado(t.id).estado, EstadoTitulo.CANCELADO)

    def test_CA_18_OPEN_16_operador_financeiro_nao_cancela(self):
        t = self.novo_titulo()
        with self.assertRaises(OperacaoRecusada):
            self.servico.cancelar_titulo(OPERADOR, t.id, "cliente desistiu")
        self.assertIs(self.armazenado(t.id).estado, EstadoTitulo.ABERTO)

    def test_CA_18_E4_recusa_cancelamento_sem_motivo(self):
        t = self.novo_titulo()
        with self.assertRaises(OperacaoRecusada):
            self.servico.cancelar_titulo(DONO, t.id, None)
        self.assertIs(self.armazenado(t.id).estado, EstadoTitulo.ABERTO)

    def test_CA_19_recusa_cancelamento_de_titulo_baixado(self):
        t, _ = self.baixado_por_pagamento(FUTURO)
        with self.assertRaises(OperacaoRecusada):
            self.servico.cancelar_titulo(DONO, t.id, "motivo")
        self.assertIs(self.armazenado(t.id).estado, EstadoTitulo.BAIXADO)

    def test_CA_20_titulo_proximo_do_vencimento_e_sinalizado_e_continua_aberto(self):
        self.novo_titulo(vencimento=HOJE + timedelta(days=3))
        [visao] = self.servico.consultar_titulos(FiltroTitulos(), HOJE, antecedencia_dias=5)
        self.assertTrue(visao.proximo_do_vencimento)
        self.assertIs(visao.estado, EstadoTitulo.ABERTO)

    def test_CA_21_filtra_por_cliente_e_estado(self):
        vencido_c1 = self.novo_titulo(cliente="c1", vencimento=ONTEM)
        self.novo_titulo(cliente="c1", vencimento=FUTURO)
        self.novo_titulo(cliente="c2", vencimento=ONTEM)
        self.servico.verificar_vencimentos(OPERADOR, HOJE)
        visoes = self.servico.consultar_titulos(
            FiltroTitulos(cliente_id="c1", estado=EstadoTitulo.VENCIDO), HOJE, 5
        )
        self.assertEqual([v.id for v in visoes], [vencido_c1.id])

    def test_CA_21_filtra_por_periodo_de_vencimento(self):
        dentro = self.novo_titulo(vencimento=HOJE + timedelta(days=10))
        self.novo_titulo(vencimento=HOJE + timedelta(days=40))
        visoes = self.servico.consultar_titulos(
            FiltroTitulos(vencimento_de=HOJE, vencimento_ate=HOJE + timedelta(days=15)), HOJE, 5
        )
        self.assertEqual([v.id for v in visoes], [dentro.id])

    def test_CA_22_pagamento_gera_registro_de_auditoria(self):
        t = self.novo_titulo()
        self.servico.registrar_pagamento(OPERADOR, t.id, R("400.00"), HOJE)
        registro = self.auditoria.registros[-1]
        self.assertEqual(registro.usuario_id, OPERADOR.id)
        self.assertEqual(registro.data_hora, datetime(2026, 10, 3, 10, 0))
        self.assertEqual(registro.operacao, "registrar pagamento")
        self.assertEqual(registro.registro_afetado, f"titulo {t.id}")

    def test_CA_22_RB_01_mudancas_de_estado_sao_auditadas(self):
        t, pagamento_id = self.baixado_por_pagamento(FUTURO)
        self.servico.estornar_pagamento(DONO, t.id, pagamento_id, "cheque devolvido", HOJE)
        self.servico.cancelar_titulo(DONO, t.id, "cliente desistiu")
        mudancas = [
            (r.valor_anterior, r.valor_novo, r.usuario_id)
            for r in self.auditoria.registros
            if r.operacao == "mudar estado"
        ]
        self.assertEqual(
            mudancas,
            [("Aberto", "Baixado", "operador"), ("Baixado", "Aberto", "dono"), ("Aberto", "Cancelado", "dono")],
        )

    def test_CA_23_falha_na_auditoria_desfaz_o_pagamento(self):
        t = self.novo_titulo()
        registros_antes = list(self.auditoria.registros)
        self.auditoria.falhar = True
        with self.assertRaises(RuntimeError):
            self.servico.registrar_pagamento(OPERADOR, t.id, R("1000.00"), HOJE)
        salvo = self.armazenado(t.id)
        self.assertEqual(salvo.pagamentos, [])
        self.assertEqual(salvo.saldo, R("1000.00"))
        self.assertIs(salvo.estado, EstadoTitulo.ABERTO)
        self.assertEqual(self.auditoria.registros, registros_antes)

    def test_CA_24_saldo_e_valor_menos_pagamentos_nao_estornados(self):
        aleatorio = random.Random(6)
        for rodada in range(50):
            with self.subTest(rodada=rodada):
                t = self.novo_titulo(vencimento=FUTURO)
                for _ in range(15):
                    salvo = self.armazenado(t.id)
                    validos = [p for p in salvo.pagamentos if not p.estornado]
                    if validos and aleatorio.random() < 0.3:
                        p = aleatorio.choice(validos)
                        self.servico.estornar_pagamento(DONO, t.id, p.id, "teste", HOJE)
                    elif salvo.saldo > 0:
                        centavos = aleatorio.randint(1, int(salvo.saldo * 100))
                        self.servico.registrar_pagamento(
                            OPERADOR, t.id, Decimal(centavos) / 100, HOJE
                        )
                    salvo = self.armazenado(t.id)
                    pago = sum((p.valor for p in salvo.pagamentos if not p.estornado), Decimal(0))
                    self.assertEqual(salvo.saldo, salvo.valor - pago)
                    self.assertTrue(Decimal(0) <= salvo.saldo <= salvo.valor)
                    self.assertEqual(salvo.estado is EstadoTitulo.BAIXADO, salvo.saldo == 0)


if __name__ == "__main__":
    unittest.main()
