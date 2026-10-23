"""Ponta a ponta no navegador (Spec 017, CA-23). Opcional: só roda com o Playwright instalado (OPEN-29).

    pip install playwright && python -m playwright install chromium
    python3 -m unittest tests.ponta_a_ponta.test_navegador
"""

import tempfile
import threading
import unittest
from pathlib import Path

from remindme.demonstracao import preparar_demonstracao
from remindme.inicializacao import criar_servidor, montar
from remindme.infraestrutura.memoria import RegistroErrosEmMemoria
from tests.apoio import CIFRADOR_DE_TESTE

try:
    from playwright.sync_api import sync_playwright
except ImportError:
    sync_playwright = None

SENHA = "senha-de-teste"


@unittest.skipIf(sync_playwright is None, "Playwright não instalado: o teste de navegador é opcional (OPEN-29)")
class FluxoCriticoNoNavegador(unittest.TestCase):
    """O fluxo crítico de `docs/testes.md`: entrar, registrar o pagamento integral e ver o título Baixado."""

    def setUp(self):
        self._pasta = tempfile.TemporaryDirectory()
        sistema = montar(str(Path(self._pasta.name).joinpath("demo.db")), cifrador=CIFRADOR_DE_TESTE, erros=RegistroErrosEmMemoria())
        preparar_demonstracao(sistema, SENHA)
        self.servidor = criar_servidor(sistema, "127.0.0.1", 0)
        threading.Thread(target=self.servidor.serve_forever, daemon=True).start()
        self.base = f"http://127.0.0.1:{self.servidor.server_address[1]}"

    def tearDown(self):
        self.servidor.shutdown()
        self.servidor.server_close()
        self._pasta.cleanup()

    def test_CA_23_entrar_registrar_pagamento_integral_e_ver_o_titulo_baixado(self):
        with sync_playwright() as playwright:
            navegador = playwright.chromium.launch()
            try:
                pagina = navegador.new_page(locale="pt-BR")
                pagina.goto(self.base + "/entrar")
                pagina.fill("#email", "diego@demo.example")
                pagina.fill("#senha", SENHA)
                pagina.click("button[type=submit]")
                pagina.wait_for_url(self.base + "/painel")
                self.assertIn("Olá, Diego", pagina.inner_text("h1"))

                pagina.click("nav >> text=Títulos")
                pagina.locator("tr", has_text="R$ 3.800,00").locator("a").first.click()
                pagina.fill("#valor", "3.800,00")
                pagina.click("text=Registrar pagamento >> nth=-1")

                self.assertIn("Pagamento registrado.", pagina.inner_text("main"))
                self.assertTrue(pagina.locator(".selo.baixado.grande").is_visible())
                self.assertIn("R$ 0,00", pagina.inner_text(".dados"))
            finally:
                navegador.close()


if __name__ == "__main__":
    unittest.main()
