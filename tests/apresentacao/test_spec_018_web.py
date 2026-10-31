"""Spec 018 pela interface web: fornecedores, contas a pagar, painel e Permissões sem o perfil Cliente."""

import re
import unittest
from datetime import timedelta
from decimal import Decimal

from remindme.dominio.conta_pagar import EstadoContaPagar
from tests.apresentacao.cliente_web import ClienteWeb
from tests.apresentacao.test_spec_017_web import HOJE, SENHA, Base

CNPJ = "11.222.333/0001-81"


class FornecedoresEContasPelaInterface(Base):
    def setUp(self):
        super().setUp()
        servicos = self.sistema.servicos
        self.pneus = servicos.fornecedores.cadastrar_fornecedor(self.operador, "Distribuidora de Pneus Ltda", CNPJ, "v@pneus.example")

    def conta(self, valor="1200.00", dias=10):
        return self.sistema.servicos.contas_pagar.cadastrar_conta(
            self.operador, self.pneus.id, "20 pneus aro 14", Decimal(valor), HOJE + timedelta(days=dias), "Boleto"
        )

    def conta_salva(self, conta_id):
        return self.sistema.servicos.contas_pagar.obter_conta(self.operador, conta_id)

    def test_CA_15_operador_cadastra_fornecedor_e_conta_e_paga_pela_tela(self):
        diego = self.navegador("diego@exemplo.com")
        resposta = diego.enviar(
            "/fornecedores/novo", "/fornecedores/novo",
            {"nome": "Auto Peças Silva", "documento": "529.982.247-25", "contato": "(11) 98765-4321"},
        )
        self.assertEqual(resposta.status, 303)
        fornecedor_id = re.search(r"/fornecedores/([0-9a-f]{32})", resposta.destino).group(1)
        self.assertIn("Auto Peças Silva", diego.get(f"/fornecedores/{fornecedor_id}").texto)
        resposta = diego.enviar(
            "/contas-a-pagar/nova", "/contas-a-pagar/nova",
            {"fornecedor": fornecedor_id, "descricao": "Pastilhas de freio", "valor": "1.234,56",
             "vencimento": (HOJE + timedelta(days=5)).isoformat(), "condicao": "Pix"},
        )
        self.assertEqual(resposta.status, 303)
        conta_id = re.search(r"/contas-a-pagar/([0-9a-f]{32})", resposta.destino).group(1)
        pagina = diego.get(f"/contas-a-pagar/{conta_id}")
        self.assertIn("Pastilhas de freio", pagina.texto)
        self.assertRegex(pagina.texto, r"Saldo</dt><dd>R\$ 1\.234,56")
        resposta = diego.post(
            f"/contas-a-pagar/{conta_id}/pagamentos",
            {"protecao": pagina.protecao, "pedido": pagina.pedido, "valor": "1.234,56", "data": HOJE.isoformat()},
        )
        self.assertEqual(resposta.status, 303)
        self.assertIs(self.conta_salva(conta_id).estado, EstadoContaPagar.PAGA)

    def test_RNF_14_recusas_voltam_com_o_motivo_no_campo(self):
        diego = self.navegador("diego@exemplo.com")
        resposta = diego.enviar("/fornecedores/novo", "/fornecedores/novo", {"nome": "Outra", "documento": CNPJ, "contato": "a@b.example"})
        self.assertEqual(resposta.status, 400)
        self.assertIn('id="erro-documento"', resposta.texto)
        resposta = diego.enviar(
            "/contas-a-pagar/nova", "/contas-a-pagar/nova",
            {"fornecedor": self.pneus.id, "descricao": "", "valor": "abc", "vencimento": ""},
        )
        self.assertEqual(resposta.status, 400)
        for campo in ("valor", "descricao"):
            self.assertIn(f'id="erro-{campo}"', resposta.texto)
        conta = self.conta("100.00")
        pagina = diego.get(f"/contas-a-pagar/{conta.id}")
        resposta = diego.post(
            f"/contas-a-pagar/{conta.id}/pagamentos",
            {"protecao": pagina.protecao, "pedido": pagina.pedido, "valor": "100,01", "data": HOJE.isoformat()},
        )
        self.assertEqual(resposta.status, 400)
        self.assertIn('id="erro-valor"', resposta.texto)

    def test_pagamento_de_conta_enviado_duas_vezes_registra_um(self):
        diego = self.navegador("diego@exemplo.com")
        conta = self.conta("300.00")
        pagina = diego.get(f"/contas-a-pagar/{conta.id}")
        dados = {"protecao": pagina.protecao, "pedido": pagina.pedido, "valor": "100,00", "data": HOJE.isoformat()}
        diego.post(f"/contas-a-pagar/{conta.id}/pagamentos", dados)
        diego.post(f"/contas-a-pagar/{conta.id}/pagamentos", dados)
        self.assertEqual(self.conta_salva(conta.id).saldo, Decimal("200.00"))

    def test_CA_15_dono_estorna_e_cancela_pela_tela_com_motivo(self):
        carla = self.navegador("carla@exemplo.com")
        conta = self.sistema.servicos.contas_pagar.registrar_pagamento(self.operador, self.conta("50.00").id, Decimal("50.00"), HOJE)
        caminho = f"/contas-a-pagar/{conta.id}/pagamentos/{conta.pagamentos[0].id}/estorno"
        self.assertEqual(carla.enviar(caminho, caminho, {"motivo": ""}).status, 400)
        self.assertEqual(carla.enviar(caminho, caminho, {"motivo": "Boleto devolvido"}).status, 303)
        self.assertIs(self.conta_salva(conta.id).estado, EstadoContaPagar.ABERTA)
        caminho = f"/contas-a-pagar/{conta.id}/cancelamento"
        self.assertEqual(carla.enviar(caminho, caminho, {"motivo": "Compra desfeita"}).status, 303)
        self.assertIs(self.conta_salva(conta.id).estado, EstadoContaPagar.CANCELADA)

    def test_CA_13_contador_ve_as_listas_mas_nao_os_formularios(self):
        self.conta()
        helena = self.navegador("helena@exemplo.com")
        lista = helena.get("/contas-a-pagar")
        self.assertEqual(lista.status, 200)
        self.assertIn("20 pneus aro 14", lista.texto)
        self.assertNotIn('href="/contas-a-pagar/nova"', lista.texto)
        self.assertEqual(helena.get("/fornecedores").status, 200)
        for caminho in ("/contas-a-pagar/nova", "/fornecedores/novo", f"/fornecedores/{self.pneus.id}/editar"):
            with self.subTest(caminho=caminho):
                self.assertEqual(helena.get(caminho).status, 403)

    def test_operador_nao_ve_estorno_nem_cancelamento(self):
        conta = self.sistema.servicos.contas_pagar.registrar_pagamento(self.operador, self.conta().id, Decimal("10.00"), HOJE)
        pagina = self.navegador("diego@exemplo.com").get(f"/contas-a-pagar/{conta.id}").texto
        self.assertNotIn("/estorno", pagina)
        self.assertNotIn("/cancelamento", pagina)
        self.assertEqual(self.navegador("diego@exemplo.com").get(f"/contas-a-pagar/{conta.id}/cancelamento").status, 403)

    def test_RF_89_filtro_por_fornecedor_e_estado(self):
        self.conta(dias=-3)
        self.conta("77.00", dias=4)
        self.sistema.agendador.executar_uma_vez()
        pagina = self.navegador("diego@exemplo.com").get(f"/contas-a-pagar?fornecedor={self.pneus.id}&estado=VENCIDA").texto
        self.assertIn("1.200,00", pagina)
        self.assertNotIn("77,00", pagina)

    def test_CA_14_painel_mostra_a_pagar_e_o_saldo_previsto(self):
        # A receber: o título de R$ 100,00 da Base vence em 10 dias. A pagar: R$ 30,00 vencida e R$ 1.200,00 em 10 dias.
        self.conta("30.00", dias=-2)
        self.conta(dias=10)
        self.sistema.agendador.executar_uma_vez()
        painel = self.navegador("carla@exemplo.com").get("/painel").texto
        self.assertRegex(painel, r"1 vencida\(s\), R\$ 30,00")
        self.assertRegex(painel, r"1 a vencer em 15 dias, R\$ 1\.200,00")
        self.assertRegex(painel, r"Saldo previsto em 15 dias.{0,80}-R\$ 1\.130,00")
        self.assertIn('<a href="/titulos">A receber</a>', painel)
        self.assertIn('<a href="/contas-a-pagar">A pagar</a>', painel)

    def test_menu_mostra_contas_e_fornecedores_a_quem_consulta(self):
        for email in ("carla@exemplo.com", "diego@exemplo.com", "helena@exemplo.com", "admin@exemplo.com"):
            with self.subTest(email=email):
                painel = self.navegador(email).get("/painel").texto
                self.assertIn('href="/contas-a-pagar"', painel)
                self.assertIn('href="/fornecedores"', painel)

    def test_auditoria_descreve_fornecedor_e_conta(self):
        conta = self.conta()
        pagina = self.navegador("carla@exemplo.com").get("/auditoria").texto
        self.assertIn(f'href="/contas-a-pagar/{conta.id}"', pagina)
        self.assertIn(f'href="/fornecedores/{self.pneus.id}"', pagina)


