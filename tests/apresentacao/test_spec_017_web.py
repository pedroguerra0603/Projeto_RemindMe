"""Critérios de aceitação da Spec 017 pela interface web, no próprio processo (testes de API, OPEN-29)."""

import re
import shutil
import subprocess
import tempfile
import threading
import unittest
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path

from remindme.aplicacao.servico_titulos import FiltroTitulos
from remindme.demonstracao import preparar_demonstracao
from remindme.dominio.operacoes import Operacao
from remindme.dominio.titulo import EstadoTitulo
from remindme.dominio.usuario import Perfil
from remindme.inicializacao import ConfiguracaoInvalida, conferir_endereco, criar_servidor, montar, principal
from remindme.infraestrutura.memoria import RegistroErrosEmMemoria, RelogioFixo
from tests.apoio import CIFRADOR_DE_TESTE
from tests.apresentacao.cliente_web import ClienteWeb

SENHA = "senha-de-teste"
HOJE = date(2026, 10, 22)
AGORA = datetime(2026, 10, 22, 15, 0, tzinfo=timezone.utc)  # 12h em São Paulo
OUTRO_ID = "0" * 32


class Base(unittest.TestCase):
    def setUp(self):
        self._pasta = tempfile.TemporaryDirectory()
        self.caminho = str(Path(self._pasta.name).joinpath("remindme.db"))
        self.relogio = RelogioFixo(AGORA)
        self.erros = RegistroErrosEmMemoria()
        self.sistema = montar(self.caminho, self.relogio, CIFRADOR_DE_TESTE, self.erros)
        acesso = self.sistema.servicos.acesso
        acesso.criar_primeiro_administrador("Ana Admin", "admin@exemplo.com", SENHA)
        admin = acesso.entrar("admin@exemplo.com", SENHA).identificador
        for nome, email, perfil in (
            ("Carla Menezes", "carla@exemplo.com", Perfil.DONO),
            ("Diego Ramos", "diego@exemplo.com", Perfil.OPERADOR_FINANCEIRO),
            ("Helena Prado", "helena@exemplo.com", Perfil.CONTADOR),
        ):
            acesso.cadastrar_usuario(admin, nome, email, perfil, SENHA)
        self.operador = acesso.entrar("diego@exemplo.com", SENHA).identificador
        self.cliente = self.sistema.servicos.clientes.cadastrar_cliente(
            self.operador, "Padaria Pão Quente Ltda", "11.222.333/0001-81", "p@padaria.com"
        )
        self.titulo = self.sistema.servicos.titulos.cadastrar_titulo(
            self.operador, self.cliente.id, Decimal("100.00"), HOJE + timedelta(days=10)
        )

    def tearDown(self):
        self._pasta.cleanup()

    def navegador(self, email=None, https=False) -> ClienteWeb:
        cliente = ClienteWeb(self.sistema.web, https=https)
        if email:
            resposta = cliente.entrar(email, SENHA)
            self.assertEqual((resposta.status, resposta.destino), (303, "/painel"))
        return cliente

    def titulo_salvo(self):
        return self.sistema.servicos.titulos.obter_titulo(self.operador, self.titulo.id)


