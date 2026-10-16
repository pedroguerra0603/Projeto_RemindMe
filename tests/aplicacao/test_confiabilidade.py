"""Confiabilidade: falhas injetadas em cada operação da Spec 006 e recuperação (RNF-09, E8, INV-7).

Cenários descritos em docs/qualidade/confiabilidade.md.
"""

import unittest
from datetime import date, datetime, timedelta
from decimal import Decimal

from remindme.aplicacao.servico_titulos import FiltroTitulos, ServicoTitulos
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
DONO = Usuario("dono", "Dono", Perfil.DONO)
OPERADOR = Usuario("operador", "Operador", Perfil.OPERADOR_FINANCEIRO)


class RepositorioQueFalha(RepositorioTitulosEmMemoria):
    """Simula falha de gravação a partir da n-ésima chamada a `salvar`."""

    def __init__(self):
        super().__init__()
        self.falhar_a_partir_de = None
        self.gravacoes = 0

    def salvar(self, titulo):
        self.gravacoes += 1
        if self.falhar_a_partir_de is not None and self.gravacoes >= self.falhar_a_partir_de:
            raise RuntimeError("Falha simulada na gravação do título.")
        super().salvar(titulo)


class Confiabilidade(unittest.TestCase):
    def setUp(self):
        self.titulos = RepositorioQueFalha()
        self.auditoria = AuditoriaEmMemoria()
        self.servico = ServicoTitulos(
            UnidadeDeTrabalhoEmMemoria(self.titulos, self.auditoria),
            ClientesEmMemoria({"c1"}),
            RelogioFixo(datetime(2026, 10, 3, 10, 0)),
        )

    def novo_titulo(self, vencimento=FUTURO):
        return self.servico.cadastrar_titulo(OPERADOR, "c1", Decimal("1000.00"), vencimento)

    def fotografia(self):
        """Estado completo armazenado: títulos e auditoria."""
        return (
            {i: (t.estado, t.saldo, len(t.pagamentos)) for i, t in self.titulos.dados.items()},
            list(self.auditoria.registros),
        )

    def falhar_auditoria(self):
        self.auditoria.falhar = True

    def falhar_gravacao(self):
        self.titulos.falhar_a_partir_de = self.titulos.gravacoes + 1

    def restabelecer(self):
        self.auditoria.falhar = False
        self.titulos.falhar_a_partir_de = None

    # F-01 e F-02: falha em cada operação que altera dados não deixa alteração parcial.

    def test_RNF_09_falha_em_cada_operacao_nao_deixa_alteracao_parcial(self):
        operacoes = {
            "cadastrar": lambda: self.novo_titulo(),
            "registrar pagamento": lambda: self.servico.registrar_pagamento(
                OPERADOR, self.aberto.id, Decimal("1000.00"), HOJE
            ),
            "estornar": lambda: self.servico.estornar_pagamento(
                DONO, self.baixado.id, self.baixado.pagamentos[0].id, "cheque devolvido", HOJE
            ),
            "cancelar": lambda: self.servico.cancelar_titulo(DONO, self.aberto.id, "desistência"),
            "verificar vencimentos": lambda: self.servico.verificar_vencimentos(OPERADOR, HOJE),
        }
        for falha in (self.falhar_auditoria, self.falhar_gravacao):
            for nome, operacao in operacoes.items():
                with self.subTest(falha=falha.__name__, operacao=nome):
                    self.setUp()
                    self.aberto = self.novo_titulo(vencimento=ONTEM)
                    self.baixado = self.novo_titulo()
                    self.baixado = self.servico.registrar_pagamento(
                        OPERADOR, self.baixado.id, Decimal("1000.00"), HOJE
                    )
                    antes = self.fotografia()
                    falha()
                    with self.assertRaises(RuntimeError):
                        operacao()
                    self.assertEqual(self.fotografia(), antes)

    def test_RNF_09_falha_no_meio_do_lote_de_vencimentos_desfaz_o_lote_inteiro(self):
        primeiro = self.novo_titulo(vencimento=ONTEM)
        segundo = self.novo_titulo(vencimento=ONTEM)
        self.titulos.falhar_a_partir_de = self.titulos.gravacoes + 2
        with self.assertRaises(RuntimeError):
            self.servico.verificar_vencimentos(OPERADOR, HOJE)
        for t in (primeiro, segundo):
            self.assertIs(self.titulos.obter(t.id).estado, EstadoTitulo.ABERTO)

    # F-03: depois da falha, o sistema continua operando e a operação pode ser repetida.

    def test_RNF_09_operacao_repetida_depois_da_falha_tem_o_efeito_de_uma_unica_vez(self):
        t = self.novo_titulo()
        self.falhar_auditoria()
        with self.assertRaises(RuntimeError):
            self.servico.registrar_pagamento(OPERADOR, t.id, Decimal("400.00"), HOJE)
        self.restabelecer()
        self.servico.registrar_pagamento(OPERADOR, t.id, Decimal("400.00"), HOJE)
        salvo = self.titulos.obter(t.id)
        self.assertEqual(len(salvo.pagamentos), 1)
        self.assertEqual(salvo.saldo, Decimal("600.00"))

    def test_RNF_09_consulta_continua_disponivel_depois_de_falha(self):
        t = self.novo_titulo()
        self.falhar_gravacao()
        with self.assertRaises(RuntimeError):
            self.servico.registrar_pagamento(OPERADOR, t.id, Decimal("400.00"), HOJE)
        [visao] = self.servico.consultar_titulos(FiltroTitulos(), HOJE, 5)
        self.assertEqual(visao.saldo, Decimal("1000.00"))

    # F-04: a unidade de trabalho volta a ficar pronta para a próxima transação.

    def test_RNF_09_unidade_de_trabalho_fica_pronta_depois_da_falha(self):
        uow = UnidadeDeTrabalhoEmMemoria(self.titulos, self.auditoria)
        with self.assertRaises(ValueError):
            with uow:
                raise ValueError("falha qualquer")
        self.assertIsNone(uow._copia)
        with uow:
            pass

    # F-05: objeto devolvido ao chamador não altera o que está armazenado.

    def test_INV_7_alterar_o_objeto_devolvido_nao_altera_o_armazenado(self):
        t = self.novo_titulo()
        t.estado = EstadoTitulo.BAIXADO
        t.pagamentos.append("intruso")
        salvo = self.titulos.obter(t.id)
        self.assertIs(salvo.estado, EstadoTitulo.ABERTO)
        self.assertEqual(salvo.pagamentos, [])


if __name__ == "__main__":
    unittest.main()