class PermissoesSemOCliente(Base):
    def test_CA_16_OPEN_57_matriz_e_formularios_sem_o_perfil_cliente(self):
        admin = self.navegador("admin@exemplo.com")
        for caminho in ("/permissoes", "/usuarios/novo"):
            with self.subTest(caminho=caminho):
                texto = admin.get(caminho).texto
                self.assertNotIn(">Cliente<", texto)
                self.assertIn(">Contador<", texto)
        self.assertNotIn(">Cliente<", ClienteWeb(self.sistema.web).get("/criar-conta").texto)
        self.assertIn("Cadastrar conta a pagar", admin.get("/permissoes").texto)


if __name__ == "__main__":
    unittest.main()


class DemonstracaoComContasAPagar(unittest.TestCase):
    def test_demonstracao_tem_fornecedores_e_contas_em_todos_os_estados(self):
        import tempfile
        from pathlib import Path

        from remindme.demonstracao import preparar_demonstracao
        from remindme.inicializacao import montar
        from remindme.infraestrutura.memoria import RegistroErrosEmMemoria, RelogioFixo
        from tests.apoio import CIFRADOR_DE_TESTE
        from tests.apresentacao.test_spec_017_web import AGORA

        with tempfile.TemporaryDirectory() as pasta:
            sistema = montar(str(Path(pasta).joinpath("demo.db")), RelogioFixo(AGORA), CIFRADOR_DE_TESTE, RegistroErrosEmMemoria())
            preparar_demonstracao(sistema, SENHA)
            with sistema.uow as uow:
                contas = uow.contas_pagar.listar()
                self.assertEqual(len(uow.fornecedores.listar()), 3)
        self.assertEqual({c.estado for c in contas}, set(EstadoContaPagar))
        self.assertTrue(any(c.estado is EstadoContaPagar.ABERTA and c.pagamentos for c in contas), "pagamento parcial")
        self.assertTrue(any(p.estornado for c in contas for p in c.pagamentos), "estorno")
