"""Operações repetidas não duplicam efeito financeiro. Issue #76.

Risco: registrar duas vezes o mesmo pagamento, baixar o título duas vezes ou repetir uma etapa da régua
(Americanas 2023, ViaQuatro 2022). Aqui as repetições são em sequência, no mesmo processo. A concorrência
real, com duas transações ao mesmo tempo, depende do banco (OPEN-02). Catálogo em
docs/qualidade/concorrencia-e-idempotencia.md.
"""

import copy
import unittest
from datetime import date, datetime, timedelta
from decimal import Decimal

from remindme.aplicacao.servico_titulos import ServicoTitulos
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
FUTURO = HOJE + timedelta(days=30)
DONO = Usuario("dono", "Dono", Perfil.DONO)
OPERADOR = Usuario("operador", "Operador", Perfil.OPERADOR_FINANCEIRO)


class Base(unittest.TestCase):
    def setUp(self):
        self.titulos = RepositorioTitulosEmMemoria()
        self.auditoria = AuditoriaEmMemoria()
        self.servico = ServicoTitulos(
            UnidadeDeTrabalhoEmMemoria(self.titulos, self.auditoria),
            ClientesEmMemoria({"c1"}),
            RelogioFixo(datetime(2026, 10, 3, 10, 0)),
        )
        self.titulo = self.servico.cadastrar_titulo(OPERADOR, "c1", Decimal("100.00"), FUTURO)

    def salvo(self):
        return self.titulos.obter(self.titulo.id)

    def fotografia(self):
        return copy.deepcopy(self.titulos.dados), list(self.auditoria.registros)


class PagamentosEmSequencia(Base):
    def test_RB_23_segundo_pagamento_que_estoura_o_saldo_e_recusado(self):
        """Dois pagamentos de R$ 60,00 sobre R$ 100,00: o primeiro entra, o segundo é recusado."""
        self.servico.registrar_pagamento(OPERADOR, self.titulo.id, Decimal("60.00"), HOJE)
        antes = self.fotografia()
        with self.assertRaisesRegex(OperacaoRecusada, "maior que o saldo"):
            self.servico.registrar_pagamento(OPERADOR, self.titulo.id, Decimal("60.00"), HOJE)
        self.assertEqual(self.fotografia(), antes)
        self.assertEqual(len(self.salvo().pagamentos), 1)
        self.assertEqual(self.salvo().saldo, Decimal("40.00"))

    def test_RB_23_dois_pagamentos_que_somam_exatamente_o_saldo_baixam_uma_vez(self):
        self.servico.registrar_pagamento(OPERADOR, self.titulo.id, Decimal("60.00"), HOJE)
        self.servico.registrar_pagamento(OPERADOR, self.titulo.id, Decimal("40.00"), HOJE)
        self.assertIs(self.salvo().estado, EstadoTitulo.BAIXADO)
        baixas = [r for r in self.auditoria.registros if r.operacao == "mudar estado" and r.valor_novo == "Baixado"]
        self.assertEqual(len(baixas), 1)

    def test_RB_21_repetir_o_pagamento_integral_nao_baixa_o_titulo_duas_vezes(self):
        """Duplo clique em "Registrar pagamento" com o valor do saldo (caso Americanas)."""
        self.servico.registrar_pagamento(OPERADOR, self.titulo.id, Decimal("100.00"), HOJE)
        antes = self.fotografia()
        with self.assertRaisesRegex(OperacaoRecusada, "Baixado"):
            self.servico.registrar_pagamento(OPERADOR, self.titulo.id, Decimal("100.00"), HOJE)
        self.assertEqual(self.fotografia(), antes)
        self.assertEqual(len(self.salvo().pagamentos), 1)

    def test_RB_23_muitas_repeticoes_nunca_deixam_saldo_negativo(self):
        recusas = 0
        for _ in range(20):
            try:
                self.servico.registrar_pagamento(OPERADOR, self.titulo.id, Decimal("30.00"), HOJE)
            except OperacaoRecusada:
                recusas += 1
        salvo = self.salvo()
        self.assertEqual(len(salvo.pagamentos), 3)
        self.assertEqual(salvo.saldo, Decimal("10.00"))
        self.assertEqual(recusas, 17)

    def test_OPEN_25_sem_identificador_do_pedido_pagamento_parcial_repetido_e_registrado_duas_vezes(self):
        """OPEN-25, decidida em 2026-10-23: a interface envia um identificador do pedido, e o sistema ignora o
        segundo pedido com o mesmo identificador. O identificador nasce com a primeira spec com interface;
        até lá, dois pedidos iguais de pagamento parcial continuam indistinguíveis de dois pagamentos reais."""
        for _ in range(2):
            self.servico.registrar_pagamento(OPERADOR, self.titulo.id, Decimal("30.00"), HOJE)
        self.assertEqual(self.salvo().saldo, Decimal("40.00"))


