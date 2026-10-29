"""Gráficos do painel: o desenho em SVG e o conjunto de gráficos de cada perfil."""

import unittest
from decimal import Decimal

from remindme.apresentacao.web import graficos as g
from tests.apresentacao.test_spec_017_web import Base


def texto(valor):
    return f"{valor}"


class Desenho(unittest.TestCase):
    def test_colunas_mais_alta_e_a_de_maior_valor_e_os_valores_aparecem_escritos(self):
        svg = g.colunas([("jan", Decimal(50), "azul"), ("fev", Decimal(100), "azul")], texto, "Recebido")
        self.assertIn('height="19.00"', svg)  # metade da altura máxima (38)
        self.assertIn('height="38.00"', svg)
        self.assertIn(">50<", svg)
        self.assertIn('aria-label="Recebido"', svg)

    def test_anel_divide_o_circulo_pela_parte_de_cada_item(self):
        svg = g.anel([("A", Decimal(3), "azul"), ("B", Decimal(1), "vermelho")], texto, "Carteira")
        self.assertIn('stroke-dasharray="75.00 25.00"', svg)
        self.assertIn('stroke-dasharray="25.00 75.00"', svg)

    def test_sem_dados_mostra_aviso_em_vez_de_grafico_vazio(self):
        for desenhar in (g.colunas, g.barras, g.anel):
            with self.subTest(grafico=desenhar.__name__):
                self.assertIn("Ainda não há dados", desenhar([("A", Decimal(0), "azul")], texto, "X"))

    def test_rotulo_e_escapado(self):
        svg = g.barras([("<b>x</b>", Decimal(1), "azul")], texto, "X")
        self.assertNotIn("<b>x</b>", svg)


class GraficosPorPerfil(Base):
    def test_cada_perfil_ve_os_seus_graficos(self):
        esperados = {
            "carla@exemplo.com": ("Recebido nos últimos 6 meses", "Carteira de títulos"),
            "admin@exemplo.com": ("Ações por usuário (30 dias)", "Ações mais comuns (30 dias)"),
            "diego@exemplo.com": ("Meus orçamentos por estado", "A receber nos próximos 7 dias"),
            "helena@exemplo.com": ("Carteira por atraso",),
        }
        for email, titulos in esperados.items():
            with self.subTest(email=email):
                painel = self.navegador(email).get("/painel").texto
                for titulo in titulos:
                    self.assertIn(titulo, painel)
        self.assertNotIn("Ações por usuário", self.navegador("carla@exemplo.com").get("/painel").texto)

    def test_script_do_tema_e_servido_pelo_proprio_site(self):
        resposta = self.navegador().get("/estatico/tema.js")
        self.assertEqual(resposta.status, 200)
        self.assertIn("localStorage", resposta.texto)


if __name__ == "__main__":
    unittest.main()
