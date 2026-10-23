"""Critérios de aceitação da Spec 003: cadastro de clientes (UC-03)."""

import unittest
from datetime import date, datetime, timedelta
from decimal import Decimal

from remindme.aplicacao.servico_clientes import ServicoClientes
from remindme.aplicacao.servico_titulos import FiltroTitulos, ServicoTitulos
from remindme.dominio.cliente import Cliente
from remindme.dominio.erros import OperacaoNegada, OperacaoRecusada
from remindme.dominio.usuario import Perfil, Usuario
from remindme.infraestrutura.memoria import RelogioFixo, UnidadeDeTrabalhoEmMemoria
from tests.apoio import ComSessoes

HOJE = date(2026, 10, 3)
OPERADOR = Usuario("operador", "Diego Ramos", Perfil.OPERADOR_FINANCEIRO)
CONTADOR = Usuario("contador", "Helena Prado", Perfil.CONTADOR)
ADMIN = Usuario("admin", "Administração", Perfil.ADMINISTRADOR)

CNPJ = "11.222.333/0001-81"
CPF = "529.982.247-25"
OUTRO_CPF = "111.444.777-35"


class Base(ComSessoes, unittest.TestCase):
    def setUp(self):
        self.uow = UnidadeDeTrabalhoEmMemoria()
        relogio = RelogioFixo(datetime(2026, 10, 3, 10, 0))
        self.clientes = ServicoClientes(self.uow, relogio)
        self.titulos = ServicoTitulos(self.uow, self.uow.clientes, relogio)
        self.operador = self.sessao(OPERADOR)

    def cadastrar(self, nome="Padaria Pão Quente Ltda", documento=CNPJ, contato="contato@padaria.com.br"):
        return self.clientes.cadastrar_cliente(self.operador, nome, documento, contato)

    def fotografia(self):
        return dict(self.uow.clientes.dados), self.uow.auditoria.registros