class EstornoRepetido(Base):
    def setUp(self):
        super().setUp()
        self.servico.registrar_pagamento(OPERADOR, self.titulo.id, Decimal("100.00"), HOJE)
        self.pagamento = self.salvo().pagamentos[0].id

    def test_RF_30_o_mesmo_estorno_pedido_duas_vezes_restaura_o_saldo_uma_unica_vez(self):
        self.servico.estornar_pagamento(DONO, self.titulo.id, self.pagamento, "valor errado", HOJE)
        self.assertEqual(self.salvo().saldo, Decimal("100.00"))
        antes = self.fotografia()
        with self.assertRaisesRegex(OperacaoRecusada, "já foi estornado"):
            self.servico.estornar_pagamento(DONO, self.titulo.id, self.pagamento, "valor errado", HOJE)
        self.assertEqual(self.fotografia(), antes)
        self.assertEqual(self.salvo().saldo, Decimal("100.00"))

    def test_RF_30_o_estorno_repetido_nao_gera_segundo_registro_de_auditoria(self):
        self.servico.estornar_pagamento(DONO, self.titulo.id, self.pagamento, "valor errado", HOJE)
        total = len(self.auditoria.registros)
        for _ in range(3):
            with self.assertRaises(OperacaoRecusada):
                self.servico.estornar_pagamento(DONO, self.titulo.id, self.pagamento, "valor errado", HOJE)
        self.assertEqual(len(self.auditoria.registros), total)

    def test_RF_30_estornar_e_pagar_de_novo_usa_o_saldo_restaurado_uma_vez(self):
        self.servico.estornar_pagamento(DONO, self.titulo.id, self.pagamento, "valor errado", HOJE)
        self.servico.registrar_pagamento(OPERADOR, self.titulo.id, Decimal("100.00"), HOJE)
        with self.assertRaises(OperacaoRecusada):
            self.servico.estornar_pagamento(DONO, self.titulo.id, self.pagamento, "outra vez", HOJE)
        salvo = self.salvo()
        self.assertIs(salvo.estado, EstadoTitulo.BAIXADO)
        self.assertEqual(salvo.saldo, Decimal("0.00"))


class VencimentoRepetido(Base):
    def test_RF_24_verificar_vencimentos_duas_vezes_muda_o_estado_e_audita_uma_vez(self):
        servico = self.servico
        vencido = servico.cadastrar_titulo(OPERADOR, "c1", Decimal("10.00"), HOJE - timedelta(days=1))
        primeira = servico.verificar_vencimentos(OPERADOR, HOJE)
        total = len(self.auditoria.registros)
        segunda = servico.verificar_vencimentos(OPERADOR, HOJE)
        self.assertEqual((primeira, segunda), ([vencido.id], []))
        self.assertEqual(len(self.auditoria.registros), total)


class FalhaNoMeioDoPagamento(Base):
    """A falha injetada em cada ponto do registro de pagamento (RNF-09). Complementa test_confiabilidade."""

    def test_RNF_09_falha_na_auditoria_depois_da_gravacao_desfaz_o_pagamento(self):
        antes = self.fotografia()
        self.auditoria.falhar = True
        with self.assertRaises(RuntimeError):
            self.servico.registrar_pagamento(OPERADOR, self.titulo.id, Decimal("100.00"), HOJE)
        self.assertEqual(self.fotografia(), antes)
        self.assertEqual(self.salvo().saldo, Decimal("100.00"))
        self.assertIs(self.salvo().estado, EstadoTitulo.ABERTO)

    def test_RNF_09_apos_a_falha_o_mesmo_pagamento_pode_ser_repetido_e_conta_uma_vez(self):
        self.auditoria.falhar = True
        with self.assertRaises(RuntimeError):
            self.servico.registrar_pagamento(OPERADOR, self.titulo.id, Decimal("100.00"), HOJE)
        self.auditoria.falhar = False
        self.servico.registrar_pagamento(OPERADOR, self.titulo.id, Decimal("100.00"), HOJE)
        self.assertEqual(len(self.salvo().pagamentos), 1)
        self.assertIs(self.salvo().estado, EstadoTitulo.BAIXADO)


class Pendentes(unittest.TestCase):
    """Casos que dependem de decisão ou de spec ainda não aprovada. Nenhum código é escrito antes."""

    @unittest.skip("Pendente da Spec 008 (régua de cobrança): execução repetida do agendador não repete etapa (DA-08).")
    def test_DA_08_execucao_repetida_da_regua_nao_repete_etapa(self):
        pass

    @unittest.skip("Pendente de OPEN-02 (banco de dados): duas transações simultâneas sobre o mesmo título. "
                   "A unidade de trabalho em memória não é segura para threads; a garantia real vem da "
                   "transação e da restrição do banco.")
    def test_RNF_09_duas_transacoes_simultaneas_no_mesmo_titulo_nao_estouram_o_saldo(self):
        pass


if __name__ == "__main__":
    unittest.main()
