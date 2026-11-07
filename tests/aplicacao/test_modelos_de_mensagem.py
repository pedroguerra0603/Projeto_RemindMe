"""Spec 005: o texto que chega ao cliente sai só deste modelo (RB-27, INV-4)."""

import unittest
from datetime import date
from decimal import Decimal

from remindme.aplicacao.modelos_de_mensagem import mensagem_de_orcamento, numero_do_orcamento
from remindme.dominio.cliente import Cliente
from remindme.dominio.empresa import Empresa
from remindme.dominio.orcamento import Orcamento

CLIENTE = Cliente("c1", "Padaria Pão Quente Ltda", "11222333000181", "a@padaria.com.br")


def empresa(nome_fantasia="Menezes"):
    return Empresa(
        razao_social="Menezes Serviços Ltda", nome_fantasia=nome_fantasia, cnpj="11222333000181",
        telefone="1133224455", email="contato@menezes.com.br", endereco="Rua A, 1",
    )


def orcamento(prazo=30, desconto="10", condicao="Boleto"):
    o = Orcamento.criar("abcdef1234567890", "c1", "operador", date(2026, 11, 7), condicao)
    o.incluir_item("i1", "Revisão", Decimal("2"), Decimal("1234.50"))
    o.informar_desconto(Decimal(desconto), "dono", None)
    o.alterar_prazo(prazo)
    return o


class ModeloDoOrcamento(unittest.TestCase):
    def test_numero_do_orcamento_sao_os_8_primeiros_caracteres_em_maiusculas(self):
        self.assertEqual(numero_do_orcamento("abcdef1234567890"), "ABCDEF12")

    def test_RB_27_texto_tem_empresa_numero_itens_valores_e_prazo(self):
        assunto, texto = mensagem_de_orcamento(empresa(), CLIENTE, orcamento())
        self.assertEqual(assunto, "Orçamento nº ABCDEF12 — Menezes")
        linhas = texto.splitlines()
        for esperada in (
            "Olá, Padaria Pão Quente Ltda.",
            "Menezes envia o orçamento nº ABCDEF12:",
            "- Revisão: 2 × R$ 1.234,50 = R$ 2.469,00",
            "Valor bruto: R$ 2.469,00",
            "Desconto: 10% (R$ 246,90)",
            "Valor líquido: R$ 2.222,10",
            "Prazo para pagamento: 30 dias a partir da aprovação",
            "Condição de pagamento: Boleto",
            "Para aprovar ou recusar, responda a esta mensagem.",
        ):
            self.assertIn(esperada, linhas)

    def test_RB_27_prazo_zero_e_sem_desconto_nem_condicao(self):
        _, texto = mensagem_de_orcamento(empresa(), CLIENTE, orcamento(prazo=0, desconto="0", condicao=None))
        self.assertIn("Prazo para pagamento: à vista, na aprovação", texto.splitlines())
        self.assertNotIn("Desconto:", texto)
        self.assertNotIn("Condição de pagamento:", texto)

    def test_quantidade_fracionada_usa_virgula(self):
        o = Orcamento.criar("o2", "c1", "operador", date(2026, 11, 7))
        o.incluir_item("i1", "Horas", Decimal("1.50"), Decimal("100.00"))
        o.alterar_prazo(1)
        _, texto = mensagem_de_orcamento(empresa(), CLIENTE, o)
        self.assertIn("- Horas: 1,5 × R$ 100,00 = R$ 150,00", texto.splitlines())
        self.assertIn("Prazo para pagamento: 1 dia a partir da aprovação", texto.splitlines())

    def test_foco_2_sem_empresa_cadastrada_usa_nossa_empresa(self):
        assunto, texto = mensagem_de_orcamento(None, CLIENTE, orcamento())
        self.assertEqual(assunto, "Orçamento nº ABCDEF12 — Nossa empresa")
        self.assertIn("Nossa empresa envia o orçamento nº ABCDEF12:", texto.splitlines())

    def test_nome_fantasia_vazio_usa_razao_social(self):
        assunto, _ = mensagem_de_orcamento(empresa(nome_fantasia=""), CLIENTE, orcamento())
        self.assertEqual(assunto, "Orçamento nº ABCDEF12 — Menezes Serviços Ltda")


if __name__ == "__main__":
    unittest.main()