class Spec003(Base):
    def test_CA_01_cadastro_guarda_o_documento_sem_pontuacao_e_audita_os_tres_campos(self):
        cliente = self.cadastrar()
        self.assertEqual(self.uow.clientes.obter(cliente.id).documento, "11222333000181")
        registros = [r for r in self.uow.auditoria.registros if r.registro_afetado == f"cliente {cliente.id}"]
        self.assertEqual(
            {(r.campo, r.valor_anterior, r.valor_novo) for r in registros},
            {
                ("nome", None, "Padaria Pão Quente Ltda"),
                ("documento", None, "11222333000181"),
                ("contato", None, "contato@padaria.com.br"),
            },
        )
        self.assertTrue(all(r.usuario_id == OPERADOR.id for r in registros))

    def test_CA_02_cpf_com_digito_verificador_errado_e_recusado_no_campo_documento(self):
        with self.assertRaises(OperacaoRecusada) as ctx:
            self.cadastrar(documento="529.982.247-24")
        self.assertEqual(set(ctx.exception.campos), {"documento"})

    def test_CA_03_INV_1_documento_repetido_e_recusado(self):
        self.cadastrar(nome="Sérgio Tavares", documento=CPF, contato="(11) 98765-4321")
        antes = self.fotografia()
        with self.assertRaises(OperacaoRecusada) as ctx:
            self.cadastrar(nome="Outro Sérgio", documento="52998224725", contato="sergio@exemplo.com")
        self.assertIn("documento", ctx.exception.campos)
        self.assertEqual(self.fotografia(), antes)

    def test_CA_04_RNF_14_sem_nome_e_sem_contato_indica_os_dois_campos(self):
        with self.assertRaises(OperacaoRecusada) as ctx:
            self.cadastrar(nome=" ", contato="")
        self.assertEqual(set(ctx.exception.campos), {"nome", "contato"})

    def test_CA_05_OPEN_41_contato_precisa_ser_email_ou_telefone_com_ddd(self):
        with self.assertRaises(OperacaoRecusada) as ctx:
            self.cadastrar(contato="abc")
        self.assertEqual(set(ctx.exception.campos), {"contato"})
        cliente = self.cadastrar(contato="(11) 98765-4321")
        self.assertEqual(cliente.contato, "11987654321")

    def test_CA_06_RF_05_alteracao_audita_so_o_campo_que_mudou(self):
        cliente = self.cadastrar()
        total = len(self.uow.auditoria.registros)
        self.clientes.alterar_cliente(self.operador, cliente.id, cliente.nome, CNPJ, "financeiro@padaria.com.br")
        [registro] = self.uow.auditoria.registros[total:]
        self.assertEqual(
            (registro.operacao, registro.campo, registro.valor_anterior, registro.valor_novo),
            ("alterar cliente", "contato", "contato@padaria.com.br", "financeiro@padaria.com.br"),
        )

    def test_CA_07_alteracao_para_documento_de_outro_cliente_e_recusada(self):
        a = self.cadastrar(nome="Cliente A", documento=CPF)
        self.cadastrar(nome="Cliente B", documento=OUTRO_CPF)
        antes = self.fotografia()
        with self.assertRaises(OperacaoRecusada) as ctx:
            self.clientes.alterar_cliente(self.operador, a.id, a.nome, OUTRO_CPF, a.contato)
        self.assertIn("documento", ctx.exception.campos)
        self.assertEqual(self.fotografia(), antes)

    def test_CA_08_RB_03_contador_nao_cadastra_mas_pesquisa(self):
        self.cadastrar()
        contador = self.sessao(CONTADOR)
        with self.assertRaisesRegex(OperacaoNegada, "RB-03"):
            self.clientes.cadastrar_cliente(contador, "Outro", CPF, "a@b.com")
        self.assertEqual(len(self.clientes.consultar_clientes(contador)), 1)

    def test_CA_09_pesquisa_por_parte_do_nome_ou_pelo_documento(self):
        self.cadastrar()
        self.cadastrar(nome="Sérgio Tavares", documento=CPF, contato="sergio@exemplo.com")
        for termo in ("pão", "PÃO QUENTE", "11222333000181", CNPJ):
            with self.subTest(termo=termo):
                self.assertEqual(
                    [c.nome for c in self.clientes.consultar_clientes(self.operador, termo)],
                    ["Padaria Pão Quente Ltda"],
                )
        self.assertEqual(
            [c.nome for c in self.clientes.consultar_clientes(self.operador)],
            ["Padaria Pão Quente Ltda", "Sérgio Tavares"],
        )

    def test_CA_10_INV_5_titulo_so_para_cliente_cadastrado(self):
        with self.assertRaisesRegex(OperacaoRecusada, "Cliente inexistente"):
            self.titulos.cadastrar_titulo(self.operador, "cliente-que-nao-existe", Decimal("100.00"), HOJE)
        cliente = self.cadastrar()
        titulo = self.titulos.cadastrar_titulo(self.operador, cliente.id, Decimal("100.00"), HOJE)
        self.assertEqual(titulo.cliente_id, cliente.id)

    def test_CA_11_titulos_do_cliente(self):
        a = self.cadastrar(nome="Cliente A", documento=CPF)
        b = self.cadastrar(nome="Cliente B", documento=OUTRO_CPF)
        for cliente in (a, b, a):
            self.titulos.cadastrar_titulo(self.operador, cliente.id, Decimal("100.00"), HOJE + timedelta(days=5))
        visoes = self.titulos.consultar_titulos(self.operador, FiltroTitulos(cliente_id=a.id), HOJE)
        self.assertEqual({v.cliente_id for v in visoes}, {a.id})
        self.assertEqual(len(visoes), 2)

    def test_CA_12_RNF_02_administrador_nao_pesquisa_clientes(self):
        with self.assertRaises(OperacaoNegada):
            self.clientes.consultar_clientes(self.sessao(ADMIN))

    def test_CA_13_OPEN_40_cnpj_alfanumerico_valido_e_aceito(self):
        cliente = self.cadastrar(documento="12.ABC.345/01DE-35")
        self.assertEqual(cliente.documento, "12ABC34501DE35")


class ClienteNoDominio(unittest.TestCase):
    def test_OPEN_40_cpf_e_cnpj_com_tamanho_ou_digito_errado_sao_recusados(self):
        for documento in ("123", "52998224724", "11111111111", "11222333000182", "12ABC34501DE36", "1" * 14):
            with self.subTest(documento=documento), self.assertRaises(OperacaoRecusada):
                Cliente.cadastrar("c1", "Nome", documento, "a@b.com")

    def test_OPEN_41_telefone_com_codigo_do_pais_e_aceito(self):
        self.assertEqual(Cliente.cadastrar("c1", "Nome", CPF, "+55 (11) 3333-4444").contato, "1133334444")

    def test_A1_alteracao_sem_mudanca_nao_tem_alteracoes(self):
        cliente = Cliente.cadastrar("c1", "Nome", CPF, "a@b.com")
        _, alteracoes = cliente.alterado("Nome", "529.982.247-25", "A@B.COM")
        self.assertEqual(alteracoes, {})


if __name__ == "__main__":
    unittest.main()
