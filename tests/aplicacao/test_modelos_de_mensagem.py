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
    def test_RF_08_numero_do_orcamento_sao_os_8_primeiros_caracteres_em_maiusculas(self):
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

    def test_RF_08_quantidade_fracionada_usa_virgula(self):
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

    def test_OPEN_54_nome_fantasia_vazio_usa_razao_social(self):
        assunto, _ = mensagem_de_orcamento(empresa(nome_fantasia=""), CLIENTE, orcamento())
        self.assertEqual(assunto, "Orçamento nº ABCDEF12 — Menezes Serviços Ltda")


class ModelosDosAlertasDeObrigacao(unittest.TestCase):
    """Spec 010: o texto do aviso e do escalonamento sai só destes modelos (RB-27, INV-6)."""

    def setUp(self):
        from datetime import datetime

        from remindme.dominio.obrigacao import Obrigacao
        from remindme.dominio.usuario import Perfil, Usuario

        self.operador = Usuario("operador", "Diego Ramos", Perfil.OPERADOR_FINANCEIRO, "diego@demo.example")
        self.dona = Usuario("dono", "Carla Menezes", Perfil.DONO, "carla@demo.example")
        agora = datetime(2026, 11, 20, 9, 0)

        def nova(prazo, exige):
            return Obrigacao.cadastrar("o1", "DAS", "Fiscal", "Mensal", prazo, self.operador, exige, date(2026, 11, 1), "operador", agora)

        self.nova = nova

    def test_RB_27_aviso_de_obrigacao_tem_o_texto_do_modelo(self):
        from remindme.aplicacao.modelos_de_mensagem import mensagem_de_aviso_de_obrigacao

        hoje = date(2026, 11, 20)
        assunto, texto = mensagem_de_aviso_de_obrigacao(empresa(), self.operador, self.nova(date(2026, 11, 25), True), hoje)
        self.assertEqual(assunto, "Obrigação a vencer: DAS em 25/11/2026")
        self.assertEqual(
            texto,
            "Olá, Diego Ramos.\n\nA obrigação DAS (Fiscal) vence em 25/11/2026, daqui a 5 dias.\n"
            "Ao registrar o cumprimento, anexe a evidência.\n\nMenezes · RemindMe",
        )
        for prazo, quando in ((date(2026, 11, 20), "hoje"), (date(2026, 11, 21), "amanhã")):
            with self.subTest(quando=quando):
                _, texto = mensagem_de_aviso_de_obrigacao(None, self.operador, self.nova(prazo, False), hoje)
                self.assertEqual(
                    texto,
                    f"Olá, Diego Ramos.\n\nA obrigação DAS (Fiscal) vence em {prazo:%d/%m/%Y}, {quando}.\n\nNossa empresa · RemindMe",
                )

    def test_RB_27_escalonamento_tem_o_texto_do_modelo(self):
        from remindme.aplicacao.modelos_de_mensagem import mensagem_de_escalonamento

        o = self.nova(date(2026, 11, 19), False)
        assunto, texto = mensagem_de_escalonamento(empresa(), self.dona, o, self.operador, date(2026, 11, 20))
        self.assertEqual(assunto, "Obrigação atrasada: DAS")
        self.assertEqual(
            texto,
            "Olá, Carla Menezes.\n\nA obrigação DAS (Fiscal) venceu em 19/11/2026 e está Atrasada há 1 dia.\n"
            "Responsável: Diego Ramos.\n\nMenezes · RemindMe",
        )
        _, texto = mensagem_de_escalonamento(None, self.dona, o, None, date(2026, 11, 22))
        self.assertIn("está Atrasada há 3 dias.\nResponsável: não definido.", texto)


if __name__ == "__main__":
    unittest.main()