class AcessoPelaInterface(Base):
    def test_CA_01_RNF_01_sem_sessao_toda_pagina_protegida_leva_a_entrada(self):
        t, c = self.titulo.id, self.cliente.id
        paginas = [
            "/painel", "/clientes", "/clientes/novo", f"/clientes/{c}", f"/clientes/{c}/editar", "/titulos",
            "/titulos/novo", f"/titulos/{t}", f"/titulos/{t}/cancelamento", f"/titulos/{t}/pagamentos/{OUTRO_ID}/estorno",
            "/auditoria", "/usuarios", "/usuarios/novo", f"/usuarios/{OUTRO_ID}", "/permissoes",
        ]
        envios = [
            "/sair", "/clientes/novo", f"/clientes/{c}/editar", "/titulos/novo", "/titulos/verificar-vencimentos",
            f"/titulos/{t}/pagamentos", f"/titulos/{t}/cancelamento", "/usuarios/novo", "/permissoes",
        ]
        navegador = ClienteWeb(self.sistema.web, cookies={"remindme_sessao": "sessao-inventada"})
        for metodo, caminhos in (("GET", paginas), ("POST", envios)):
            for caminho in caminhos:
                with self.subTest(metodo=metodo, caminho=caminho):
                    resposta = navegador.pedir(metodo, caminho, {"protecao": "x"})
                    self.assertEqual((resposta.status, resposta.destino), (303, "/entrar"))
                    self.assertEqual(resposta.texto, "")
        self.assertEqual(self.titulo_salvo().estado, EstadoTitulo.ABERTO)

    def test_CA_02_RF_65_painel_com_nome_perfil_e_menu_do_perfil(self):
        for email, nome, perfil, com, sem in (
            ("helena@exemplo.com", "Helena Prado", "Contador", ["/titulos", "/clientes", "/auditoria"], ["/usuarios", "/titulos/novo", "/clientes/novo"]),
            ("admin@exemplo.com", "Ana Admin", "Administrador", ["/auditoria", "/usuarios", "/permissoes"], ["/titulos", "/clientes"]),
            ("diego@exemplo.com", "Diego Ramos", "Operador Financeiro", ["/titulos", "/clientes", "/titulos/novo"], ["/auditoria", "/usuarios"]),
        ):
            with self.subTest(perfil=perfil):
                painel = self.navegador(email).get("/painel")
                self.assertEqual(painel.status, 200)
                self.assertIn(nome, painel.texto)
                self.assertIn(f'<span class="perfil">{perfil}</span>', painel.texto)
                for href in com:
                    self.assertIn(f'href="{href}"', painel.texto)
                for href in sem:
                    self.assertNotIn(f'href="{href}"', painel.texto)

    def test_CA_03_RF_66_credenciais_invalidas_voltam_com_mensagem_generica_e_sem_sessao(self):
        for email, senha in (("ninguem@exemplo.com", SENHA), ("diego@exemplo.com", "senha-errada")):
            with self.subTest(email=email):
                navegador = ClienteWeb(self.sistema.web)
                resposta = navegador.post("/entrar", {"protecao": navegador.get("/entrar").protecao, "email": email, "senha": senha})
                self.assertEqual(resposta.status, 401)
                self.assertIn("E-mail ou senha incorretos.", resposta.texto)
                self.assertNotIn("remindme_sessao", navegador.cookies)

    def test_CA_04_RF_67_RNF_03_contador_e_negado_na_pagina_e_no_envio(self):
        navegador = self.navegador("helena@exemplo.com")
        pagina = navegador.get("/titulos/novo")
        self.assertEqual(pagina.status, 403)
        self.assertIn("RB-03", pagina.texto)
        protecao = navegador.get("/painel").protecao
        envio = navegador.post(
            "/titulos/novo",
            {"protecao": protecao, "cliente": self.cliente.id, "valor": "50,00", "vencimento": "2026-11-30"},
        )
        self.assertEqual(envio.status, 403)
        self.assertIn("RB-03", envio.texto)
        self.assertEqual(len(self.sistema.servicos.titulos.consultar_titulos(self.operador, FiltroTitulos(), HOJE)), 1)

    def test_CA_05_RNF_14_formulario_volta_com_os_valores_e_o_motivo_no_campo(self):
        navegador = self.navegador("diego@exemplo.com")
        resposta = navegador.enviar(
            "/clientes/novo", "/clientes/novo",
            {"nome": "Sérgio Tavares", "documento": "529.982.247-24", "contato": "sergio@exemplo.com"},
        )
        self.assertEqual(resposta.status, 400)
        self.assertIn('value="Sérgio Tavares"', resposta.texto)
        self.assertIn('value="529.982.247-24"', resposta.texto)
        self.assertRegex(resposta.texto, r'id="documento"[^>]*aria-invalid="true"')
        self.assertIn('id="erro-documento"', resposta.texto)


