"""Critérios de aceitação da Spec 018: fornecedores e contas a pagar (UC-15)."""

import unittest
from datetime import date, datetime, timedelta
from decimal import Decimal

from remindme.aplicacao.servico_clientes import ServicoClientes
from remindme.aplicacao.servico_fornecedores import ServicoFornecedores
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


if __name__ == "__main__":
    unittest.main()
