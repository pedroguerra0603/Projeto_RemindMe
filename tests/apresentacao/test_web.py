"""Interface web: chamada direta da aplicação WSGI, sem servidor e sem rede."""

import io
import re
import unittest
from decimal import Decimal
from urllib.parse import urlencode

from remindme.apresentacao import formatos
from remindme.apresentacao.web import COOKIE_SESSAO, AplicacaoWeb
from tests.apoio_sistema import CNPJ, SENHA, com_usuarios, novo_sistema

ROTAS_PROTEGIDAS = [
    "/", "/titulos", "/titulos/novo", "/titulos/x", "/clientes", "/clientes/novo", "/clientes/x",
    "/auditoria", "/usuarios", "/usuarios/novo", "/usuarios/x", "/permissoes",
]


class Navegador:
    def __init__(self, aplicacao):
        self.aplicacao = aplicacao
        self.cookies = {}

    def pedir(self, metodo, caminho, dados=None):
        caminho, _, consulta = caminho.partition("?")
        corpo = urlencode(dados or {}, doseq=True).encode()
        ambiente = {
            "REQUEST_METHOD": metodo,
            "PATH_INFO": caminho,
            "QUERY_STRING": consulta,
            "CONTENT_LENGTH": str(len(corpo)),
            "CONTENT_TYPE": "application/x-www-form-urlencoded",
            "HTTP_COOKIE": "; ".join(f"{k}={v}" for k, v in self.cookies.items()),
            "wsgi.input": io.BytesIO(corpo),
        }
        resposta = {}

        def iniciar(status, cabecalhos):
            resposta["status"] = int(status.split()[0])
            resposta["cabecalhos"] = cabecalhos

        texto = b"".join(self.aplicacao(ambiente, iniciar)).decode()
        for nome, valor in resposta["cabecalhos"]:
            if nome == "Set-Cookie":
                chave, _, resto = valor.partition("=")
                conteudo = resto.split(";")[0]
                if "Max-Age=0" in valor:
                    self.cookies.pop(chave, None)
                else:
                    self.cookies[chave] = conteudo
        return resposta["status"], dict(resposta["cabecalhos"]), texto

    def entrar(self, email):
        return self.pedir("POST", "/login", {"email": email, "senha": SENHA})

    def csrf(self, caminho="/"):
        _, _, texto = self.pedir("GET", caminho)
        return re.search(r'name="_csrf" value="([0-9a-f]+)"', texto).group(1)


