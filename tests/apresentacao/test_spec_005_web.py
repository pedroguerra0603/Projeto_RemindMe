"""Spec 005 pela interface web, com o banco SQLite de verdade (no próprio processo, sem rede)."""

import re
import tempfile
import unittest
from pathlib import Path

from remindme.dominio.orcamento import EstadoOrcamento
from remindme.infraestrutura.sqlite import UnidadeDeTrabalhoSQLite
from tests.apoio import CanalQueFalha
from tests.apresentacao.test_spec_017_web import AGORA, SENHA, Base


class Spec005Web(Base):
    def orcamento_pronto(self, navegador, descricao="Revisão do forno"):
        resposta = navegador.enviar("/orcamentos/novo", "/orcamentos/novo", {"cliente": self.cliente.id, "condicao": "Pix"})
        pagina = resposta.destino.split("?")[0]
        navegador.enviar(pagina, f"{pagina}/itens", {"descricao": descricao, "quantidade": "1", "valor_unitario": "1.000,00"})
        resposta = navegador.enviar(pagina, f"{pagina}/condicao", {"condicao": "Pix", "prazo": "30"})
        self.assertEqual(resposta.status, 303)
        return pagina

    def salvo(self, pagina):
        with UnidadeDeTrabalhoSQLite(self.caminho) as uow:
            return uow.orcamentos.obter(pagina.rsplit("/", 1)[1])

    def test_fluxo_operador_envia_e_registra_aprovacao(self):
        diego = self.navegador("diego@exemplo.com")
        pagina = self.orcamento_pronto(diego)
        resposta = diego.enviar(pagina, f"{pagina}/envio", {})
        self.assertEqual((resposta.status, resposta.destino), (303, f"{pagina}?aviso=orcamento-enviado"))
        self.assertIn("Orçamento enviado ao cliente.", diego.get(resposta.destino).texto)
        resposta = diego.enviar(pagina, f"{pagina}/resposta-do-cliente", {"decisao": "aprovar", "data": "2026-10-22", "motivo": ""})
        self.assertEqual((resposta.status, resposta.destino), (303, f"{pagina}?aviso=orcamento-convertido"))
        orcamento = self.salvo(pagina)
        self.assertIs(orcamento.estado, EstadoOrcamento.CONVERTIDO)
        texto = diego.get(pagina).texto
        self.assertIn(f'href="/titulos/{orcamento.titulo_id}"', texto)
        self.assertIn("Prazo para pagamento", texto)
        self.assertIn(f'href="/orcamentos/{orcamento.id}"', diego.get(f"/titulos/{orcamento.titulo_id}").texto)

    def test_contadora_ve_a_origem_do_titulo_sem_link_que_ela_nao_pode_abrir(self):
        diego = self.navegador("diego@exemplo.com")
        pagina = self.orcamento_pronto(diego)
        diego.enviar(pagina, f"{pagina}/envio", {})
        diego.enviar(pagina, f"{pagina}/resposta-do-cliente", {"decisao": "aprovar", "data": "2026-10-22"})
        orcamento = self.salvo(pagina)
        texto = self.navegador("helena@exemplo.com").get(f"/titulos/{orcamento.titulo_id}").texto
        self.assertIn(f"Gerado do orçamento nº {orcamento.id[:8].upper()}", texto)
        self.assertNotIn(f'href="/orcamentos/{orcamento.id}"', texto)

    def test_botoes_conforme_o_estado(self):
        diego = self.navegador("diego@exemplo.com")
        pagina = self.orcamento_pronto(diego)
        texto = diego.get(pagina).texto
        self.assertIn(f'action="{pagina}/envio"', texto)
        self.assertNotIn(f'action="{pagina}/resposta-do-cliente"', texto)
        diego.enviar(pagina, f"{pagina}/envio", {})
        texto = diego.get(pagina).texto
        self.assertNotIn(f'action="{pagina}/envio"', texto)
        self.assertIn(f'action="{pagina}/resposta-do-cliente"', texto)
        self.assertIn('value="2026-10-22"', texto)  # a data padrão é hoje

    def test_erros_por_campo_em_prazo_e_data(self):
        diego = self.navegador("diego@exemplo.com")
        pagina = self.orcamento_pronto(diego)
        resposta = diego.enviar(pagina, f"{pagina}/condicao", {"condicao": "Pix", "prazo": "abc"})
        self.assertEqual(resposta.status, 400)
        self.assertIn('id="erro-prazo"', resposta.texto)
        diego.enviar(pagina, f"{pagina}/envio", {})
        for data in ("31/02/2026", "2026-10-23"):
            resposta = diego.enviar(pagina, f"{pagina}/resposta-do-cliente", {"decisao": "aprovar", "data": data})
            self.assertEqual(resposta.status, 400, data)
            self.assertIn('id="erro-data"', resposta.texto)
        self.assertIs(self.salvo(pagina).estado, EstadoOrcamento.ENVIADO)

    def test_texto_da_mensagem_e_escapado(self):
        diego = self.navegador("diego@exemplo.com")
        pagina = self.orcamento_pronto(diego, "<script>alert(1)</script>")
        diego.enviar(pagina, f"{pagina}/envio", {})
        for caminho in ("/mensagens", pagina):
            texto = diego.get(caminho).texto
            self.assertIn("&lt;script&gt;alert(1)&lt;/script&gt;", texto)
            self.assertNotIn("<script>alert(1)", texto)

    def test_caixa_de_saida_exige_sessao_e_nega_o_contador(self):
        self.assertEqual(self.navegador().get("/mensagens").destino, "/entrar")
        helena = self.navegador("helena@exemplo.com")
        self.assertEqual(helena.get("/mensagens").status, 403)
        menu = re.search(r'<nav class="menu".*?</nav>', helena.get("/painel").texto, re.S).group(0)
        self.assertNotIn('href="/mensagens"', menu)
        diego = self.navegador("diego@exemplo.com")
        menu = re.search(r'<nav class="menu".*?</nav>', diego.get("/painel").texto, re.S).group(0)
        self.assertIn('href="/mensagens"', menu)

    def test_foco_3_aprovacao_enviada_duas_vezes_gera_um_titulo(self):
        diego = self.navegador("diego@exemplo.com")
        pagina = self.orcamento_pronto(diego)
        diego.enviar(pagina, f"{pagina}/envio", {})
        dados = {"decisao": "aprovar", "data": "2026-10-22"}
        protecao = diego.get(pagina).protecao
        primeira = diego.post(f"{pagina}/resposta-do-cliente", {"protecao": protecao, **dados})
        segunda = diego.post(f"{pagina}/resposta-do-cliente", {"protecao": protecao, **dados})
        self.assertEqual(primeira.status, 303)
        self.assertEqual(segunda.status, 400)
        self.assertIn("Convertido", segunda.texto)
        with UnidadeDeTrabalhoSQLite(self.caminho) as uow:
            self.assertEqual(len([t for t in uow.titulos.listar() if t.orcamento_id]), 1)


