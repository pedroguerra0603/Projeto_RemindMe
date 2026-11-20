"""Spec 010 pela interface web: calendário, cadastro, cumprimento com upload, download e painel."""

import re
import unittest
from datetime import timedelta

from remindme.dominio.obrigacao import ArquivoDeEvidencia, EstadoObrigacao
from tests.apresentacao.test_spec_017_web import HOJE, Base

PDF = b"%PDF-1.4\n%teste\n"
ID = re.compile(r"/obrigacoes/([0-9a-f]{32})")


class ObrigacoesPelaInterface(Base):
    def setUp(self):
        super().setUp()
        self.servico = self.sistema.servicos.obrigacoes
        responsaveis = {u.nome: u.id for u in self.servico.responsaveis_possiveis(self.operador)}
        self.diego_id = responsaveis["Diego Ramos"]
        self.carla_id = responsaveis["Carla Menezes"]

    def obrigacao(self, prazo=None, exige=False, periodicidade="Mensal", nome="DAS"):
        return self.servico.cadastrar_obrigacao(
            self.operador, nome, "Fiscal", periodicidade, prazo or HOJE + timedelta(days=20), self.diego_id, exige
        )

    def salva(self, obrigacao_id):
        return self.servico.obter_obrigacao(self.operador, obrigacao_id)

    def cumprir_pela_tela(self, navegador, obrigacao_id, arquivos=None, **campos):
        protecao = navegador.get(f"/obrigacoes/{obrigacao_id}").protecao
        dados = {"protecao": protecao, "data": HOJE.isoformat(), "descricao": "", **campos}
        return navegador.postar_multipart(f"/obrigacoes/{obrigacao_id}/cumprimento", dados, arquivos)

    def test_fluxo_cadastro_cumprimento_com_pdf_e_proxima_ocorrencia(self):
        diego = self.navegador("diego@exemplo.com")
        self.assertIn('href="/obrigacoes"', diego.get("/painel").texto)
        resposta = diego.enviar(
            "/obrigacoes/nova", "/obrigacoes/nova",
            {"nome": "DAS", "tipo": "Fiscal", "periodicidade": "Mensal", "prazo": (HOJE + timedelta(days=3)).isoformat(),
             "responsavel": self.diego_id, "exige_evidencia": "sim"},
        )
        self.assertEqual(resposta.status, 303)
        obrigacao_id = ID.search(resposta.destino).group(1)
        calendario = diego.get("/obrigacoes").texto
        self.assertIn("DAS", calendario)
        self.assertIn("Pendente", calendario)
        resposta = self.cumprir_pela_tela(diego, obrigacao_id, {"arquivo": ("DAS outubro.pdf", PDF)}, descricao="Guia paga")
        self.assertEqual(resposta.status, 303)
        salva = self.salva(obrigacao_id)
        self.assertIs(salva.estado, EstadoObrigacao.CUMPRIDA)
        pagina = diego.get(f"/obrigacoes/{obrigacao_id}").texto
        self.assertIn("DAS outubro.pdf", pagina)
        self.assertIn("Guia paga", pagina)
        self.assertIn(f'href="/obrigacoes/{salva.proxima_id}"', pagina)
        self.assertIn("cumprida", pagina)
        download = diego.get(f"/obrigacoes/{obrigacao_id}/evidencias/{salva.evidencias[0].id}")
        self.assertEqual((download.status, download.bruto, download.cabecalho("Content-Type")), (200, PDF, "application/pdf"))

    def test_erros_por_campo_no_cadastro_e_no_upload(self):
        diego = self.navegador("diego@exemplo.com")
        resposta = diego.enviar("/obrigacoes/nova", "/obrigacoes/nova", {"nome": "", "tipo": "", "periodicidade": "", "prazo": "", "responsavel": ""})
        self.assertEqual(resposta.status, 400)
        self.assertIn("Informe o nome da obrigação.", resposta.texto)
        self.assertIn("Escolha o tipo", resposta.texto)
        self.assertIn('aria-invalid="true"', resposta.texto)
        o = self.obrigacao(exige=True)
        resposta = self.cumprir_pela_tela(diego, o.id, {"arquivo": ("nota.txt", b"texto")}, descricao="Guia")
        self.assertEqual(resposta.status, 400)
        self.assertIn("Anexe um PDF, PNG ou JPG", resposta.texto)
        self.assertIs(self.salva(o.id).estado, EstadoObrigacao.PENDENTE)

    def test_escape_de_html_no_nome_e_na_descricao(self):
        o = self.obrigacao(nome="<script>alert(1)</script>", exige=True)
        self.servico.registrar_cumprimento(self.operador, o.id, HOJE, ArquivoDeEvidencia("a.pdf", PDF), "<b>negrito</b>")
        diego = self.navegador("diego@exemplo.com")
        for caminho in ("/obrigacoes?estado=todas", f"/obrigacoes/{o.id}"):
            texto = diego.get(caminho).texto
            self.assertNotIn("<script>alert(1)</script>", texto)
            self.assertIn("&lt;script&gt;", texto)
        self.assertNotIn("<b>negrito</b>", diego.get(f"/obrigacoes/{o.id}").texto)

    def test_CA_21_contador_nao_ve_o_menu_nem_abre_as_rotas(self):
        o = self.obrigacao()
        helena = self.navegador("helena@exemplo.com")
        self.assertNotIn('href="/obrigacoes"', helena.get("/painel").texto)
        for caminho in ("/obrigacoes", "/obrigacoes/nova", f"/obrigacoes/{o.id}"):
            with self.subTest(caminho=caminho):
                self.assertEqual(helena.get(caminho).status, 403)

    def test_CA_22_RNF_15_painel_destaca_atrasadas(self):
        self.obrigacao(prazo=HOJE - timedelta(days=2), nome="FGTS")
        for email in ("carla@exemplo.com", "diego@exemplo.com"):
            with self.subTest(email=email):
                painel = self.navegador(email).get("/painel").texto
                self.assertRegex(painel, r'class="[^"]*atraso[^"]*"[^>]*>\s*<div class="rotulo">Obrigações atrasadas</div><div class="numero">1</div>')
                self.assertIn("FGTS", painel)

    def test_CA_08_RF_77_quadro_aguardando_evidencia_no_painel(self):
        o = self.obrigacao(exige=True, nome="Aluguel da loja")
        diego = self.navegador("diego@exemplo.com")
        self.cumprir_pela_tela(diego, o.id)
        self.assertIs(self.salva(o.id).estado, EstadoObrigacao.AGUARDANDO_EVIDENCIA)
        painel = diego.get("/painel").texto
        self.assertIn("Obrigações aguardando evidência", painel)
        self.assertIn(f'href="/obrigacoes/{o.id}"', painel)
        protecao = diego.get(f"/obrigacoes/{o.id}").protecao
        resposta = diego.postar_multipart(
            f"/obrigacoes/{o.id}/evidencias", {"protecao": protecao, "descricao": "Recibo"}, {"arquivo": ("recibo.pdf", PDF)}
        )
        self.assertEqual(resposta.status, 303)
        self.assertNotIn("Obrigações aguardando evidência", diego.get("/painel").texto)

    def test_alteracao_de_prazo_e_responsavel_pela_tela(self):
        o = self.obrigacao()
        diego = self.navegador("diego@exemplo.com")
        novo = (HOJE + timedelta(days=30)).isoformat()
        self.assertEqual(diego.enviar(f"/obrigacoes/{o.id}", f"/obrigacoes/{o.id}/prazo", {"prazo": novo}).status, 303)
        self.assertEqual(diego.enviar(f"/obrigacoes/{o.id}", f"/obrigacoes/{o.id}/responsavel", {"responsavel": self.carla_id}).status, 303)
        salva = self.salva(o.id)
        self.assertEqual((salva.prazo.isoformat(), salva.responsavel_id), (novo, self.carla_id))
        pagina = diego.get(f"/obrigacoes/{o.id}").texto
        self.assertIn("Diego Ramos → Carla Menezes", pagina)
        ontem = diego.enviar(f"/obrigacoes/{o.id}", f"/obrigacoes/{o.id}/prazo", {"prazo": (HOJE - timedelta(days=1)).isoformat()})
        self.assertEqual(ontem.status, 400)
        self.assertIn("O novo prazo não pode ser anterior a hoje.", ontem.texto)

    def test_foco_1_download_e_anexo_com_nome_seguro(self):
        o = self.obrigacao(exige=True)
        self.servico.registrar_cumprimento(self.operador, o.id, HOJE, ArquivoDeEvidencia('C:\\fakepath\\DAS "março".pdf', PDF), "Guia")
        evidencia = self.salva(o.id).evidencias[0]
        resposta = self.navegador("diego@exemplo.com").get(f"/obrigacoes/{o.id}/evidencias/{evidencia.id}")
        disposicao = resposta.cabecalho("Content-Disposition")
        self.assertTrue(disposicao.startswith("attachment;"))
        self.assertIn("filename*=UTF-8''DAS%20mar%C3%A7o.pdf", disposicao)
        self.assertNotIn("\\", disposicao)
        self.assertEqual(resposta.cabecalho("X-Content-Type-Options"), "nosniff")
        outra = self.navegador("diego@exemplo.com").get(f"/obrigacoes/{o.id}/evidencias/{'0' * 32}")
        self.assertEqual(outra.status, 400)

    def test_foco_2_campo_de_arquivo_vazio_vale_como_sem_anexo(self):
        o = self.obrigacao(exige=True)
        diego = self.navegador("diego@exemplo.com")
        resposta = self.cumprir_pela_tela(diego, o.id, {"arquivo": ("", b"")})
        self.assertEqual(resposta.status, 303)
        self.assertIs(self.salva(o.id).estado, EstadoObrigacao.AGUARDANDO_EVIDENCIA)

    def test_foco_3_multipart_fora_da_rota_ou_grande_demais_e_recusado(self):
        o = self.obrigacao(exige=True)
        diego = self.navegador("diego@exemplo.com")
        protecao = diego.get("/obrigacoes/nova").protecao
        fora = diego.postar_multipart("/obrigacoes/nova", {"protecao": protecao, "nome": "X"})
        self.assertIn(fora.status, (403, 413))
        grande = self.cumprir_pela_tela(diego, o.id, {"arquivo": ("g.pdf", b"%PDF-" + b"0" * (6 * 1024 * 1024))})
        self.assertEqual(grande.status, 413)
        sem_protecao = diego.postar_multipart(f"/obrigacoes/{o.id}/cumprimento", {"data": HOJE.isoformat()}, {"arquivo": ("a.pdf", PDF)})
        self.assertEqual(sem_protecao.status, 403)
        self.assertIs(self.salva(o.id).estado, EstadoObrigacao.PENDENTE)

    def test_cumprimento_enviado_duas_vezes_gera_uma_proxima(self):
        o = self.obrigacao()
        diego = self.navegador("diego@exemplo.com")
        protecao = diego.get(f"/obrigacoes/{o.id}").protecao
        dados = {"protecao": protecao, "data": HOJE.isoformat(), "descricao": ""}
        self.assertEqual(diego.postar_multipart(f"/obrigacoes/{o.id}/cumprimento", dados).status, 303)
        self.assertEqual(diego.postar_multipart(f"/obrigacoes/{o.id}/cumprimento", dados).status, 400)
        serie = self.servico.ocorrencias_da_serie(self.operador, o.id)
        self.assertEqual(len(serie), 2)

    def test_calendario_esconde_cumpridas_por_padrao_e_mostra_responsavel_inativo(self):
        cumprida = self.obrigacao(periodicidade="Única", nome="Licença antiga")
        self.servico.registrar_cumprimento(self.operador, cumprida.id, HOJE)
        diego = self.navegador("diego@exemplo.com")
        self.assertNotIn("Licença antiga", diego.get("/obrigacoes").texto)
        self.assertIn("Licença antiga", diego.get("/obrigacoes?estado=todas").texto)
        self.assertIn("Licença antiga", diego.get("/obrigacoes?estado=CUMPRIDA").texto)

    def test_caixa_de_saida_mostra_alerta_ao_usuario(self):
        o = self.obrigacao(prazo=HOJE + timedelta(days=2))
        self.sistema.agendador.executar_uma_vez()
        pagina = self.navegador("diego@exemplo.com").get("/mensagens").texto
        self.assertIn("Obrigação a vencer: DAS", pagina)
        self.assertIn("Diego Ramos", pagina)
        self.assertIn(f'href="/obrigacoes/{o.id}"', pagina)

    def test_auditoria_descreve_e_liga_a_obrigacao_e_a_evidencia(self):
        from remindme.apresentacao.web.paginas import _descrever

        self.assertEqual(_descrever("obrigacao " + "a" * 32), ("Obrigação aaaaaaaa", "/obrigacoes/" + "a" * 32))
        self.assertEqual(
            _descrever(f"obrigacao {'a' * 32}, evidencia {'b' * 32}"), ("Evidência da obrigação aaaaaaaa", "/obrigacoes/" + "a" * 32)
        )


class DemonstracaoDeObrigacoes(unittest.TestCase):
    def test_demonstracao_tem_obrigacoes_em_todos_os_estados(self):
        import tempfile
        from pathlib import Path

        from remindme.demonstracao import preparar_demonstracao
        from remindme.inicializacao import montar
        from tests.apoio import CIFRADOR_DE_TESTE

        with tempfile.TemporaryDirectory() as pasta:
            sistema = montar(str(Path(pasta) / "demo.db"), cifrador=CIFRADOR_DE_TESTE)
            preparar_demonstracao(sistema, "senha-de-teste")
            dona = sistema.servicos.acesso.entrar("carla@demo.example", "senha-de-teste").identificador
            estados = {v.estado for v in sistema.servicos.obrigacoes.consultar_calendario(dona)}
            self.assertEqual(estados, set(EstadoObrigacao))
            mensagens = sistema.servicos.mensagens.consultar(dona)
            self.assertTrue(any(m.assunto.startswith("Obrigação atrasada") for m in mensagens))
            self.assertTrue(any(m.assunto.startswith("Obrigação a vencer") for m in mensagens))


if __name__ == "__main__":
    unittest.main()
