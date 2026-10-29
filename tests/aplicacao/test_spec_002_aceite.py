"""Critérios de aceitação da Spec 002 (autenticação e autorização por perfil)."""

import unittest
from datetime import date
from decimal import Decimal

from remindme.aplicacao.portas import FiltroAuditoria
from remindme.dominio.acesso import MATRIZ_INICIAL, Operacao
from remindme.dominio.erros import AcessoNegado, EntradaInvalida, OperacaoRecusada
from remindme.dominio.usuario import Perfil
from tests.apoio_sistema import CNPJ, SENHA, com_usuarios, novo_sistema


class Spec002(unittest.TestCase):
    def setUp(self):
        self.sistema, self.uow, self.banco = novo_sistema()
        self.t = com_usuarios(self.sistema)
        self.acesso = self.sistema.acesso
        self.cliente = self.sistema.cadastrar_cliente(self.t["operador"], nome="ACME", documento=CNPJ)

    def auditoria(self):
        return self.sistema.consultar_auditoria(self.t["admin"], FiltroAuditoria())

    def titulo(self):
        return self.sistema.cadastrar_titulo(self.t["operador"], self.cliente.id, Decimal("100.00"), date(2026, 11, 1))

    def test_CA_01_cadastro_de_usuario_auditado_sem_a_senha(self):
        usuario = self.acesso.cadastrar_usuario(self.t["admin"], "Bia", "bia@exemplo.com", "outra-senha-1", "Operador Financeiro")
        self.assertTrue(usuario.ativo)
        self.assertIs(usuario.perfil, Perfil.OPERADOR_FINANCEIRO)
        registro = next(r for r in self.auditoria() if r.registro_afetado == f"usuario {usuario.id}")
        self.assertEqual(registro.valor_novo, "Operador Financeiro")
        self.assertNotIn("outra-senha-1", repr(self.auditoria()))

    def test_CA_02_email_ja_cadastrado_e_recusado(self):
        with self.assertRaises(EntradaInvalida) as erro:
            self.acesso.cadastrar_usuario(self.t["admin"], "Outro", "DIEGO@exemplo.com", SENHA, "Contador")
        self.assertIn("e-mail", erro.exception.campos)

    def test_CA_03_campos_obrigatorios_ausentes(self):
        with self.assertRaises(EntradaInvalida) as erro:
            self.acesso.cadastrar_usuario(self.t["admin"], "Sem", "", SENHA, "")
        self.assertEqual(set(erro.exception.campos), {"e-mail", "perfil"})

    def test_CA_04_operador_nao_cadastra_usuario(self):
        antes = len(self.uow.usuarios.listar())
        with self.assertRaises(AcessoNegado):
            self.acesso.cadastrar_usuario(self.t["operador"], "X", "x@exemplo.com", SENHA, "Dono")
        self.assertEqual(len(self.uow.usuarios.listar()), antes)

    def test_CA_05_senha_guardada_so_como_hash_scrypt_com_salt_proprio(self):
        linhas = self.banco.conexao.execute(
            "SELECT * FROM usuarios WHERE email IN ('dona@exemplo.com', 'diego@exemplo.com')"
        ).fetchall()
        self.assertNotIn(SENHA, repr(linhas))
        hashes = [l[-1] for l in linhas]
        self.assertTrue(all(h.startswith("scrypt$") for h in hashes))
        self.assertNotEqual(hashes[0], hashes[1])
        self.assertNotEqual(hashes[0].split("$")[4], hashes[1].split("$")[4])

    def test_CA_06_login_devolve_exatamente_as_operacoes_do_contador(self):
        sessao = self.acesso.entrar("carla@exemplo.com", SENHA)
        self.assertEqual(sessao.operacoes, MATRIZ_INICIAL[Perfil.CONTADOR])

    def test_CA_07_mesma_mensagem_para_email_inexistente_e_senha_errada(self):
        sessoes = self.banco.conexao.execute("SELECT count(*) FROM sessoes").fetchone()[0]
        with self.assertRaises(AcessoNegado) as a:
            self.acesso.entrar("ninguem@exemplo.com", SENHA)
        with self.assertRaises(AcessoNegado) as b:
            self.acesso.entrar("diego@exemplo.com", "errada")
        self.assertEqual(a.exception.motivo, b.exception.motivo)
        self.assertEqual(self.banco.conexao.execute("SELECT count(*) FROM sessoes").fetchone()[0], sessoes)

    def test_CA_08_usuario_inativo_nao_entra(self):
        diego = self.uow.usuarios.obter_por_email("diego@exemplo.com")
        self.acesso.inativar_usuario(self.t["admin"], diego.id)
        with self.assertRaises(AcessoNegado) as erro:
            self.acesso.entrar("diego@exemplo.com", SENHA)
        self.assertIn("Administrador", erro.exception.motivo)

    def test_CA_09_sem_sessao_ou_sessao_desconhecida(self):
        for token in (None, "", "desconhecido"):
            with self.subTest(token=token), self.assertRaises(AcessoNegado):
                self.sistema.cadastrar_titulo(token, self.cliente.id, Decimal("10"), date(2026, 11, 1))
        self.assertEqual(self.uow.titulos.listar(), [])

    def test_CA_10_RB_03_contador_nao_cadastra_titulo_nem_registra_pagamento(self):
        titulo = self.titulo()
        with self.assertRaises(AcessoNegado):
            self.sistema.cadastrar_titulo(self.t["contador"], self.cliente.id, Decimal("10"), date(2026, 11, 1))
        with self.assertRaises(AcessoNegado) as erro:
            self.sistema.registrar_pagamento(self.t["contador"], titulo.id, Decimal("10"), date(2026, 10, 20))
        self.assertIn("RF-67", erro.exception.motivo)
        self.assertEqual(self.uow.titulos.obter(titulo.id).saldo, Decimal("100.00"))

    def test_CA_11_operacao_fora_da_matriz_e_negada(self):
        with self.assertRaises(AcessoNegado):
            self.sistema.consultar_auditoria(self.t["operador"], FiltroAuditoria())

    def test_CA_12_retirar_permissao_vale_na_sessao_aberta(self):
        self.acesso.alterar_permissao(self.t["admin"], Perfil.OPERADOR_FINANCEIRO, Operacao.MANTER_TITULOS, False)
        with self.assertRaises(AcessoNegado):
            self.titulo()

    def test_CA_13_permissao_fixada_nao_muda(self):
        casos = [
            (Perfil.OPERADOR_FINANCEIRO, Operacao.ESTORNAR_PAGAMENTO, True, "RB-02"),
            (Perfil.CONTADOR, Operacao.MANTER_TITULOS, True, "RB-03"),
        ]
        for perfil, operacao, permitir, regra in casos:
            with self.subTest(perfil=perfil, operacao=operacao):
                with self.assertRaises(OperacaoRecusada) as erro:
                    self.acesso.alterar_permissao(self.t["admin"], perfil, operacao, permitir)
                self.assertIn(regra, erro.exception.motivo)
                self.assertEqual(self.acesso.operacoes_permitidas(perfil), MATRIZ_INICIAL[perfil])

    def test_CA_14_inativacao_derruba_a_sessao_e_preserva_a_auditoria(self):
        self.titulo()
        diego = self.uow.usuarios.obter_por_email("diego@exemplo.com")
        self.acesso.inativar_usuario(self.t["admin"], diego.id)
        with self.assertRaises(AcessoNegado):
            self.titulo()
        self.assertTrue(any(r.usuario_id == diego.id for r in self.auditoria()))

    def test_CA_15_mudanca_de_perfil_vale_na_operacao_seguinte_e_e_auditada(self):
        diego = self.uow.usuarios.obter_por_email("diego@exemplo.com")
        self.acesso.alterar_perfil(self.t["admin"], diego.id, "Contador")
        with self.assertRaises(AcessoNegado):
            self.titulo()
        registro = next(r for r in self.auditoria() if r.operacao == "alterar perfil")
        self.assertEqual((registro.valor_anterior, registro.valor_novo), ("Operador Financeiro", "Contador"))

    def test_CA_16_RB_02_operador_nao_estorna_nem_chamando_o_servico(self):
        titulo = self.titulo()
        titulo = self.sistema.registrar_pagamento(self.t["operador"], titulo.id, Decimal("10"), date(2026, 10, 20))
        with self.assertRaises(AcessoNegado):
            self.sistema.estornar_pagamento(self.t["operador"], titulo.id, titulo.pagamentos[0].id, "erro")
        self.sistema.estornar_pagamento(self.t["dono"], titulo.id, titulo.pagamentos[0].id, "erro")

    def test_OPEN_16_somente_o_dono_cancela(self):
        titulo = self.titulo()
        with self.assertRaises(AcessoNegado):
            self.sistema.cancelar_titulo(self.t["operador"], titulo.id, "motivo")
        self.sistema.cancelar_titulo(self.t["dono"], titulo.id, "motivo")

    def test_OPEN_36_administrador_nao_se_inativa(self):
        admin = self.acesso.usuario_da_sessao(self.t["admin"])
        with self.assertRaises(OperacaoRecusada):
            self.acesso.inativar_usuario(self.t["admin"], admin.id)

    def test_logout_encerra_a_sessao(self):
        self.acesso.sair(self.t["dono"])
        with self.assertRaises(AcessoNegado):
            self.sistema.painel(self.t["dono"])

    def test_instalacao_e_operacao_automatica(self):
        registro = self.auditoria()[-1]
        self.assertTrue(registro.automatica)
        self.assertEqual(registro.rotina, "instalação")
        with self.assertRaises(OperacaoRecusada):
            self.acesso.instalar_administrador("Outro", "outro@exemplo.com", SENHA)


if __name__ == "__main__":
    unittest.main()
