"""Melhorias pedidas pelo professor em 2026-10-30: Administrador global (OPEN-53), dados da empresa (OPEN-54),
criar conta pela entrada (OPEN-55) e SEO das páginas públicas."""

import unittest
from datetime import timedelta
from decimal import Decimal

from remindme.dominio.erros import OperacaoNegada, OperacaoRecusada
from remindme.dominio.titulo import EstadoTitulo
from remindme.dominio.usuario import Perfil
from tests.apresentacao.cliente_web import ClienteWeb
from tests.apresentacao.test_spec_017_web import HOJE, SENHA, Base

CNPJ = "11.222.333/0001-81"


class AdministradorGlobal(Base):
    def test_OPEN_53_administrador_faz_as_operacoes_que_eram_so_do_dono(self):
        s = self.sistema.servicos
        admin = s.acesso.entrar("admin@exemplo.com", SENHA).identificador
        titulo = s.titulos.registrar_pagamento(admin, self.titulo.id, Decimal("10.00"), HOJE)
        s.titulos.estornar_pagamento(admin, titulo.id, titulo.pagamentos[0].id, "Lançado em duplicidade", HOJE)
        self.assertIs(s.titulos.cancelar_titulo(admin, titulo.id, "Cobrança indevida").estado, EstadoTitulo.CANCELADO)
        orcamento = s.orcamentos.criar_orcamento(self.operador, self.cliente.id)
        s.orcamentos.incluir_item(self.operador, orcamento.id, "Serviço", Decimal("1"), Decimal("100.00"))
        s.orcamentos.informar_desconto(self.operador, orcamento.id, Decimal("30"))
        self.assertEqual(s.orcamentos.decidir_desconto(admin, orcamento.id, True).percentual_desconto, Decimal("30.00"))

    def test_OPEN_53_a_celula_do_administrador_e_fixa_na_tela_de_permissoes(self):
        admin = self.navegador("admin@exemplo.com")
        resposta = admin.enviar("/permissoes", "/permissoes", {"perfil": "ADMINISTRADOR", "operacao": "CADASTRAR_TITULO", "acao": "retirar"})
        self.assertEqual(resposta.status, 400)
        self.assertIn("OPEN-53", resposta.texto)


class DadosDaEmpresa(Base):
    def dados(self, **troca):
        return {"razao_social": "Menezes Serviços Ltda", "nome_fantasia": "Menezes", "cnpj": CNPJ,
                "telefone": "(11) 3322-4455", "email": "contato@menezes.com.br", "endereco": "Rua A, 1", **troca}

    def test_OPEN_54_dono_salva_e_cada_campo_alterado_fica_na_auditoria(self):
        carla = self.navegador("carla@exemplo.com")
        self.assertEqual(carla.enviar("/empresa", "/empresa", self.dados()).status, 303)
        self.assertEqual(carla.enviar("/empresa", "/empresa", self.dados(telefone="(11) 98765-4321")).status, 303)
        pagina = carla.get("/empresa").texto
        self.assertIn("Menezes Serviços Ltda", pagina)
        self.assertIn("(11) 98765-4321", pagina)
        with self.sistema.uow as uow:
            telefones = [(r.valor_anterior, r.valor_novo) for r in uow.auditoria.listar() if r.campo == "telefone"]
        self.assertEqual(telefones, [(None, "1133224455"), ("1133224455", "11987654321")])

    def test_OPEN_54_dados_invalidos_indicam_o_campo(self):
        resposta = self.navegador("carla@exemplo.com").enviar("/empresa", "/empresa", self.dados(cnpj="123", email="x"))
        self.assertEqual(resposta.status, 400)
        self.assertIn('id="erro-cnpj"', resposta.texto)
        self.assertIn('id="erro-email"', resposta.texto)

    def test_OPEN_54_outros_perfis_veem_mas_nao_alteram(self):
        self.navegador("carla@exemplo.com").enviar("/empresa", "/empresa", self.dados())
        helena = self.navegador("helena@exemplo.com")
        pagina = helena.get("/empresa")
        self.assertIn("Menezes Serviços Ltda", pagina.texto)
        self.assertNotIn('action="/empresa"', pagina.texto)
        with self.assertRaises(OperacaoNegada):
            self.sistema.servicos.empresa.salvar(self.operador, **self.dados())


class CriarConta(Base):
    def criar(self, navegador, **troca):
        dados = {"nome": "Paula Souza", "email": "paula@exemplo.com", "perfil": "CONTADOR", "senha": "senha-da-paula", **troca}
        return navegador.enviar("/criar-conta", "/criar-conta", dados)

    def test_OPEN_55_conta_nasce_inativa_e_so_entra_depois_de_ativada(self):
        visitante = ClienteWeb(self.sistema.web)
        resposta = self.criar(visitante)
        self.assertEqual(resposta.status, 200)
        self.assertIn("Conta criada", resposta.texto)
        with self.assertRaisesRegex(OperacaoRecusada, "aguardando ativação"):
            self.sistema.servicos.acesso.entrar("paula@exemplo.com", "senha-da-paula")
        admin = self.navegador("admin@exemplo.com")
        with self.sistema.uow as uow:
            paula = uow.usuarios.obter_por_email("paula@exemplo.com")
        self.assertFalse(paula.ativo)
        pagina = f"/usuarios/{paula.id}"
        self.assertEqual(admin.enviar(pagina, f"{pagina}/ativacao", {}).status, 303)
        self.assertEqual(ClienteWeb(self.sistema.web).entrar("paula@exemplo.com", "senha-da-paula").destino, "/painel")

    def test_OPEN_55_ninguem_pede_conta_de_administrador_e_erros_indicam_o_campo(self):
        resposta = self.criar(ClienteWeb(self.sistema.web), perfil="ADMINISTRADOR", email="diego@exemplo.com", senha="curta")
        self.assertEqual(resposta.status, 400)
        for campo in ("perfil", "email", "senha"):
            self.assertIn(f'id="erro-{campo}"', resposta.texto)

    def test_OPEN_55_formulario_sem_protecao_e_recusado(self):
        resposta = ClienteWeb(self.sistema.web).post("/criar-conta", {"nome": "X", "email": "x@x.com", "perfil": "DONO", "senha": "12345678"})
        self.assertEqual(resposta.status, 400)
        with self.sistema.uow as uow:
            self.assertIsNone(uow.usuarios.obter_por_email("x@x.com"))


class SEO(Base):
    def test_paginas_publicas_tem_descricao_e_robots_txt(self):
        visitante = ClienteWeb(self.sistema.web)
        for caminho in ("/entrar", "/criar-conta"):
            with self.subTest(caminho=caminho):
                self.assertIn('<meta name="description" content="', visitante.get(caminho).texto)
        robots = visitante.get("/robots.txt")
        self.assertEqual(robots.status, 200)
        self.assertIn("Disallow: /", robots.texto)
        self.assertIn("connect-src 'self'", robots.cabecalho("Content-Security-Policy"))


if __name__ == "__main__":
    unittest.main()
