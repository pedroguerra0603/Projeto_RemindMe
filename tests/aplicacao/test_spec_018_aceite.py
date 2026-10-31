"""Critérios de aceitação da Spec 018: fornecedores e contas a pagar (UC-15)."""

import unittest
from datetime import date, datetime, timedelta
from decimal import Decimal

from remindme.aplicacao.servico_clientes import ServicoClientes
from remindme.aplicacao.servico_contas_pagar import FiltroContas, ServicoContasPagar
from remindme.aplicacao.servico_fornecedores import ServicoFornecedores
from remindme.dominio.conta_pagar import EstadoContaPagar
from remindme.dominio.erros import OperacaoNegada, OperacaoRecusada
from remindme.dominio.usuario import Perfil, Usuario
from remindme.infraestrutura.memoria import RelogioFixo, UnidadeDeTrabalhoEmMemoria
from tests.apoio import ComSessoes

HOJE = date(2026, 10, 3)
DONO = Usuario("dono", "Carla Menezes", Perfil.DONO)
OPERADOR = Usuario("operador", "Diego Ramos", Perfil.OPERADOR_FINANCEIRO)
CONTADOR = Usuario("contador", "Helena Prado", Perfil.CONTADOR)

CNPJ = "11.222.333/0001-81"
CPF = "529.982.247-25"


class Base(ComSessoes, unittest.TestCase):
    def setUp(self):
        self.uow = UnidadeDeTrabalhoEmMemoria()
        self.relogio = RelogioFixo(datetime(2026, 10, 3, 15, 0))
        self.fornecedores = ServicoFornecedores(self.uow, self.relogio)
        self.contas = ServicoContasPagar(self.uow, self.relogio)
        self.operador = self.sessao(OPERADOR)
        self.dono = self.sessao(DONO)
        self.contador = self.sessao(CONTADOR)

    def fornecedor(self, nome="Distribuidora de Pneus Ltda", documento=CNPJ, contato="vendas@pneus.example"):
        return self.fornecedores.cadastrar_fornecedor(self.operador, nome, documento, contato)

    def auditoria_de(self, referencia):
        return [r for r in self.uow.auditoria.registros if r.registro_afetado == referencia]


class Fornecedores(Base):
    def test_CA_01_cadastro_guarda_o_documento_sem_pontuacao_e_audita_os_tres_campos(self):
        fornecedor = self.fornecedor()
        self.assertEqual(self.uow.fornecedores.obter(fornecedor.id).documento, "11222333000181")
        self.assertEqual(
            {(r.campo, r.valor_anterior, r.valor_novo, r.usuario_id) for r in self.auditoria_de(f"fornecedor {fornecedor.id}")},
            {
                ("nome", None, "Distribuidora de Pneus Ltda", OPERADOR.id),
                ("documento", None, "11222333000181", OPERADOR.id),
                ("contato", None, "vendas@pneus.example", OPERADOR.id),
            },
        )

    def test_CA_02_INV_6_documento_repetido_com_ou_sem_pontuacao_e_recusado_no_campo(self):
        self.fornecedor()
        with self.assertRaises(OperacaoRecusada) as ctx:
            self.fornecedor(nome="Outra Distribuidora", documento="11222333000181")
        self.assertIn("documento", ctx.exception.campos)
        self.assertEqual(len(self.uow.fornecedores.listar()), 1)

    def test_E1_dados_invalidos_indicam_cada_campo_e_nomeiam_o_fornecedor(self):
        with self.assertRaises(OperacaoRecusada) as ctx:
            self.fornecedor(nome=" ", documento="123", contato="")
        self.assertEqual(set(ctx.exception.campos), {"nome", "documento", "contato"})
        self.assertIn("fornecedor", ctx.exception.campos["nome"])

    def test_fornecedor_pode_ter_o_documento_de_um_cliente(self):
        ServicoClientes(self.uow, self.relogio).cadastrar_cliente(self.operador, "Padaria", CNPJ, "p@padaria.example")
        self.assertEqual(self.fornecedor().documento, "11222333000181")

    def test_A6_alteracao_registra_so_os_campos_que_mudaram(self):
        fornecedor = self.fornecedor()
        self.fornecedores.alterar_fornecedor(self.operador, fornecedor.id, "Distribuidora de Pneus Ltda", CNPJ, "(11) 3456-7890")
        alteracoes = [r for r in self.auditoria_de(f"fornecedor {fornecedor.id}") if r.valor_anterior is not None]
        self.assertEqual([(r.campo, r.valor_anterior, r.valor_novo) for r in alteracoes], [("contato", "vendas@pneus.example", "1134567890")])

    def test_A5_pesquisa_por_parte_do_nome_ou_pelo_documento(self):
        self.fornecedor()
        self.fornecedor(nome="Auto Peças Silva", documento=CPF, contato="(11) 98765-4321")
        self.assertEqual([f.nome for f in self.fornecedores.consultar_fornecedores(self.contador, "pneus")], ["Distribuidora de Pneus Ltda"])
        self.assertEqual([f.nome for f in self.fornecedores.consultar_fornecedores(self.contador, "529.982")], ["Auto Peças Silva"])
        self.assertEqual(len(self.fornecedores.consultar_fornecedores(self.contador)), 2)

    def test_CA_13_RB_03_contador_consulta_mas_nao_cadastra_fornecedor(self):
        with self.assertRaises(OperacaoNegada):
            self.fornecedores.cadastrar_fornecedor(self.contador, "Distribuidora", CNPJ, "v@d.example")


