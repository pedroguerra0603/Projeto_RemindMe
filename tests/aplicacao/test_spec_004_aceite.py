"""Critérios de aceitação da Spec 004: orçamento, itens, valores e alçada de desconto (UC-04, UC-05)."""

import unittest
from datetime import date, datetime
from decimal import Decimal

from remindme.aplicacao.servico_orcamentos import FiltroOrcamentos, ServicoOrcamentos
from remindme.dominio.cliente import Cliente
from remindme.dominio.erros import OperacaoNegada, OperacaoRecusada
from remindme.dominio.orcamento import EstadoOrcamento
from remindme.dominio.usuario import Perfil, Usuario
from remindme.infraestrutura.memoria import RelogioFixo, UnidadeDeTrabalhoEmMemoria
from tests.apoio import ComSessoes

HOJE = date(2026, 10, 29)
OPERADOR = Usuario("operador", "Diego Ramos", Perfil.OPERADOR_FINANCEIRO)
DONO = Usuario("dono", "Carla Menezes", Perfil.DONO)
CONTADOR = Usuario("contador", "Helena Prado", Perfil.CONTADOR)


class Base(ComSessoes, unittest.TestCase):
    def setUp(self):
        self.uow = UnidadeDeTrabalhoEmMemoria()
        self.uow.clientes.salvar(Cliente("c1", "Padaria Pão Quente Ltda", "11222333000181", "a@padaria.com.br"))
        self.uow.clientes.salvar(Cliente("c2", "Sérgio Tavares", "52998224725", "11987654321"))
        self.servico = ServicoOrcamentos(self.uow, RelogioFixo(datetime(2026, 10, 29, 12, 0)))
        self.operador = self.sessao(OPERADOR)
        self.dono = self.sessao(DONO)
        self.contador = self.sessao(CONTADOR)

    def criar(self, cliente="c1", itens=(("Revisão do forno", "1", "1000.00"),)):
        o = self.servico.criar_orcamento(self.operador, cliente, "Boleto, 28 dias")
        for descricao, quantidade, unitario in itens:
            o = self.servico.incluir_item(self.operador, o.id, descricao, Decimal(quantidade), Decimal(unitario))
        return o

    def registros(self, orcamento, campo=None):
        return [
            r
            for r in self.uow.auditoria.registros
            if r.registro_afetado.startswith(f"orcamento {orcamento.id}") and (campo is None or r.campo == campo)
        ]

    def fotografia(self):
        return {k: (v.estado, v.percentual_desconto, list(v.itens)) for k, v in self.uow.orcamentos.dados.items()}, len(
            self.uow.auditoria.registros
        )