class TitulosPelaInterface(Base):
    def test_CA_06_UC_06_pagamento_integral_pela_tela_baixa_o_titulo(self):
        navegador = self.navegador("diego@exemplo.com")
        pagina = navegador.get(f"/titulos/{self.titulo.id}")
        resposta = navegador.post(
            f"/titulos/{self.titulo.id}/pagamentos",
            {"protecao": pagina.protecao, "pedido": pagina.pedido, "valor": "100,00", "data": HOJE.isoformat()},
        )
        self.assertEqual((resposta.status, resposta.destino), (303, f"/titulos/{self.titulo.id}?aviso=pagamento"))
        titulo = navegador.get(resposta.destino)
        self.assertIn("Pagamento registrado.", titulo.texto)
        self.assertRegex(titulo.texto, r"Saldo</dt><dd>R\$ 0,00")
        self.assertIn('class="selo baixado grande"', titulo.texto)

    def test_CA_07_OPEN_25_o_mesmo_formulario_enviado_duas_vezes_registra_um_pagamento(self):
        navegador = self.navegador("diego@exemplo.com")
        pagina = navegador.get(f"/titulos/{self.titulo.id}")
        dados = {"protecao": pagina.protecao, "pedido": pagina.pedido, "valor": "30,00", "data": HOJE.isoformat()}
        for _ in range(2):
            self.assertEqual(navegador.post(f"/titulos/{self.titulo.id}/pagamentos", dados).status, 303)
        titulo = self.titulo_salvo()
        self.assertEqual(len(titulo.pagamentos), 1)
        self.assertEqual(titulo.saldo, Decimal("70.00"))

    def test_CA_08_INV_3_envio_sem_a_protecao_da_sessao_e_recusado(self):
        navegador = self.navegador("diego@exemplo.com")
        for protecao in ("", "protecao-de-outro-site"):
            with self.subTest(protecao=protecao):
                resposta = navegador.post(
                    f"/titulos/{self.titulo.id}/pagamentos",
                    {"protecao": protecao, "valor": "100,00", "data": HOJE.isoformat()},
                )
                self.assertEqual(resposta.status, 403)
                self.assertIn("Formulário recusado", resposta.texto)
        self.assertEqual(self.titulo_salvo().pagamentos, [])

    def test_CA_09_INV_4_valor_com_html_aparece_escapado(self):
        self.sistema.servicos.clientes.cadastrar_cliente(
            self.operador, "<script>alert('x')</script> Ltda", "529.982.247-25", "a@b.com"
        )
        pagina = self.navegador("diego@exemplo.com").get("/clientes")
        self.assertIn("&lt;script&gt;alert(&#x27;x&#x27;)&lt;/script&gt; Ltda", pagina.texto)
        self.assertNotIn("<script>", pagina.texto)

    def test_CA_10_RNF_15_painel_destaca_os_vencidos_com_o_total_em_atraso(self):
        titulos = self.sistema.servicos.titulos
        for valor, dias in (("300.00", -3), ("200.00", -1)):
            titulos.cadastrar_titulo(self.operador, self.cliente.id, Decimal(valor), HOJE + timedelta(days=dias))
        self.sistema.agendador.executar_uma_vez()
        painel = self.navegador("carla@exemplo.com").get("/painel")
        self.assertRegex(painel.texto, r'indicador atraso".*?R\$ 500,00')
        self.assertEqual(painel.texto.count('<tr class="vencido">'), 2)

    def test_CA_11_historico_do_titulo_mostra_quem_estornou_quando_e_o_motivo(self):
        titulos = self.sistema.servicos.titulos
        titulo = titulos.registrar_pagamento(self.operador, self.titulo.id, Decimal("100.00"), HOJE)
        dona = self.navegador("carla@exemplo.com")
        estorno = f"/titulos/{titulo.id}/pagamentos/{titulo.pagamentos[0].id}/estorno"
        resposta = dona.enviar(estorno, estorno, {"motivo": "Cheque devolvido"})
        self.assertEqual(resposta.status, 303)
        pagina = dona.get(f"/titulos/{titulo.id}")
        self.assertIn("estornar pagamento", pagina.texto)
        self.assertIn("Carla Menezes", pagina.texto)
        self.assertIn("motivo: Cheque devolvido", pagina.texto)
        self.assertIn("22/10/2026 12:00", pagina.texto)

    def test_cancelamento_pela_tela_exige_motivo(self):
        dona = self.navegador("carla@exemplo.com")
        caminho = f"/titulos/{self.titulo.id}/cancelamento"
        sem_motivo = dona.enviar(caminho, caminho, {"motivo": " "})
        self.assertEqual(sem_motivo.status, 400)
        self.assertIn('id="erro-motivo"', sem_motivo.texto)
        self.assertEqual(dona.enviar(caminho, caminho, {"motivo": "Desistência"}).status, 303)
        self.assertIs(self.titulo_salvo().estado, EstadoTitulo.CANCELADO)

    def test_cadastro_de_titulo_pela_tela_com_valor_em_formato_brasileiro(self):
        navegador = self.navegador("diego@exemplo.com")
        resposta = navegador.enviar(
            "/titulos/novo", "/titulos/novo",
            {"cliente": self.cliente.id, "valor": "1.234,56", "vencimento": "2026-11-30", "condicao": "Pix"},
        )
        self.assertEqual(resposta.status, 303)
        novo = navegador.get(resposta.destino)
        self.assertIn("R$ 1.234,56", novo.texto)
        invalido = navegador.enviar("/titulos/novo", "/titulos/novo", {"cliente": self.cliente.id, "valor": "abc", "vencimento": ""})
        self.assertEqual(invalido.status, 400)
        self.assertIn('id="erro-valor"', invalido.texto)


