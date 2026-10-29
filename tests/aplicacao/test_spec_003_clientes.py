"""Cadastro de clientes (UC-03, RF-01)."""

import unittest

from remindme.aplicacao.portas import FiltroAuditoria
from remindme.dominio.erros import AcessoNegado, EntradaInvalida
from tests.apoio_sistema import CNPJ, CPF, com_usuarios, novo_sistema


class Clientes(unittest.TestCase):
    def setUp(self):
        self.sistema, self.uow, _ = novo_sistema()
        self.t = com_usuarios(self.sistema)

    def test_RF_01_cadastra_cliente_e_audita(self):
        cliente = self.sistema.cadastrar_cliente(self.t["operador"], nome="ACME", documento=CNPJ, email="a@acme.com")
        self.assertEqual(cliente.documento, "11222333000181")
        registros = self.sistema.consultar_auditoria(self.t["dono"], FiltroAuditoria(operacao="cadastrar cliente"))
        self.assertEqual(len(registros), 1)

    def test_E1_documento_duplicado(self):
        self.sistema.cadastrar_cliente(self.t["operador"], nome="ACME", documento=CNPJ)
        with self.assertRaises(EntradaInvalida) as erro:
            self.sistema.cadastrar_cliente(self.t["operador"], nome="Outra", documento="11222333000181")
        self.assertEqual(erro.exception.campos, {"documento": "já cadastrado"})

    def test_E2_campos_obrigatorios(self):
        with self.assertRaises(EntradaInvalida) as erro:
            self.sistema.cadastrar_cliente(self.t["operador"], nome=" ", documento="")
        self.assertEqual(set(erro.exception.campos), {"nome", "documento"})

    def test_A1_alteracao_audita_cada_campo(self):
        cliente = self.sistema.cadastrar_cliente(self.t["operador"], nome="ACME", documento=CNPJ)
        self.sistema.alterar_cliente(self.t["operador"], cliente.id, nome="ACME S.A.", documento=CNPJ, telefone="11 4000-0000")
        registros = self.sistema.consultar_auditoria(self.t["dono"], FiltroAuditoria(operacao="alterar cliente"))
        self.assertEqual({(r.campo, r.valor_anterior, r.valor_novo) for r in registros},
                         {("nome", "ACME", "ACME S.A."), ("telefone", "", "11 4000-0000")})

    def test_A2_busca_por_nome_ou_documento(self):
        self.sistema.cadastrar_cliente(self.t["operador"], nome="ACME", documento=CNPJ)
        self.sistema.cadastrar_cliente(self.t["operador"], nome="João", documento=CPF)
        self.assertEqual([c.nome for c in self.sistema.listar_clientes(self.t["operador"], "acm")], ["ACME"])
        self.assertEqual([c.nome for c in self.sistema.listar_clientes(self.t["operador"], "529.982")], ["João"])

    def test_RB_03_contador_consulta_mas_nao_cadastra(self):
        self.sistema.listar_clientes(self.t["contador"])
        with self.assertRaises(AcessoNegado):
            self.sistema.cadastrar_cliente(self.t["contador"], nome="ACME", documento=CNPJ)


if __name__ == "__main__":
    unittest.main()
