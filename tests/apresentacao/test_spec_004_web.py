"""Spec 004 pela interface web, com o banco SQLite de verdade (no próprio processo, sem rede)."""

import re
import unittest
from decimal import Decimal

from remindme.dominio.orcamento import EstadoOrcamento
from remindme.infraestrutura.sqlite import UnidadeDeTrabalhoSQLite
from tests.apresentacao.test_spec_017_web import OUTRO_ID, Base


class OrcamentosPelaInterface(Base):
    def criar_pela_interface(self, navegador):
        resposta = navegador.enviar("/orcamentos/novo", "/orcamentos/novo", {"cliente": self.cliente.id, "condicao": "Pix"})
        self.assertEqual(resposta.status, 303)
        return resposta.destino.split("?")[0]

    def test_RNF_01_paginas_de_orcamento_exigem_sessao(self):
        navegador = self.navegador()
        for caminho in ("/orcamentos", "/orcamentos/novo", f"/orcamentos/{OUTRO_ID}", f"/orcamentos/{OUTRO_ID}/cancelamento"):
            with self.subTest(caminho=caminho):
                self.assertEqual(navegador.get(caminho).destino, "/entrar")
        self.assertEqual(navegador.post("/orcamentos/novo", {"cliente": self.cliente.id}).destino, "/entrar")

    def test_fluxo_completo_operador_pede_desconto_e_a_dona_decide(self):
        diego = self.navegador("diego@exemplo.com")
        pagina = self.criar_pela_interface(diego)
        resposta = diego.enviar(pagina, f"{pagina}/itens", {"descricao": "Instalação", "quantidade": "1,5", "valor_unitario": "1.200,00"})
        self.assertEqual(resposta.status, 303)
        resposta = diego.enviar(pagina, f"{pagina}/desconto", {"percentual": "20"})
        self.assertIn("desconto-pendente", resposta.destino)
        texto = diego.get(pagina).texto
        self.assertIn("Pendente de Alçada", texto)
        self.assertIn("Desconto aguardando o Dono", texto)
        self.assertNotIn('action="' + pagina + '/decisao"', texto)

        carla = self.navegador("carla@exemplo.com")
        self.assertIn("Descontos aguardando sua decisão", carla.get("/painel").texto)
        resposta = carla.enviar(pagina, f"{pagina}/decisao", {"acao": "aprovar", "percentual": "15"})
        self.assertEqual(resposta.status, 303)
        texto = carla.get(pagina).texto
        self.assertIn("15% (R$ 270,00)", texto)
        self.assertIn("R$ 1.530,00", texto)

        orcamento_id = pagina.rsplit("/", 1)[1]
        with UnidadeDeTrabalhoSQLite(self.caminho) as uow:
            salvo = uow.orcamentos.obter(orcamento_id)
        self.assertEqual((salvo.estado, salvo.percentual_desconto), (EstadoOrcamento.RASCUNHO, Decimal("15.00")))
        self.assertEqual([(d.percentual_solicitado, d.percentual_aprovado) for d in salvo.decisoes], [(Decimal("20.00"), Decimal("15.00"))])

    def test_RNF_14_item_invalido_mostra_todos_os_campos(self):
        diego = self.navegador("diego@exemplo.com")
        pagina = self.criar_pela_interface(diego)
        resposta = diego.enviar(pagina, f"{pagina}/itens", {"descricao": "", "quantidade": "0", "valor_unitario": "abc"})
        self.assertEqual(resposta.status, 400)
        for campo in ("descricao", "quantidade", "valor_unitario"):
            self.assertIn(f'id="erro-{campo}"', resposta.texto)

    def test_RNF_03_operador_nao_decide_desconto_pela_interface(self):
        diego = self.navegador("diego@exemplo.com")
        pagina = self.criar_pela_interface(diego)
        diego.enviar(pagina, f"{pagina}/itens", {"descricao": "Serviço", "quantidade": "1", "valor_unitario": "100"})
        diego.enviar(pagina, f"{pagina}/desconto", {"percentual": "50"})
        resposta = diego.enviar(pagina, f"{pagina}/decisao", {"acao": "aprovar"})
        self.assertEqual(resposta.status, 403)
        self.assertIn("Pendente de Alçada", diego.get(pagina).texto)

    def test_RB_03_contador_nao_ve_orcamentos(self):
        helena = self.navegador("helena@exemplo.com")
        menu = re.search(r'<nav class="menu".*?</nav>', helena.get("/painel").texto, re.S).group(0)
        self.assertNotIn("Orçamentos", menu)
        self.assertEqual(helena.get("/orcamentos").status, 403)

    def test_texto_do_item_e_escapado(self):
        diego = self.navegador("diego@exemplo.com")
        pagina = self.criar_pela_interface(diego)
        diego.enviar(pagina, f"{pagina}/itens", {"descricao": "<script>alert(1)</script>", "quantidade": "1", "valor_unitario": "10"})
        texto = diego.get(pagina).texto
        self.assertNotIn("<script>alert(1)</script>", texto)
        self.assertIn("&lt;script&gt;", texto)

    def test_alterar_remover_item_e_cancelar(self):
        diego = self.navegador("diego@exemplo.com")
        pagina = self.criar_pela_interface(diego)
        diego.enviar(pagina, f"{pagina}/itens", {"descricao": "Serviço", "quantidade": "1", "valor_unitario": "100"})
        item_id = re.search(rf'{pagina}/itens/([0-9a-f]{{32}})"', diego.get(pagina).texto).group(1)
        item = f"{pagina}/itens/{item_id}"
        self.assertEqual(diego.enviar(item, item, {"descricao": "Serviço", "quantidade": "2", "valor_unitario": "100"}).status, 303)
        self.assertIn("R$ 200,00", diego.get(pagina).texto)
        self.assertEqual(diego.enviar(pagina, f"{item}/remocao", {}).status, 303)
        self.assertIn("Nenhum item ainda", diego.get(pagina).texto)
        cancelamento = f"{pagina}/cancelamento"
        self.assertEqual(diego.enviar(cancelamento, cancelamento, {"motivo": ""}).status, 400)
        self.assertEqual(diego.enviar(cancelamento, cancelamento, {"motivo": "Cliente desistiu"}).status, 303)
        self.assertIn("Cliente desistiu", diego.get(pagina).texto)

    def test_lista_filtra_por_estado(self):
        diego = self.navegador("diego@exemplo.com")
        pagina = self.criar_pela_interface(diego)
        self.assertIn(pagina, diego.get("/orcamentos?estado=RASCUNHO").texto)
        self.assertNotIn(pagina, diego.get("/orcamentos?estado=CANCELADO").texto)


if __name__ == "__main__":
    unittest.main()