class BancoEAgendador(Base):
    def test_CA_12_A7_titulo_continua_depois_de_montar_a_aplicacao_de_novo(self):
        self.sistema.servicos.titulos.registrar_pagamento(self.operador, self.titulo.id, Decimal("40.00"), HOJE)
        outro = montar(self.caminho, self.relogio, CIFRADOR_DE_TESTE, self.erros)
        pagina = ClienteWeb(outro.web)
        pagina.entrar("diego@exemplo.com", SENHA)
        self.assertRegex(pagina.get(f"/titulos/{self.titulo.id}").texto, r"Saldo</dt><dd>R\$ 60,00")

    def test_CA_15_A5_agendador_vence_o_titulo_com_registro_automatico(self):
        vencido = self.sistema.servicos.titulos.cadastrar_titulo(
            self.operador, self.cliente.id, Decimal("10.00"), HOJE - timedelta(days=1)
        )
        self.assertEqual(self.sistema.agendador.executar_uma_vez(), [vencido.id])
        with self.sistema.uow as uow:
            registro = uow.auditoria.listar()[-1]
        self.assertTrue(registro.automatica)
        self.assertEqual(registro.rotina, "verificação de vencimento")
        self.assertEqual(self.sistema.agendador.executar_uma_vez(), [])

    def test_OPEN_48_o_agendador_roda_ao_iniciar_e_continua_em_segundo_plano(self):
        vencido = self.sistema.servicos.titulos.cadastrar_titulo(
            self.operador, self.cliente.id, Decimal("10.00"), HOJE - timedelta(days=1)
        )
        self.sistema.agendador.iniciar()
        try:
            for _ in range(100):
                if self.sistema.servicos.titulos.obter_titulo(self.operador, vencido.id).estado is EstadoTitulo.VENCIDO:
                    break
                threading.Event().wait(0.05)
        finally:
            self.sistema.agendador.parar()
        self.assertIs(self.sistema.servicos.titulos.obter_titulo(self.operador, vencido.id).estado, EstadoTitulo.VENCIDO)


