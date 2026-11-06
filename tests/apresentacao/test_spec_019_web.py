"""Spec 019 pela interface web: a tela "Trocar senha" e o link no topo (RF-95, RF-96)."""

import re
import unittest

from tests.apresentacao.cliente_web import ClienteWeb
from tests.apresentacao.test_spec_017_web import SENHA, Base

NOVA = "outra-senha-segura"
EMAIL = "carla@exemplo.com"


class TrocaDeSenhaPelaInterface(Base):
    def dados(self, atual=SENHA, nova=NOVA, confirmacao=None):
        return {"senha_atual": atual, "nova_senha": nova, "confirmacao": nova if confirmacao is None else confirmacao}

    def trocar(self, navegador, **dados):
        return navegador.enviar("/trocar-senha", "/trocar-senha", self.dados(**dados))

    def entra(self, senha):
        return ClienteWeb(self.sistema.web).entrar(EMAIL, senha)

    def test_CA_13_sem_sessao_get_e_post_levam_a_entrada(self):
        anonimo = ClienteWeb(self.sistema.web)
        for resposta in (anonimo.get("/trocar-senha"), anonimo.post("/trocar-senha", self.dados())):
            self.assertEqual((resposta.status, resposta.destino), (303, "/entrar"))
        self.assertEqual(self.entra(SENHA).status, 303)
        self.assertEqual(self.entra(NOVA).status, 401)

    def test_CA_14_todos_os_perfis_veem_o_link(self):
        for email in ("carla@exemplo.com", "diego@exemplo.com", "helena@exemplo.com", "admin@exemplo.com"):
            painel = self.navegador(email).get("/painel").texto
            self.assertIn('<a class="botao discreto" href="/trocar-senha">Trocar senha</a>', painel, email)

    def test_CA_15_erros_voltam_com_400_por_campo_sem_as_senhas(self):
        carla = self.navegador(EMAIL)
        resposta = self.trocar(carla, atual="errada-123", nova="curta", confirmacao="diferente-9")
        self.assertEqual(resposta.status, 400)
        for campo in ("senha_atual", "nova_senha", "confirmacao"):
            self.assertIn(f'id="erro-{campo}"', resposta.texto)
        self.assertIn("A senha atual não confere.", resposta.texto)
        for digitada in ("errada-123", "curta", "diferente-9"):
            self.assertNotIn(digitada, resposta.texto)
        self.assertEqual(self.entra(SENHA).status, 303)

    def test_CA_16_sem_protecao_e_recusado(self):
        carla = self.navegador(EMAIL)
        self.assertEqual(carla.post("/trocar-senha", self.dados()).status, 403)
        self.assertEqual(self.entra(SENHA).status, 303)
        self.assertEqual(self.entra(NOVA).status, 401)

    def test_CA_17_troca_leva_ao_painel_e_derruba_o_outro_navegador(self):
        carla, outro = self.navegador(EMAIL), self.navegador(EMAIL)
        resposta = self.trocar(carla)
        self.assertEqual((resposta.status, resposta.destino), (303, "/painel?aviso=senha"))
        self.assertIn("Senha alterada. As outras sessões abertas com o seu usuário foram encerradas.", carla.get(resposta.destino).texto)
        derrubado = outro.get("/painel")
        self.assertEqual(derrubado.status, 303)
        self.assertTrue(derrubado.destino.startswith("/entrar?aviso=sessao-encerrada"))
        self.assertEqual(self.entra(NOVA).destino, "/painel")

    def test_senha_com_espacos_e_acentos_e_guardada_como_digitada(self):
        nova = "  pão de açúcar 🙂  "
        self.assertEqual(self.trocar(self.navegador(EMAIL), nova=nova).status, 303)
        resposta = self.entra(nova)
        self.assertEqual((resposta.status, resposta.destino), (303, "/painel"))
        self.assertEqual(self.entra(nova.strip()).status, 401)

    def test_envio_repetido_nao_derruba_a_sessao(self):
        carla = self.navegador(EMAIL)
        pagina = carla.get("/trocar-senha")
        dados = {"protecao": pagina.protecao, **self.dados()}
        self.assertEqual(carla.post("/trocar-senha", dados).status, 303)
        repetido = carla.post("/trocar-senha", dados)
        self.assertEqual(repetido.status, 400)
        self.assertIn('id="erro-senha_atual"', repetido.texto)
        self.assertEqual(carla.get("/painel").status, 200)

    def test_auditoria_mostra_a_troca_sem_a_senha(self):
        self.assertEqual(self.trocar(self.navegador(EMAIL)).status, 303)
        with self.sistema.uow as uow:
            registro = [r for r in uow.auditoria.listar() if r.campo == "senha"][-1]
        pagina = self.navegador("admin@exemplo.com").get("/auditoria?registro=" + registro.registro_afetado.replace(" ", "+")).texto
        self.assertIn("trocar senha", pagina)
        self.assertIn("alterada", pagina)
        self.assertIn("—", pagina)
        self.assertNotIn(NOVA, pagina)
        self.assertNotIn(SENHA, pagina)

    def test_campos_de_senha_orientam_o_gerenciador_de_senhas(self):
        texto = self.navegador(EMAIL).get("/trocar-senha").texto
        for campo, autocompletar in (("senha_atual", "current-password"), ("nova_senha", "new-password"), ("confirmacao", "new-password")):
            entrada = re.search(rf'<input[^>]*id="{campo}"[^>]*>', texto).group(0)
            self.assertIn('type="password"', entrada)
            self.assertIn(f'autocomplete="{autocompletar}"', entrada)
            self.assertNotRegex(entrada, r'value="[^"]')
        self.assertIn("Pelo menos 8 caracteres.", texto)
        self.assertIn(">Trocar senha</button>", texto)


if __name__ == "__main__":
    unittest.main()