class Web(unittest.TestCase):
    def setUp(self):
        self.sistema, self.uow, _ = novo_sistema()
        self.tokens = com_usuarios(self.sistema)
        self.cliente = self.sistema.cadastrar_cliente(self.tokens["operador"], nome="ACME", documento=CNPJ)
        self.web = Navegador(AplicacaoWeb(self.sistema, segredo=b"teste"))

    def test_RNF_01_toda_rota_exige_sessao(self):
        for caminho in ROTAS_PROTEGIDAS:
            with self.subTest(caminho=caminho):
                status, cabecalhos, _ = self.web.pedir("GET", caminho)
                self.assertEqual((status, cabecalhos.get("Location")), (303, "/login"))

    def test_login_valido_abre_o_painel_e_invalido_nao_diz_o_campo(self):
        status, _, texto = self.web.pedir("POST", "/login", {"email": "diego@exemplo.com", "senha": "x"})
        self.assertEqual(status, 401)
        self.assertIn("E-mail ou senha inválidos.", texto)
        status, cabecalhos, _ = self.web.entrar("diego@exemplo.com")
        self.assertEqual((status, cabecalhos["Location"]), (303, "/"))
        self.assertIn(COOKIE_SESSAO, self.web.cookies)
        status, _, texto = self.web.pedir("GET", "/")
        self.assertEqual(status, 200)
        self.assertIn("Olá, Diego", texto)

    def test_RF_65_menu_mostra_somente_o_que_o_perfil_pode(self):
        self.web.entrar("carla@exemplo.com")
        _, _, texto = self.web.pedir("GET", "/")
        menu = re.search(r'<nav class="menu".*?</nav>', texto, re.S).group(0)
        self.assertIn("Títulos", menu)
        self.assertNotIn("Usuários", menu)
        self.assertNotIn("Novo título", texto)

    def test_RF_67_negacao_mostra_o_motivo(self):
        self.web.entrar("carla@exemplo.com")
        status, _, texto = self.web.pedir("GET", "/usuarios")
        self.assertEqual(status, 403)
        self.assertIn("não tem permissão", texto)

    def test_post_sem_csrf_e_recusado(self):
        self.web.entrar("diego@exemplo.com")
        status, _, _ = self.web.pedir("POST", "/clientes/novo", {"nome": "X", "documento": "52998224725"})
        self.assertEqual(status, 400)
        self.assertEqual(len(self.uow.clientes.listar()), 1)

    def test_fluxo_titulo_pagamento_e_baixa(self):
        self.web.entrar("diego@exemplo.com")
        csrf = self.web.csrf()
        status, cabecalhos, _ = self.web.pedir("POST", "/titulos/novo", {
            "_csrf": csrf, "cliente": self.cliente.id, "valor": "1.234,50", "vencimento": "2026-11-10",
        })
        self.assertEqual(status, 303)
        destino = cabecalhos["Location"]
        titulo_id = destino.rsplit("/", 1)[1]
        self.web.pedir("POST", f"{destino}/pagamentos", {"_csrf": csrf, "valor": "1234,50", "data": "2026-10-20"})
        _, _, texto = self.web.pedir("GET", destino)
        self.assertIn("Título baixado", texto)
        self.assertIn("Baixado", texto)
        self.assertEqual(self.uow.titulos.obter(titulo_id).saldo, Decimal("0.00"))

    def test_RNF_14_formulario_invalido_informa_campo_e_motivo(self):
        self.web.entrar("diego@exemplo.com")
        csrf = self.web.csrf()
        status, _, texto = self.web.pedir("POST", "/clientes/novo", {"_csrf": csrf, "nome": "", "documento": "123"})
        self.assertEqual(status, 400)
        self.assertIn("<strong>nome</strong>: obrigatório", texto)
        self.assertIn("<strong>documento</strong>: CPF ou CNPJ inválido", texto)

    def test_recusa_de_negocio_volta_com_o_motivo(self):
        titulo = self.sistema.cadastrar_titulo(self.tokens["operador"], self.cliente.id, Decimal("10"), formatos.ler_data("2026-11-10"))
        self.web.entrar("diego@exemplo.com")
        csrf = self.web.csrf()
        self.web.pedir("POST", f"/titulos/{titulo.id}/pagamentos", {"_csrf": csrf, "valor": "50,00", "data": "2026-10-20"})
        _, _, texto = self.web.pedir("GET", f"/titulos/{titulo.id}")
        self.assertIn("maior que o saldo", texto)

    def test_texto_do_usuario_e_escapado(self):
        self.sistema.cadastrar_cliente(self.tokens["operador"], nome="<script>alert(1)</script>", documento="52998224725")
        self.web.entrar("diego@exemplo.com")
        _, _, texto = self.web.pedir("GET", "/clientes")
        self.assertNotIn("<script>alert(1)</script>", texto)
        self.assertIn("&lt;script&gt;", texto)

    def test_cabecalhos_de_seguranca_e_cookie_httponly(self):
        _, cabecalhos, _ = self.web.pedir("GET", "/login")
        self.assertIn("frame-ancestors 'none'", cabecalhos["Content-Security-Policy"])
        self.assertEqual(cabecalhos["X-Content-Type-Options"], "nosniff")
        bruto = {}
        aplicacao = self.web.aplicacao
        ambiente = {"REQUEST_METHOD": "POST", "PATH_INFO": "/login", "QUERY_STRING": "",
                    "CONTENT_LENGTH": "", "wsgi.input": io.BytesIO(b"")}
        corpo = urlencode({"email": "diego@exemplo.com", "senha": SENHA}).encode()
        ambiente.update(CONTENT_LENGTH=str(len(corpo)), **{"wsgi.input": io.BytesIO(corpo)})
        aplicacao(ambiente, lambda s, c: bruto.setdefault("c", c))
        cookie = next(v for n, v in bruto["c"] if n == "Set-Cookie")
        self.assertIn("HttpOnly", cookie)
        self.assertIn("SameSite=Lax", cookie)

    def test_sair_encerra_a_sessao(self):
        self.web.entrar("diego@exemplo.com")
        csrf = self.web.csrf()
        token = self.web.cookies[COOKIE_SESSAO]
        self.web.pedir("POST", "/sair", {"_csrf": csrf})
        self.web.cookies[COOKIE_SESSAO] = token
        status, _, _ = self.web.pedir("GET", "/")
        self.assertEqual(status, 303)

    def test_estatico_e_rota_inexistente(self):
        status, cabecalhos, _ = self.web.pedir("GET", "/static/estilo.css")
        self.assertEqual(status, 200)
        self.assertTrue(cabecalhos["Content-Type"].startswith("text/css"))
        self.assertEqual(self.web.pedir("GET", "/static/..secreto.css")[0], 404)
        self.assertEqual(self.web.pedir("GET", "/nao-existe")[0], 404)


class Formatos(unittest.TestCase):
    def test_leitura_de_dinheiro(self):
        for texto, esperado in (("1.234,56", "1234.56"), ("R$ 10", "10"), ("1234.5", "1234.5"), ("1.000.000", "1000000")):
            with self.subTest(texto=texto):
                self.assertEqual(formatos.ler_dinheiro(texto), Decimal(esperado))

    def test_dinheiro_invalido(self):
        for texto in ("", "abc", "1,234", "1" * 16, "NaN"):
            with self.subTest(texto=texto), self.assertRaises(formatos.ValorInvalido):
                formatos.ler_dinheiro(texto)

    def test_apresentacao(self):
        self.assertEqual(formatos.dinheiro(Decimal("1234567.5")), "R$ 1.234.567,50")
        self.assertEqual(formatos.data(formatos.ler_data("10/11/2026")), "10/11/2026")


if __name__ == "__main__":
    unittest.main()