class SegurancaDoServidor(Base):
    def test_CA_16_OPEN_38_sem_certificado_so_a_propria_maquina(self):
        conferir_endereco("127.0.0.1", None, None)
        for host in ("0.0.0.0", "192.168.0.10"):
            with self.subTest(host=host), self.assertRaisesRegex(ConfiguracaoInvalida, "HTTPS"):
                conferir_endereco(host, None, None)
        with self.assertRaises(ConfiguracaoInvalida):
            conferir_endereco("127.0.0.1", "certificado.pem", None)

    def test_CA_16_RNF_05_com_https_o_cookie_e_seguro_e_ha_hsts(self):
        navegador = ClienteWeb(self.sistema.web, https=True)
        protecao = navegador.get("/entrar").protecao
        resposta = navegador.post("/entrar", {"protecao": protecao, "email": "diego@exemplo.com", "senha": SENHA})
        sessao = next(c for c in resposta.cookies_definidos() if c.startswith("remindme_sessao="))
        self.assertIn("Secure", sessao)
        self.assertEqual(resposta.cabecalho("Strict-Transport-Security"), "max-age=31536000")

    @unittest.skipUnless(shutil.which("openssl"), "openssl não está disponível para gerar um certificado de teste")
    def test_CA_16_RNF_05_servidor_com_certificado_atende_por_https(self):
        import http.client
        import ssl

        certificado = str(Path(self._pasta.name).joinpath("teste.crt"))
        chave = str(Path(self._pasta.name).joinpath("teste.chave"))
        subprocess.run(
            ["openssl", "req", "-x509", "-newkey", "rsa:2048", "-nodes", "-days", "1", "-subj", "/CN=localhost",
             "-keyout", chave, "-out", certificado],
            check=True, capture_output=True,
        )
        servidor = criar_servidor(self.sistema, "127.0.0.1", 0, certificado, chave)
        linha = threading.Thread(target=servidor.serve_forever, daemon=True)
        linha.start()
        try:
            contexto = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
            contexto.check_hostname = False
            contexto.verify_mode = ssl.CERT_NONE  # certificado autoassinado: o teste é do HTTPS, e não da cadeia
            conexao = http.client.HTTPSConnection("127.0.0.1", servidor.server_address[1], context=contexto, timeout=10)
            conexao.request("GET", "/entrar")
            resposta = conexao.getresponse()
            self.assertEqual(resposta.status, 200)
            self.assertIn("Secure", resposta.getheader("Set-Cookie"))
        finally:
            servidor.shutdown()
            servidor.server_close()

    def test_CA_21_cabecalhos_de_seguranca_e_cookie_protegido(self):
        navegador = ClienteWeb(self.sistema.web)
        entrada = navegador.get("/entrar")
        resposta = navegador.post("/entrar", {"protecao": entrada.protecao, "email": "diego@exemplo.com", "senha": SENHA})
        painel = navegador.get("/painel")
        for pagina in (entrada, resposta, painel):
            with self.subTest(status=pagina.status):
                politica = pagina.cabecalho("Content-Security-Policy")
                self.assertIn("default-src 'none'", politica)
                self.assertIn("frame-ancestors 'none'", politica)
                # Só scripts do próprio site (o botão de tema): nada inline e nada de fora.
                self.assertIn("script-src 'self';", politica)
                self.assertNotIn("unsafe-inline", politica)
                self.assertEqual(pagina.cabecalho("X-Content-Type-Options"), "nosniff")
                self.assertEqual(pagina.cabecalho("X-Frame-Options"), "DENY")
        sessao = next(c for c in resposta.cookies_definidos() if c.startswith("remindme_sessao="))
        self.assertIn("HttpOnly", sessao)
        self.assertIn("SameSite=Lax", sessao)
        self.assertEqual(painel.cabecalho("Cache-Control"), "no-store")


class AdministracaoPelaInterface(Base):
    def test_CA_17_UC_02_administrador_cadastra_usuario_e_retira_permissao_pela_tela(self):
        admin = self.navegador("admin@exemplo.com")
        resposta = admin.enviar(
            "/usuarios/novo", "/usuarios/novo",
            {"nome": "Bruno Lima", "email": "bruno@exemplo.com", "perfil": "OPERADOR_FINANCEIRO", "senha": SENHA},
        )
        self.assertEqual(resposta.status, 303)
        bruno = self.navegador("bruno@exemplo.com")
        resposta = admin.enviar(
            "/permissoes", "/permissoes",
            {"perfil": "OPERADOR_FINANCEIRO", "operacao": "CADASTRAR_TITULO", "acao": "retirar"},
        )
        self.assertEqual((resposta.status, resposta.destino), (303, "/permissoes?aviso=permissao"))
        self.assertEqual(bruno.get("/titulos/novo").status, 403)
        fixada = admin.enviar(
            "/permissoes", "/permissoes",
            {"perfil": "OPERADOR_FINANCEIRO", "operacao": "ESTORNAR_PAGAMENTO", "acao": "conceder"},
        )
        self.assertEqual(fixada.status, 400)
        self.assertIn("RB-02", fixada.texto)
        with self.sistema.uow as uow:
            self.assertFalse(uow.permissoes.obter().permite(Perfil.OPERADOR_FINANCEIRO, Operacao.ESTORNAR_PAGAMENTO))

    def test_CA_18_A6_sair_encerra_a_sessao(self):
        navegador = self.navegador("diego@exemplo.com")
        sessao_antiga = navegador.cookies["remindme_sessao"]
        resposta = navegador.enviar("/painel", "/sair", {})
        self.assertEqual((resposta.status, resposta.destino), (303, "/entrar?aviso=saiu"))
        self.assertNotIn("remindme_sessao", navegador.cookies)
        antigo = ClienteWeb(self.sistema.web, cookies={"remindme_sessao": sessao_antiga})
        self.assertEqual(antigo.get("/painel").destino, "/entrar")

    def test_usuario_inativado_pela_tela_perde_a_sessao_aberta(self):
        diego = self.navegador("diego@exemplo.com")
        admin = self.navegador("admin@exemplo.com")
        with self.sistema.uow as uow:
            usuario = uow.usuarios.obter_por_email("diego@exemplo.com")
        caminho = f"/usuarios/{usuario.id}"
        self.assertEqual(admin.enviar(caminho, f"{caminho}/inativacao", {}).status, 303)
        self.assertEqual(diego.get("/painel").destino, "/entrar")