class FalhaDoCanalNaInterface(Base):
    canal = CanalQueFalha()

    def test_falha_do_canal_aparece_na_pagina(self):
        diego = self.navegador("diego@exemplo.com")
        pagina = Spec005Web.orcamento_pronto(self, diego)
        resposta = diego.enviar(pagina, f"{pagina}/envio", {})
        self.assertEqual(resposta.status, 400)
        self.assertIn("O canal de notificação não entregou o orçamento.", resposta.texto)
        self.assertIn("Rascunho", resposta.texto)
        self.assertIn("Falhou", diego.get("/mensagens").texto)


class DemonstracaoDaSpec005(unittest.TestCase):
    def test_demonstracao_tem_orcamentos_enviado_convertido_e_rejeitado(self):
        from remindme.demonstracao import preparar_demonstracao
        from remindme.inicializacao import montar
        from remindme.infraestrutura.memoria import RegistroErrosEmMemoria, RelogioFixo
        from tests.apoio import CIFRADOR_DE_TESTE

        with tempfile.TemporaryDirectory() as pasta:
            sistema = montar(str(Path(pasta).joinpath("demo.db")), RelogioFixo(AGORA), CIFRADOR_DE_TESTE, RegistroErrosEmMemoria())
            preparar_demonstracao(sistema, SENHA)
            with sistema.uow as uow:
                orcamentos = uow.orcamentos.listar()
                mensagens = uow.mensagens.listar()
                gerados = [t for t in uow.titulos.listar() if t.orcamento_id]
        estados = {o.estado for o in orcamentos}
        for estado in (EstadoOrcamento.ENVIADO, EstadoOrcamento.CONVERTIDO, EstadoOrcamento.REJEITADO):
            self.assertIn(estado, estados)
        self.assertEqual(len(mensagens), len([o for o in orcamentos if o.enviado_em]))
        self.assertEqual(len(gerados), len([o for o in orcamentos if o.estado is EstadoOrcamento.CONVERTIDO]))


if __name__ == "__main__":
    unittest.main()