class Spec004(Base):
    def test_CA_01_RF_06_cria_em_rascunho_para_cliente_cadastrado_e_audita(self):
        o = self.servico.criar_orcamento(self.operador, "c1", "Pix")
        guardado = self.uow.orcamentos.obter(o.id)
        self.assertEqual((guardado.estado, guardado.elaborado_por, guardado.criado_em), (EstadoOrcamento.RASCUNHO, "operador", HOJE))
        (registro,) = self.registros(o, "estado")
        self.assertEqual((registro.valor_anterior, registro.valor_novo, registro.usuario_id), (None, "Rascunho", "operador"))

    def test_CA_02_cliente_inexistente_e_recusado_no_campo_cliente(self):
        with self.assertRaises(OperacaoRecusada) as ctx:
            self.servico.criar_orcamento(self.operador, "nao-existe")
        self.assertEqual(set(ctx.exception.campos), {"cliente"})
        self.assertEqual(self.uow.orcamentos.dados, {})

    def test_CA_03_RF_07_RF_18_itens_recalculam_e_auditam_o_valor(self):
        o = self.criar(itens=(("Revisão", "2", "150.00"),))
        item_id = o.itens[0].id
        o = self.servico.alterar_item(self.operador, o.id, item_id, "Revisão completa", Decimal("3"), Decimal("150.00"))
        self.assertEqual(o.valor_liquido, Decimal("450.00"))
        o = self.servico.remover_item(self.operador, o.id, item_id)
        self.assertEqual(o.valor_liquido, Decimal("0.00"))
        valores = [(r.valor_anterior, r.valor_novo) for r in self.registros(o, "valor")]
        self.assertEqual(valores, [("0.00", "300.00"), ("300.00", "450.00"), ("450.00", "0.00")])
        itens = [(r.valor_anterior, r.valor_novo) for r in self.registros(o, "item")]
        self.assertEqual(itens[-1], ("Revisão completa: 3 × 150.00", None))

    def test_CA_04_RF_15_desconto_dentro_da_alcada_e_aplicado_e_auditado(self):
        o = self.criar()
        o = self.servico.informar_desconto(self.operador, o.id, Decimal("10"))
        self.assertEqual((o.estado, o.valor_liquido), (EstadoOrcamento.RASCUNHO, Decimal("900.00")))
        (registro,) = self.registros(o, "desconto")
        self.assertEqual((registro.valor_anterior, registro.valor_novo), ("0.00", "10.00"))

    def test_CA_05_RF_16_desconto_acima_da_alcada_fica_pendente_de_alcada(self):
        o = self.criar()
        o = self.servico.informar_desconto(self.operador, o.id, Decimal("15"))
        self.assertEqual((o.estado, o.percentual_desconto), (EstadoOrcamento.PENDENTE_DE_ALCADA, Decimal("0.00")))
        estados = [(r.valor_anterior, r.valor_novo) for r in self.registros(o, "estado")]
        self.assertEqual(estados[-1], ("Rascunho", "Pendente de Alçada"))
        self.assertEqual([x.id for x in self.servico.pendentes_de_decisao(self.dono)], [o.id])

    def test_CA_06_RF_17_dono_aprova_e_a_decisao_fica_registrada(self):
        o = self.criar()
        self.servico.informar_desconto(self.operador, o.id, Decimal("15"))
        o = self.servico.decidir_desconto(self.dono, o.id, True)
        self.assertEqual((o.estado, o.percentual_desconto, o.valor_liquido), (EstadoOrcamento.RASCUNHO, Decimal("15.00"), Decimal("850.00")))
        (decisao,) = o.decisoes
        self.assertEqual((decisao.aprovado, decisao.decidido_por, decisao.data), (True, "dono", HOJE))
        (registro,) = self.registros(o, "decisão do desconto")
        self.assertEqual(registro.usuario_id, "dono")
        self.assertIsNone(o.motivo_para_nao_enviar())

    def test_CA_07_UC_05_A2_aprovacao_menor_registra_solicitado_e_aprovado(self):
        o = self.criar()
        self.servico.informar_desconto(self.operador, o.id, Decimal("20"))
        o = self.servico.decidir_desconto(self.dono, o.id, True, Decimal("12"))
        self.assertEqual(o.percentual_desconto, Decimal("12.00"))
        (registro,) = self.registros(o, "decisão do desconto")
        self.assertEqual(registro.valor_novo, "aprovado 12.00% de 20.00% solicitados")

    def test_CA_08_UC_05_A1_rejeicao_volta_a_rascunho_com_o_desconto_anterior(self):
        o = self.criar()
        self.servico.informar_desconto(self.operador, o.id, Decimal("8"))
        self.servico.informar_desconto(self.operador, o.id, Decimal("30"))
        o = self.servico.decidir_desconto(self.dono, o.id, False)
        self.assertEqual((o.estado, o.percentual_desconto), (EstadoOrcamento.RASCUNHO, Decimal("8.00")))

    def test_CA_09_RNF_03_operador_nao_decide_nem_chamando_o_servico(self):
        o = self.criar()
        self.servico.informar_desconto(self.operador, o.id, Decimal("30"))
        antes = self.fotografia()
        with self.assertRaises(OperacaoNegada) as ctx:
            self.servico.decidir_desconto(self.operador, o.id, True)
        self.assertIn("RB-15", ctx.exception.motivo)
        self.assertEqual(self.fotografia(), antes)

    def test_CA_10_RB_15_dono_concede_qualquer_desconto_sem_pendencia(self):
        o = self.criar()
        o = self.servico.informar_desconto(self.dono, o.id, Decimal("40"))
        self.assertEqual((o.estado, o.percentual_desconto), (EstadoOrcamento.RASCUNHO, Decimal("40.00")))

    def test_CA_11_RB_03_contador_nao_cria_nem_conduz_orcamento(self):
        o = self.criar()
        antes = self.fotografia()
        for tentativa in (
            lambda: self.servico.criar_orcamento(self.contador, "c1"),
            lambda: self.servico.incluir_item(self.contador, o.id, "X", Decimal("1"), Decimal("1.00")),
            lambda: self.servico.consultar_orcamentos(self.contador),
        ):
            with self.assertRaises(OperacaoNegada):
                tentativa()
        self.assertEqual(self.fotografia(), antes)

    def test_CA_12_RF_13_cancelamento_exige_motivo_e_fica_auditado(self):
        o = self.criar()
        with self.assertRaises(OperacaoRecusada):
            self.servico.cancelar_orcamento(self.operador, o.id, "")
        o = self.servico.cancelar_orcamento(self.operador, o.id, "Cliente desistiu")
        registro = self.registros(o, "estado")[-1]
        self.assertEqual((registro.valor_novo, registro.motivo), ("Cancelado", "Cliente desistiu"))

    def test_CA_13_RF_10_consulta_filtra_por_cliente_estado_e_periodo(self):
        a = self.criar("c1")
        b = self.criar("c2")
        self.servico.cancelar_orcamento(self.operador, b.id, "Desistiu")
        por_cliente = self.servico.consultar_orcamentos(self.operador, FiltroOrcamentos(cliente_id="c2"))
        self.assertEqual([o.id for o in por_cliente], [b.id])
        por_estado = self.servico.consultar_orcamentos(self.operador, FiltroOrcamentos(estado=EstadoOrcamento.RASCUNHO))
        self.assertEqual([o.id for o in por_estado], [a.id])
        fora = self.servico.consultar_orcamentos(self.operador, FiltroOrcamentos(criado_de=date(2026, 10, 30)))
        self.assertEqual(fora, [])

    def test_CA_14_RF_07_pendente_de_alcada_nao_aceita_itens(self):
        o = self.criar()
        self.servico.informar_desconto(self.operador, o.id, Decimal("30"))
        antes = self.fotografia()
        with self.assertRaises(OperacaoRecusada) as ctx:
            self.servico.incluir_item(self.operador, o.id, "Outro", Decimal("1"), Decimal("10.00"))
        self.assertIn("Pendente de Alçada", ctx.exception.motivo)
        self.assertEqual(self.fotografia(), antes)

    def test_CA_15_RB_24_orcamento_sem_item_nao_esta_pronto_para_envio(self):
        o = self.servico.criar_orcamento(self.operador, "c1")
        self.assertIn("RB-24", o.motivo_para_nao_enviar())

    def test_CA_16_recusa_nao_altera_dados_nem_deixa_auditoria(self):
        o = self.criar()
        antes = self.fotografia()
        with self.assertRaises(OperacaoRecusada):
            self.servico.incluir_item(self.operador, o.id, "", Decimal("0"), Decimal("-1"))
        with self.assertRaises(OperacaoRecusada):
            self.servico.informar_desconto(self.operador, o.id, Decimal("101"))
        self.assertEqual(self.fotografia(), antes)

    def test_sem_sessao_nada_e_feito(self):
        with self.assertRaises(OperacaoRecusada):
            self.servico.criar_orcamento(None, "c1")
        self.assertEqual(self.uow.orcamentos.dados, {})


if __name__ == "__main__":
    unittest.main()