class Demonstracao(unittest.TestCase):
    def test_CA_19_A8_demonstracao_tem_todos_os_perfis_e_todos_os_estados(self):
        with tempfile.TemporaryDirectory() as pasta:
            sistema = montar(str(Path(pasta).joinpath("demo.db")), RelogioFixo(AGORA), CIFRADOR_DE_TESTE, RegistroErrosEmMemoria())
            usuarios = preparar_demonstracao(sistema, SENHA)
            self.assertEqual({perfil for _, _, perfil in usuarios}, {p.value for p in Perfil if p is not Perfil.CLIENTE})
            with sistema.uow as uow:
                estados = {t.estado for t in uow.titulos.listar()}
                self.assertEqual(len(uow.clientes.listar()), 5)
            self.assertEqual(estados, {EstadoTitulo.ABERTO, EstadoTitulo.VENCIDO, EstadoTitulo.BAIXADO, EstadoTitulo.CANCELADO})
            self.assertEqual(ClienteWeb(sistema.web).entrar("carla@demo.example", SENHA).status, 303)


class ErrosDaInterface(Base):
    def test_CA_20_RNF_21_erro_inesperado_mostra_a_correlacao_e_fica_registrado(self):
        navegador = self.navegador("diego@exemplo.com")

        def quebrar(*argumentos, **nomeados):
            raise RuntimeError("defeito simulado")

        self.sistema.servicos.clientes.consultar_clientes = quebrar
        resposta = navegador.get("/clientes")
        self.assertEqual(resposta.status, 500)
        self.assertNotIn("defeito simulado", resposta.texto)
        correlacao = re.search(r'class="mono">([0-9a-f]{32})<', resposta.texto).group(1)
        self.assertEqual([r.correlacao for r in self.erros.registros], [correlacao])

    def test_CA_22_E4_pagina_inexistente(self):
        resposta = self.navegador("diego@exemplo.com").get("/nao-existe")
        self.assertEqual(resposta.status, 404)
        self.assertIn("Página não encontrada", resposta.texto)

    def test_metodo_errado_envio_grande_demais_e_arquivos_estaticos(self):
        navegador = self.navegador("diego@exemplo.com")
        self.assertEqual(navegador.post("/painel", {"protecao": "x"}).status, 405)
        self.assertEqual(navegador.pedir("POST", "/entrar", corpo=b"a" * (65 * 1024)).status, 413)
        estilo = navegador.get("/estatico/estilo.css")
        self.assertEqual((estilo.status, estilo.cabecalho("Content-Type")), (200, "text/css; charset=utf-8"))
        self.assertEqual(navegador.get("/estatico/segredo.txt").status, 404)


class LinhaDeComando(unittest.TestCase):
    def test_OPEN_38_servidor_na_rede_sem_certificado_nao_inicia(self):
        self.assertEqual(principal(["--host", "0.0.0.0", "--banco", ":memory:"]), 2)

    def test_demonstracao_nao_apaga_banco_existente_sem_pedir(self):
        with tempfile.TemporaryDirectory() as pasta:
            banco = Path(pasta).joinpath("demo.db")
            banco.write_bytes(b"")
            self.assertEqual(principal(["demonstracao", "--banco", str(banco), "--sem-servidor"]), 1)


if __name__ == "__main__":
    unittest.main()
