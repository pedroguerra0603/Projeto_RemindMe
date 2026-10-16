"""Regras de negócio e invariantes da Spec 006 (seção 5), verificadas de forma exaustiva no domínio
e por perfil na aplicação."""

import copy
import random
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
ONTEM = HOJE - timedelta(days=1)
A, V, B, C = EstadoTitulo.ABERTO, EstadoTitulo.VENCIDO, EstadoTitulo.BAIXADO, EstadoTitulo.CANCELADO
RECUSA = "recusa"

# Transições do título implementadas na Spec 006 (docs/uml/estados.md, sem Em Renegociação).
TRANSICOES_VALIDAS = {(A, V), (A, B), (V, B), (B, A), (B, V), (A, C), (V, C)}


def titulo_em(estado):
    """Título de R$ 1.000,00 vencido ontem, levado ao estado solicitado. Aberto, Vencido e Cancelado
    ficam com um pagamento parcial de R$ 100,00; Baixado, com um de R$ 1.000,00."""
    t = Titulo.cadastrar_manual("t1", "c1", Decimal("1000.00"), ONTEM)
    if estado is B:
        t.registrar_pagamento("p1", Decimal("1000.00"), HOJE)
        return t
    t.registrar_pagamento("p1", Decimal("100.00"), HOJE)
    if estado is V:
        t.marcar_vencido(HOJE)
    if estado is C:
        t.cancelar("motivo")
    return t


OPERACOES = {
    "pagamento parcial": lambda t: t.registrar_pagamento("p2", Decimal("1.00"), HOJE),
    "pagamento do saldo": lambda t: t.registrar_pagamento("p2", max(t.saldo, Decimal("0.01")), HOJE),
    "verificação de vencimento": lambda t: t.marcar_vencido(HOJE),
    "estorno": lambda t: t.estornar_pagamento("p1", "motivo", HOJE),
    "cancelamento": lambda t: t.cancelar("motivo"),
}

# Estado resultante esperado de cada operação em cada estado, ou recusa.
ESPERADO = {
    A: {"pagamento parcial": A, "pagamento do saldo": B, "verificação de vencimento": V, "estorno": A, "cancelamento": C},
    V: {"pagamento parcial": V, "pagamento do saldo": B, "verificação de vencimento": V, "estorno": V, "cancelamento": C},
    B: {"pagamento parcial": RECUSA, "pagamento do saldo": RECUSA, "verificação de vencimento": B, "estorno": V, "cancelamento": RECUSA},
    C: {"pagamento parcial": RECUSA, "pagamento do saldo": RECUSA, "verificação de vencimento": C, "estorno": RECUSA, "cancelamento": RECUSA},
}


def verificar_invariantes(caso, t, valor_original, pagamentos_antes):
    pago = sum((p.valor for p in t.pagamentos if not p.estornado), Decimal(0))
    caso.assertEqual(t.saldo, t.valor - pago)  # INV-1
    caso.assertTrue(Decimal(0) <= t.saldo <= t.valor)  # INV-2
    caso.assertEqual(t.estado is B, t.saldo == 0)  # INV-3, RB-22
    caso.assertIsInstance(t.estado, EstadoTitulo)  # INV-4
    caso.assertEqual(t.valor, valor_original)  # INV-5
    caso.assertEqual([p.id for p in t.pagamentos[: len(pagamentos_antes)]], pagamentos_antes)  # INV-6


class RB21TabelaDeTransicoes(unittest.TestCase):
    def test_RB_21_cada_operacao_em_cada_estado(self):
        for estado, esperados in ESPERADO.items():
            for nome, operacao in OPERACOES.items():
                with self.subTest(estado=estado.value, operacao=nome):
                    t = titulo_em(estado)
                    antes = copy.deepcopy(t)
                    if esperados[nome] is RECUSA:
                        with self.assertRaises(OperacaoRecusada):
                            operacao(t)
                        self.assertEqual(t, antes)
                    else:
                        operacao(t)
                        self.assertIs(t.estado, esperados[nome])

    def test_INV_4_toda_mudanca_de_estado_esta_na_tabela(self):
        for estado in ESPERADO:
            for operacao in OPERACOES.values():
                t = titulo_em(estado)
                try:
                    operacao(t)
                except OperacaoRecusada:
                    continue
                if t.estado is not estado:
                    with self.subTest(de=estado.value, para=t.estado.value):
                        self.assertIn((estado, t.estado), TRANSICOES_VALIDAS)

    def test_INV_4_cancelado_e_final(self):
        t = titulo_em(C)
        for nome, operacao in OPERACOES.items():
            with self.subTest(operacao=nome):
                try:
                    operacao(t)
                except OperacaoRecusada:
                    pass
                self.assertIs(t.estado, C)


