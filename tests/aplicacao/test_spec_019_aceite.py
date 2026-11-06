"""Critérios de aceitação da Spec 019: troca da própria senha, sem interface (RF-95, RF-96)."""

import inspect
import unittest
from datetime import datetime

from remindme.aplicacao.acesso import DURACAO_DA_SESSAO, SessaoInvalida
from remindme.aplicacao.servico_acesso import CREDENCIAIS_INVALIDAS, ServicoAcesso
from remindme.dominio.erros import OperacaoRecusada
from remindme.dominio.usuario import Perfil
from remindme.infraestrutura.memoria import RelogioFixo, UnidadeDeTrabalhoEmMemoria
from tests.apoio import CIFRADOR_DE_TESTE

ANTIGA = "senha-antiga-1"
NOVA = "senha-nova-123"


class Base(unittest.TestCase):
    def setUp(self):
        self.uow = UnidadeDeTrabalhoEmMemoria()
        self.relogio = RelogioFixo(datetime(2026, 11, 6, 10, 0))
        self.acesso = ServicoAcesso(self.uow, self.relogio, cifrador=CIFRADOR_DE_TESTE)
        self.acesso.criar_primeiro_administrador("Ana Admin", "admin@exemplo.com", "senha-admin-1")
        self.admin = self.acesso.entrar("admin@exemplo.com", "senha-admin-1").identificador
        self.diego = self.acesso.cadastrar_usuario(
            self.admin, "Diego Ramos", "diego@exemplo.com", Perfil.OPERADOR_FINANCEIRO, ANTIGA
        )

    def entrar(self, email="diego@exemplo.com", senha=ANTIGA):
        return self.acesso.entrar(email, senha).identificador

    def hash_do_diego(self):
        return self.uow.usuarios.hash_de(self.diego.id)

    def recusa(self, sessao, atual, nova, confirmacao):
        with self.assertRaises(OperacaoRecusada) as ctx:
            self.acesso.trocar_senha(sessao, atual, nova, confirmacao)
        return ctx.exception.campos