class ContasAPagar(Base):
    def setUp(self):
        super().setUp()
        self.pneus = self.fornecedor()

    def conta(self, valor="1200.00", dias=10, fornecedor=None, descricao="20 pneus aro 14"):
        fornecedor_id = (fornecedor or self.pneus).id
        return self.contas.cadastrar_conta(
            self.operador, fornecedor_id, descricao, Decimal(valor), HOJE + timedelta(days=dias), "Boleto"
        )

    def test_CA_03_conta_nasce_aberta_com_saldo_e_auditoria(self):
        conta = self.conta()
        salva = self.uow.contas_pagar.obter(conta.id)
        self.assertEqual((salva.estado, salva.saldo), (EstadoContaPagar.ABERTA, Decimal("1200.00")))
        [registro] = self.auditoria_de(f"conta_pagar {conta.id}")
        self.assertEqual((registro.operacao, registro.valor_novo), ("cadastrar conta a pagar", "Aberta"))

    def test_CA_04_fornecedor_inexistente_descricao_vazia_ou_valor_zero_nao_gravam_nada(self):
        for dados in (
            dict(fornecedor_id="nao-existe", descricao="Pneus", valor=Decimal("10.00")),
            dict(fornecedor_id=self.pneus.id, descricao=" ", valor=Decimal("10.00")),
            dict(fornecedor_id=self.pneus.id, descricao="Pneus", valor=Decimal("0.00")),
        ):
            with self.subTest(dados=dados), self.assertRaises(OperacaoRecusada):
                self.contas.cadastrar_conta(self.operador, dados["fornecedor_id"], dados["descricao"], dados["valor"], HOJE)
        self.assertEqual(self.uow.contas_pagar.listar(), [])

    def test_CA_05_pagamento_parcial_e_depois_integral(self):
        conta = self.conta()
        self.contas.registrar_pagamento(self.operador, conta.id, Decimal("500.00"), HOJE)
        conta = self.contas.registrar_pagamento(self.operador, conta.id, Decimal("700.00"), HOJE)
        self.assertEqual((conta.estado, conta.saldo), (EstadoContaPagar.PAGA, Decimal("0.00")))
        estados = [r.valor_novo for r in self.auditoria_de(f"conta_pagar {conta.id}") if r.campo == "estado"]
        self.assertEqual(estados, ["Aberta", "Paga"])

    def test_CA_06_pagamento_invalido_nao_muda_o_saldo(self):
        conta = self.conta("700.00")
        for valor, data in (("700.01", HOJE), ("0.00", HOJE), ("10.00", HOJE + timedelta(days=1))):
            with self.subTest(valor=valor, data=data), self.assertRaises(OperacaoRecusada):
                self.contas.registrar_pagamento(self.operador, conta.id, Decimal(valor), data)
        self.assertEqual(self.uow.contas_pagar.obter(conta.id).saldo, Decimal("700.00"))

    def test_CA_08_verificacao_automatica_vence_a_conta_com_registro_automatico(self):
        ontem, hoje = self.conta(dias=-1), self.conta(dias=0)
        self.assertEqual(self.contas.verificar_vencimentos_automaticamente(HOJE), [ontem.id])
        self.assertIs(self.uow.contas_pagar.obter(hoje.id).estado, EstadoContaPagar.ABERTA)
        [registro] = [r for r in self.auditoria_de(f"conta_pagar {ontem.id}") if r.valor_novo == "Vencida"]
        self.assertTrue(registro.automatica)
        self.assertIsNone(registro.usuario_id)

    def test_CA_09_estorno_pelo_dono_de_conta_paga_vencida(self):
        conta = self.conta("80.00", dias=-5)
        conta = self.contas.registrar_pagamento(self.operador, conta.id, Decimal("80.00"), HOJE)
        conta = self.contas.estornar_pagamento(self.dono, conta.id, conta.pagamentos[0].id, "Boleto em duplicidade", HOJE)
        self.assertEqual((conta.estado, conta.saldo), (EstadoContaPagar.VENCIDA, Decimal("80.00")))

    def test_CA_10_RB_33_operador_nao_estorna_nem_cancela_e_o_dono_precisa_de_motivo(self):
        conta = self.contas.registrar_pagamento(self.operador, self.conta().id, Decimal("100.00"), HOJE)
        pagamento = conta.pagamentos[0].id
        with self.assertRaisesRegex(OperacaoNegada, "RB-33"):
            self.contas.estornar_pagamento(self.operador, conta.id, pagamento, "Motivo", HOJE)
        with self.assertRaisesRegex(OperacaoNegada, "RB-33"):
            self.contas.cancelar_conta(self.operador, conta.id, "Motivo")
        with self.assertRaises(OperacaoRecusada):
            self.contas.estornar_pagamento(self.dono, conta.id, pagamento, "", HOJE)
        self.assertEqual(self.uow.contas_pagar.obter(conta.id).saldo, Decimal("1100.00"))

    def test_CA_11_cancelamento_pelo_dono_guarda_o_motivo_na_auditoria(self):
        conta = self.contas.cancelar_conta(self.dono, self.conta().id, "Compra desfeita")
        self.assertIs(conta.estado, EstadoContaPagar.CANCELADA)
        [registro] = [r for r in self.auditoria_de(f"conta_pagar {conta.id}") if r.valor_novo == "Cancelada"]
        self.assertEqual((registro.motivo, registro.usuario_id), ("Compra desfeita", DONO.id))

    def test_CA_12_filtro_por_fornecedor_e_estado_ordenado_por_vencimento(self):
        pecas = self.fornecedor(nome="Auto Peças Silva", documento=CPF, contato="(11) 98765-4321")
        self.conta(dias=-2, descricao="b")
        self.conta(dias=-9, descricao="a")
        self.conta(dias=-3, fornecedor=pecas)
        self.conta(dias=5)
        self.contas.verificar_vencimentos_automaticamente(HOJE)
        visoes = self.contas.consultar_contas(
            self.contador, FiltroContas(fornecedor_id=self.pneus.id, estado=EstadoContaPagar.VENCIDA)
        )
        self.assertEqual([v.descricao for v in visoes], ["a", "b"])
        self.assertTrue(all(v.fornecedor_id == self.pneus.id and v.saldo == v.valor for v in visoes))
        periodo = self.contas.consultar_contas(self.contador, FiltroContas(vencimento_de=HOJE, vencimento_ate=HOJE + timedelta(days=5)))
        self.assertEqual(len(periodo), 1)

    def test_CA_13_RB_03_contador_consulta_mas_nao_cadastra_nem_paga(self):
        conta = self.conta()
        self.assertEqual(self.contas.obter_conta(self.contador, conta.id).id, conta.id)
        with self.assertRaisesRegex(OperacaoNegada, "RB-03"):
            self.contas.cadastrar_conta(self.contador, self.pneus.id, "Pneus", Decimal("1.00"), HOJE)
        with self.assertRaisesRegex(OperacaoNegada, "RB-03"):
            self.contas.registrar_pagamento(self.contador, conta.id, Decimal("1.00"), HOJE)

    def test_OPEN_25_pedido_repetido_nao_registra_de_novo_nem_audita(self):
        conta = self.conta()
        self.contas.registrar_pagamento(self.operador, conta.id, Decimal("100.00"), HOJE, pedido_id="x")
        antes = len(self.uow.auditoria.registros)
        conta = self.contas.registrar_pagamento(self.operador, conta.id, Decimal("100.00"), HOJE, pedido_id="x")
        self.assertEqual((len(conta.pagamentos), len(self.uow.auditoria.registros)), (1, antes))

    def test_E6_RNF_09_falha_da_auditoria_desfaz_o_pagamento(self):
        conta = self.conta()
        self.uow.auditoria.falhar = True
        with self.assertRaises(RuntimeError):
            self.contas.registrar_pagamento(self.operador, conta.id, Decimal("100.00"), HOJE)
        self.assertEqual(self.uow.contas_pagar.obter(conta.id).pagamentos, [])


if __name__ == "__main__":
    unittest.main()