class InvariantesEmSequenciasAleatorias(unittest.TestCase):
    def test_INV_1_a_INV_6_valem_depois_de_cada_operacao(self):
        """200 sequências de 20 operações, inclusive vencimento, cancelamento e operações recusadas."""
        aleatorio = random.Random(67)
        for rodada in range(200):
            vencimento = HOJE + timedelta(days=aleatorio.randint(-5, 5))
            valor = Decimal(aleatorio.randint(1, 500_000)) / 100
            t = Titulo.cadastrar_manual("t", "c", valor, vencimento)
            data = HOJE
            for passo in range(20):
                data += timedelta(days=aleatorio.randint(0, 2))
                ids_antes = [p.id for p in t.pagamentos]
                estado_antes = t.estado
                escolha = aleatorio.random()
                try:
                    if escolha < 0.45:
                        limite = int(max(t.saldo, Decimal("0.01")) * 100) + 2
                        centavos = aleatorio.randint(-1, limite)
                        t.registrar_pagamento(f"p{passo}", Decimal(centavos) / 100, data)
                    elif escolha < 0.70 and t.pagamentos:
                        p = aleatorio.choice(t.pagamentos)
                        t.estornar_pagamento(p.id, "motivo", data)
                    elif escolha < 0.95:
                        t.marcar_vencido(data)
                    else:
                        t.cancelar("motivo")
                except OperacaoRecusada:
                    pass
                with self.subTest(rodada=rodada, passo=passo):
                    verificar_invariantes(self, t, valor, ids_antes)
                    if t.estado is not estado_antes:
                        self.assertIn((estado_antes, t.estado), TRANSICOES_VALIDAS)


class RB23Limites(unittest.TestCase):
    def test_RB_23_limite_do_saldo_depois_de_pagamentos_parciais(self):
        t = titulo_em(A)  # saldo de R$ 900,00
        with self.assertRaises(OperacaoRecusada):
            t.registrar_pagamento("p2", Decimal("900.01"), HOJE)
        t.registrar_pagamento("p2", Decimal("899.99"), HOJE)
        self.assertEqual(t.saldo, Decimal("0.01"))
        with self.assertRaises(OperacaoRecusada):
            t.registrar_pagamento("p3", Decimal("0.02"), HOJE)
        t.registrar_pagamento("p3", Decimal("0.01"), HOJE)
        self.assertIs(t.estado, B)

    def test_RB_23_saldo_restaurado_pelo_estorno_volta_a_aceitar_pagamento(self):
        t = titulo_em(B)
        t.estornar_pagamento("p1", "devolvido", HOJE)
        t.registrar_pagamento("p2", Decimal("1000.00"), HOJE)
        self.assertIs(t.estado, B)
        self.assertEqual(t.saldo, Decimal("0.00"))


class RB22SomenteQuando(unittest.TestCase):
    def test_RB_22_um_centavo_de_saldo_impede_a_baixa(self):
        t = Titulo.cadastrar_manual("t", "c", Decimal("10.00"), HOJE)
        t.registrar_pagamento("p1", Decimal("9.99"), HOJE)
        self.assertIs(t.estado, A)


class RegrasDePerfilNaAplicacao(unittest.TestCase):
    """RB-02 e OPEN-16 valem para todo perfil que não é o Dono, chamando o serviço sem interface (RNF-03)."""

    def setUp(self):
        self.titulos = RepositorioTitulosEmMemoria()
        self.auditoria = AuditoriaEmMemoria()
        self.servico = ServicoTitulos(
            UnidadeDeTrabalhoEmMemoria(self.titulos, self.auditoria),
            ClientesEmMemoria({"c1"}),
            RelogioFixo(datetime(2026, 10, 3, 10, 0)),
        )
        dono = Usuario("dono", "Dono", Perfil.DONO)
        t = self.servico.cadastrar_titulo(dono, "c1", Decimal("100.00"), HOJE)
        self.titulo = self.servico.registrar_pagamento(dono, t.id, Decimal("10.00"), HOJE)

    def outros_perfis(self):
        return [Usuario(p.name, p.value, p) for p in Perfil if p is not Perfil.DONO]

    def test_RB_02_nenhum_outro_perfil_estorna(self):
        pagamento = self.titulo.pagamentos[0].id
        for usuario in self.outros_perfis():
            with self.subTest(perfil=usuario.perfil.value):
                with self.assertRaises(OperacaoRecusada):
                    self.servico.estornar_pagamento(usuario, self.titulo.id, pagamento, "motivo", HOJE)
                self.assertFalse(self.titulos.obter(self.titulo.id).pagamentos[0].estornado)

    def test_OPEN_16_nenhum_outro_perfil_cancela(self):
        for usuario in self.outros_perfis():
            with self.subTest(perfil=usuario.perfil.value):
                with self.assertRaises(OperacaoRecusada):
                    self.servico.cancelar_titulo(usuario, self.titulo.id, "motivo")
                self.assertIs(self.titulos.obter(self.titulo.id).estado, A)

    def test_RB_01_toda_mudanca_de_estado_tem_registro_de_auditoria(self):
        dono = Usuario("dono", "Dono", Perfil.DONO)
        s = self.servico
        s.registrar_pagamento(dono, self.titulo.id, Decimal("90.00"), HOJE)
        s.estornar_pagamento(dono, self.titulo.id, self.titulo.pagamentos[0].id, "motivo", HOJE + timedelta(days=1))
        s.cancelar_titulo(dono, self.titulo.id, "motivo")
        mudancas = [(r.valor_anterior, r.valor_novo) for r in self.auditoria.registros if r.operacao == "mudar estado"]
        self.assertEqual(mudancas, [("Aberto", "Baixado"), ("Baixado", "Vencido"), ("Vencido", "Cancelado")])
        for r in self.auditoria.registros:
            with self.subTest(operacao=r.operacao):
                self.assertTrue(r.usuario_id and r.data_hora and r.operacao and r.registro_afetado)


if __name__ == "__main__":
    unittest.main()