class Spec019(Base):
    def test_CA_01_troca_aceita_e_so_a_nova_entra(self):
        sessao = self.entrar()
        self.assertIsNone(self.acesso.trocar_senha(sessao, ANTIGA, NOVA, NOVA))
        self.assertTrue(self.entrar(senha=NOVA))
        with self.assertRaises(OperacaoRecusada) as ctx:
            self.entrar(senha=ANTIGA)
        self.assertEqual(str(ctx.exception), CREDENCIAIS_INVALIDAS)

    def test_CA_02_senha_atual_errada_nao_muda_nada(self):
        a, b = self.entrar(), self.entrar()
        antes = self.hash_do_diego()
        campos = self.recusa(a, "errada-123456", NOVA, NOVA)
        self.assertEqual(campos, {"senha_atual": "A senha atual não confere."})
        self.assertEqual(self.hash_do_diego(), antes)
        self.assertTrue(self.entrar())
        self.acesso.sessao_ativa(a)
        self.acesso.sessao_ativa(b)

    def test_CA_03_nova_senha_com_7_ou_257_caracteres(self):
        sessao = self.entrar()
        casos = {"a" * 7: "A senha deve ter pelo menos 8 caracteres.", "a" * 257: "A senha deve ter no máximo 256 caracteres."}
        for nova, mensagem in casos.items():
            with self.subTest(tamanho=len(nova)):
                self.assertEqual(self.recusa(sessao, ANTIGA, nova, nova), {"nova_senha": mensagem})
        self.assertTrue(self.entrar())

    def test_CA_04_confirmacao_diferente(self):
        sessao = self.entrar()
        campos = self.recusa(sessao, ANTIGA, NOVA, NOVA + "x")
        self.assertEqual(campos, {"confirmacao": "A confirmação não é igual à nova senha."})
        self.assertTrue(self.entrar())

    def test_CA_05_nova_igual_a_atual(self):
        sessao = self.entrar()
        campos = self.recusa(sessao, ANTIGA, ANTIGA, ANTIGA)
        self.assertEqual(campos, {"nova_senha": "A nova senha deve ser diferente da atual."})

    def test_CA_06_tres_campos_vazios_indicados_de_uma_vez(self):
        sessao = self.entrar()
        campos = self.recusa(sessao, "", "", "")
        self.assertEqual(set(campos), {"senha_atual", "nova_senha", "confirmacao"})
        self.assertEqual(campos["senha_atual"], "Informe a senha atual.")
        self.assertEqual(campos["nova_senha"], "Informe a nova senha.")
        self.assertEqual(campos["confirmacao"], "Repita a nova senha.")

    def test_CA_07_outras_sessoes_sao_encerradas(self):
        a, b, c = self.entrar(), self.entrar(), self.entrar()
        self.acesso.trocar_senha(a, ANTIGA, NOVA, NOVA)
        self.acesso.sessao_ativa(a)
        for outra in (b, c):
            with self.assertRaises(SessaoInvalida):
                self.acesso.sessao_ativa(outra)

    def test_CA_08_sessoes_de_outro_usuario_continuam(self):
        sessao = self.entrar()
        self.acesso.trocar_senha(sessao, ANTIGA, NOVA, NOVA)
        self.acesso.sessao_ativa(self.admin)

    def test_CA_09_sem_sessao_valida_e_recusada(self):
        antes = self.hash_do_diego()
        vencida = self.entrar()
        self.relogio.momento = self.relogio.momento + DURACAO_DA_SESSAO
        inativada = self.entrar()
        usuario = self.uow.usuarios.obter(self.diego.id)
        self.uow.usuarios.salvar(usuario.inativado())
        for caso, sessao in {"nula": None, "desconhecida": "desconhecida", "vencida": vencida, "usuario inativado": inativada}.items():
            with self.subTest(caso=caso), self.assertRaises(SessaoInvalida):
                self.acesso.trocar_senha(sessao, ANTIGA, NOVA, NOVA)
        self.assertEqual(self.hash_do_diego(), antes)

    def test_CA_10_hash_e_salt_novos_e_auditoria_sem_senha(self):
        sessao = self.entrar()
        antes = self.hash_do_diego()
        self.acesso.trocar_senha(sessao, ANTIGA, NOVA, NOVA)
        depois = self.hash_do_diego()
        self.assertTrue(depois.startswith("scrypt$"))
        self.assertNotEqual(depois.split("$")[4], antes.split("$")[4])
        registros = [r for r in self.uow.auditoria.registros if r.campo == "senha" and r.operacao == "trocar senha"]
        self.assertEqual(len(registros), 1)
        registro = registros[0]
        self.assertEqual(registro.registro_afetado, f"usuario {self.diego.id}")
        self.assertEqual(registro.usuario_id, self.diego.id)
        self.assertIsNone(registro.valor_anterior)
        self.assertEqual(registro.valor_novo, "alterada")
        for r in self.uow.auditoria.registros:
            texto = f"{r.valor_anterior} {r.valor_novo} {r.motivo} {r.registro_afetado}"
            self.assertFalse(ANTIGA in texto and NOVA in texto)
            self.assertNotIn(NOVA, texto)

    def test_CA_11_falha_na_auditoria_desfaz_tudo(self):
        a, b = self.entrar(), self.entrar()
        antes = self.hash_do_diego()
        self.uow.auditoria.falhar = True
        with self.assertRaises(RuntimeError):
            self.acesso.trocar_senha(a, ANTIGA, NOVA, NOVA)
        self.uow.auditoria.falhar = False
        self.assertEqual(self.hash_do_diego(), antes)
        self.assertTrue(self.entrar())
        self.acesso.sessao_ativa(b)

    def test_CA_12_todos_os_perfis_trocam_sem_permissao_da_matriz(self):
        for perfil in Perfil:
            email = f"{perfil.name.lower()}@exemplo.com"
            with self.subTest(perfil=perfil.value):
                self.acesso.cadastrar_usuario(self.admin, perfil.value, email, perfil, ANTIGA)
                sessao = self.entrar(email)
                self.acesso.trocar_senha(sessao, ANTIGA, NOVA, NOVA)
                self.assertTrue(self.entrar(email, NOVA))

    def test_CA_12_contador_sem_nenhuma_permissao_da_matriz_troca_a_senha(self):
        self.acesso.cadastrar_usuario(self.admin, "Carla", "carla@exemplo.com", Perfil.CONTADOR, ANTIGA)
        for linha in self.acesso.matriz(self.admin):
            celula = linha.celulas[Perfil.CONTADOR]
            if celula.permitido and celula.fixada is None:
                self.acesso.retirar_permissao(self.admin, Perfil.CONTADOR, linha.operacao)
        sessao = self.entrar("carla@exemplo.com")
        self.acesso.trocar_senha(sessao, ANTIGA, NOVA, NOVA)
        self.assertTrue(self.entrar("carla@exemplo.com", NOVA))

    def test_INV_5_trocar_senha_nao_recebe_usuario(self):
        parametros = list(inspect.signature(ServicoAcesso.trocar_senha).parameters)
        self.assertEqual(parametros, ["self", "sessao", "senha_atual", "nova_senha", "confirmacao"])


if __name__ == "__main__":
    unittest.main()
