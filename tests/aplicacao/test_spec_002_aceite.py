"""Critérios de aceitação da Spec 002: autenticação e autorização por perfil, sem interface (RNF-03)."""

import ast
import unittest
from datetime import date, datetime, timedelta
from decimal import Decimal

from remindme.aplicacao.acesso import DURACAO_DA_SESSAO, Autorizacao, SessaoInvalida
from remindme.aplicacao.servico_acesso import CREDENCIAIS_INVALIDAS, ServicoAcesso
from remindme.aplicacao.servico_titulos import ServicoTitulos
from remindme.dominio.erros import OperacaoNegada, OperacaoRecusada
from remindme.dominio.operacoes import Operacao
from remindme.dominio.usuario import Perfil
from remindme.infraestrutura.memoria import (
    ClientesEmMemoria,
    RelogioFixo,
    UnidadeDeTrabalhoEmMemoria,
)
from tests.apoio import CIFRADOR_DE_TESTE
from tests.arquitetura.test_camadas import RAIZ

HOJE = date(2026, 10, 3)
FUTURO = HOJE + timedelta(days=30)
SENHA = "senha-provisoria"


class Base(unittest.TestCase):
    def setUp(self):
        self.uow = UnidadeDeTrabalhoEmMemoria()
        self.relogio = RelogioFixo(datetime(2026, 10, 3, 10, 0))
        self.acesso = ServicoAcesso(self.uow, self.relogio, cifrador=CIFRADOR_DE_TESTE)
        self.titulos = ServicoTitulos(self.uow, ClientesEmMemoria({"c1"}), self.relogio)
        self.acesso.criar_primeiro_administrador("Ana Admin", "admin@exemplo.com", SENHA)
        self.admin = self.acesso.entrar("admin@exemplo.com", SENHA).identificador

    def cadastrar(self, nome, email, perfil, senha=SENHA):
        return self.acesso.cadastrar_usuario(self.admin, nome, email, perfil, senha)

    def entrar(self, email, senha=SENHA):
        return self.acesso.entrar(email, senha).identificador

    def usuario_e_sessao(self, perfil, email):
        usuario = self.cadastrar(perfil.value, email, perfil)
        return usuario, self.entrar(email)

    def fotografia(self):
        return (
            dict(self.uow.usuarios.dados),
            dict(self.uow.titulos.dados),
            self.uow.permissoes.obter(),
            self.uow.auditoria.registros,
        )


class Spec002(Base):
    def test_CA_01_administrador_cadastra_usuario_ativo_com_um_perfil_e_auditado_sem_senha(self):
        usuario = self.cadastrar("Diego Ramos", "diego@exemplo.com", Perfil.OPERADOR_FINANCEIRO)
        salvo = self.uow.usuarios.obter(usuario.id)
        self.assertTrue(salvo.ativo)
        self.assertIs(salvo.perfil, Perfil.OPERADOR_FINANCEIRO)
        registros = [r for r in self.uow.auditoria.registros if r.registro_afetado == f"usuario {usuario.id}"]
        self.assertEqual(
            {(r.campo, r.valor_novo) for r in registros},
            {("nome", "Diego Ramos"), ("email", "diego@exemplo.com"), ("perfil", "Operador Financeiro"), ("ativo", "sim")},
        )
        self.assertTrue(all(r.operacao == "cadastrar usuário" for r in registros))
        for r in self.uow.auditoria.registros:
            self.assertNotIn(SENHA, f"{r.valor_anterior} {r.valor_novo} {r.motivo}")

    def test_CA_02_RNF_14_email_ja_cadastrado_e_recusado_com_o_campo(self):
        self.cadastrar("Diego", "diego@exemplo.com", Perfil.OPERADOR_FINANCEIRO)
        antes = self.fotografia()
        with self.assertRaises(OperacaoRecusada) as ctx:
            self.cadastrar("Outro Diego", " Diego@Exemplo.com ", Perfil.CONTADOR)
        self.assertIn("email", ctx.exception.campos)
        self.assertIn("Já existe", ctx.exception.campos["email"])
        self.assertEqual(self.fotografia(), antes)

    def test_CA_03_RNF_14_cadastro_sem_perfil_e_sem_email_indica_os_dois_campos(self):
        antes = self.fotografia()
        with self.assertRaises(OperacaoRecusada) as ctx:
            self.acesso.cadastrar_usuario(self.admin, "Sem Dados", "", None, SENHA)
        self.assertEqual(set(ctx.exception.campos), {"email", "perfil"})
        self.assertEqual(self.fotografia(), antes)

    def test_CA_04_RNF_02_operador_financeiro_nao_cadastra_usuario(self):
        _, operador = self.usuario_e_sessao(Perfil.OPERADOR_FINANCEIRO, "diego@exemplo.com")
        antes = self.fotografia()
        with self.assertRaises(OperacaoNegada):
            self.acesso.cadastrar_usuario(operador, "Intruso", "intruso@exemplo.com", Perfil.DONO, SENHA)
        self.assertEqual(self.fotografia(), antes)

    def test_CA_05_RNF_04_senhas_iguais_geram_hashes_scrypt_diferentes_e_nada_guarda_a_senha(self):
        a = self.cadastrar("A", "a@exemplo.com", Perfil.CONTADOR)
        b = self.cadastrar("B", "b@exemplo.com", Perfil.CONTADOR)
        hash_a, hash_b = self.uow.usuarios.hash_de(a.id), self.uow.usuarios.hash_de(b.id)
        self.assertTrue(hash_a.startswith("scrypt$") and hash_b.startswith("scrypt$"))
        self.assertNotEqual(hash_a, hash_b)
        self.assertNotEqual(hash_a.split("$")[4], hash_b.split("$")[4])
        armazenado = repr(self.uow.usuarios.dados) + repr(self.uow.usuarios.hashes) + repr(self.uow.auditoria.registros)
        self.assertNotIn(SENHA, armazenado)

    def test_CA_06_RF_65_login_do_contador_devolve_exatamente_as_operacoes_do_perfil(self):
        self.cadastrar("Helena Prado", "helena@exemplo.com", Perfil.CONTADOR)
        aberta = self.acesso.entrar("helena@exemplo.com", SENHA)
        self.assertTrue(aberta.identificador)
        self.assertEqual(
            aberta.operacoes,
            {
                Operacao.CONSULTAR_TITULOS,
                Operacao.CONSULTAR_CLIENTES,
                Operacao.APURAR_RESULTADO,
                Operacao.CONSULTAR_AUDITORIA,
                Operacao.EXPORTAR_CSV,
                Operacao.CONSULTAR_FORNECEDORES,  # Spec 018
                Operacao.CONSULTAR_CONTAS_PAGAR,
            },
        )

    def test_CA_07_RF_66_email_inexistente_e_senha_errada_tem_a_mesma_mensagem_e_nao_criam_sessao(self):
        self.cadastrar("Diego", "diego@exemplo.com", Perfil.OPERADOR_FINANCEIRO)
        sessoes = dict(self.uow.sessoes.dados)
        mensagens = set()
        for email, senha in (("ninguem@exemplo.com", SENHA), ("diego@exemplo.com", "senha-errada")):
            with self.subTest(email=email), self.assertRaises(OperacaoRecusada) as ctx:
                self.acesso.entrar(email, senha)
            mensagens.add(ctx.exception.motivo)
        self.assertEqual(mensagens, {CREDENCIAIS_INVALIDAS})
        self.assertEqual(self.uow.sessoes.dados, sessoes)

    def test_CA_08_usuario_inativo_com_senha_certa_e_orientado_a_procurar_o_administrador(self):
        usuario = self.cadastrar("Diego", "diego@exemplo.com", Perfil.OPERADOR_FINANCEIRO)
        self.acesso.inativar_usuario(self.admin, usuario.id)
        sessoes = dict(self.uow.sessoes.dados)
        with self.assertRaisesRegex(OperacaoRecusada, "Procure o Administrador"):
            self.acesso.entrar("diego@exemplo.com", SENHA)
        self.assertEqual(self.uow.sessoes.dados, sessoes)
        with self.assertRaises(OperacaoRecusada) as ctx:
            self.acesso.entrar("diego@exemplo.com", "senha-errada")
        self.assertEqual(ctx.exception.motivo, CREDENCIAIS_INVALIDAS)

    def test_CA_09_RNF_01_sem_sessao_ou_com_sessao_desconhecida_a_operacao_e_recusada(self):
        antes = self.fotografia()
        for sessao in (None, "", "sessao-que-nao-existe"):
            with self.subTest(sessao=sessao), self.assertRaises(SessaoInvalida):
                self.titulos.cadastrar_titulo(sessao, "c1", Decimal("100.00"), FUTURO)
        self.assertEqual(self.fotografia(), antes)

    def test_CA_10_RB_03_contador_nao_cadastra_titulo_nem_registra_pagamento(self):
        _, dono = self.usuario_e_sessao(Perfil.DONO, "carla@exemplo.com")
        _, contador = self.usuario_e_sessao(Perfil.CONTADOR, "helena@exemplo.com")
        titulo = self.titulos.cadastrar_titulo(dono, "c1", Decimal("100.00"), FUTURO)
        antes = self.fotografia()
        for operacao in (
            lambda: self.titulos.cadastrar_titulo(contador, "c1", Decimal("100.00"), FUTURO),
            lambda: self.titulos.registrar_pagamento(contador, titulo.id, Decimal("10.00"), HOJE),
        ):
            with self.assertRaisesRegex(OperacaoNegada, "RB-03"):
                operacao()
        self.assertEqual(self.fotografia(), antes)

    def test_CA_11_RNF_02_operacao_fora_da_matriz_e_negada(self):
        _, operador = self.usuario_e_sessao(Perfil.OPERADOR_FINANCEIRO, "diego@exemplo.com")
        with self.assertRaises(OperacaoNegada):
            self.acesso.listar_usuarios(operador)
        with self.uow as uow, self.assertRaises(OperacaoNegada):
            Autorizacao(self.relogio).exigir(uow, operador, Operacao.CONFIGURAR_REGRAS)

    def test_CA_12_RF_03_permissao_retirada_vale_na_operacao_seguinte_sem_novo_login(self):
        _, operador = self.usuario_e_sessao(Perfil.OPERADOR_FINANCEIRO, "diego@exemplo.com")
        self.titulos.cadastrar_titulo(operador, "c1", Decimal("100.00"), FUTURO)
        self.acesso.retirar_permissao(self.admin, Perfil.OPERADOR_FINANCEIRO, Operacao.CADASTRAR_TITULO)
        with self.assertRaises(OperacaoNegada):
            self.titulos.cadastrar_titulo(operador, "c1", Decimal("100.00"), FUTURO)
        self.acesso.conceder_permissao(self.admin, Perfil.OPERADOR_FINANCEIRO, Operacao.CADASTRAR_TITULO)
        self.titulos.cadastrar_titulo(operador, "c1", Decimal("100.00"), FUTURO)

    def test_CA_13_INV_4_permissao_fixada_por_regra_nao_muda(self):
        antes = self.uow.permissoes.obter()
        for perfil, operacao, regra in (
            (Perfil.OPERADOR_FINANCEIRO, Operacao.ESTORNAR_PAGAMENTO, "RB-02"),
            (Perfil.CONTADOR, Operacao.REGISTRAR_PAGAMENTO, "RB-03"),
        ):
            with self.subTest(perfil=perfil.value), self.assertRaisesRegex(OperacaoRecusada, regra):
                self.acesso.conceder_permissao(self.admin, perfil, operacao)
        with self.assertRaisesRegex(OperacaoRecusada, "RB-02"):
            self.acesso.retirar_permissao(self.admin, Perfil.DONO, Operacao.ESTORNAR_PAGAMENTO)
        self.assertEqual(self.uow.permissoes.obter(), antes)

    def test_CA_14_usuario_inativado_perde_a_sessao_e_o_historico_fica(self):
        operador_usuario, operador = self.usuario_e_sessao(Perfil.OPERADOR_FINANCEIRO, "diego@exemplo.com")
        self.titulos.cadastrar_titulo(operador, "c1", Decimal("100.00"), FUTURO)
        feitos = [r for r in self.uow.auditoria.registros if r.usuario_id == operador_usuario.id]
        self.acesso.inativar_usuario(self.admin, operador_usuario.id)
        with self.assertRaises(SessaoInvalida):
            self.titulos.cadastrar_titulo(operador, "c1", Decimal("100.00"), FUTURO)
        self.assertEqual([r for r in self.uow.auditoria.registros if r.usuario_id == operador_usuario.id], feitos)

    def test_CA_15_RF_05_mudanca_de_perfil_vale_na_operacao_seguinte_e_e_auditada(self):
        usuario, sessao = self.usuario_e_sessao(Perfil.OPERADOR_FINANCEIRO, "diego@exemplo.com")
        self.titulos.cadastrar_titulo(sessao, "c1", Decimal("100.00"), FUTURO)
        self.acesso.alterar_perfil(self.admin, usuario.id, Perfil.CONTADOR)
        with self.assertRaisesRegex(OperacaoNegada, "RB-03"):
            self.titulos.cadastrar_titulo(sessao, "c1", Decimal("100.00"), FUTURO)
        registro = self.uow.auditoria.registros[-1]
        self.assertEqual(
            (registro.campo, registro.valor_anterior, registro.valor_novo),
            ("perfil", "Operador Financeiro", "Contador"),
        )

    def test_CA_16_RNF_03_RB_02_operador_chamando_o_estorno_direto_no_servico_e_negado(self):
        _, dono = self.usuario_e_sessao(Perfil.DONO, "carla@exemplo.com")
        _, operador = self.usuario_e_sessao(Perfil.OPERADOR_FINANCEIRO, "diego@exemplo.com")
        titulo = self.titulos.cadastrar_titulo(dono, "c1", Decimal("100.00"), FUTURO)
        titulo = self.titulos.registrar_pagamento(dono, titulo.id, Decimal("100.00"), HOJE)
        with self.assertRaisesRegex(OperacaoNegada, "RB-02"):
            self.titulos.estornar_pagamento(operador, titulo.id, titulo.pagamentos[0].id, "erro", HOJE)
        self.assertFalse(self.uow.titulos.obter(titulo.id).pagamentos[0].estornado)


class DecisoesDaSpec002(Base):
    def test_INV_6_dois_usuarios_nao_tem_o_mesmo_email(self):
        self.cadastrar("A", "a@exemplo.com", Perfil.CONTADOR)
        with self.assertRaises(OperacaoRecusada):
            self.cadastrar("B", "A@EXEMPLO.COM", Perfil.DONO)
        self.assertEqual(sum(u.email == "a@exemplo.com" for u in self.uow.usuarios.listar()), 1)

    def test_OPEN_39_primeiro_administrador_so_quando_nao_ha_administrador_ativo(self):
        with self.assertRaisesRegex(OperacaoRecusada, "Já existe um Administrador"):
            self.acesso.criar_primeiro_administrador("Outro", "outro@exemplo.com", SENHA)
        registro = next(r for r in self.uow.auditoria.registros if r.campo == "perfil")
        self.assertTrue(registro.automatica)
        self.assertEqual(registro.rotina, "instalação")

    def test_OPEN_44_senha_com_menos_de_8_caracteres_e_recusada_no_campo(self):
        with self.assertRaises(OperacaoRecusada) as ctx:
            self.cadastrar("Diego", "diego@exemplo.com", Perfil.OPERADOR_FINANCEIRO, senha="1234567")
        self.assertEqual(set(ctx.exception.campos), {"senha"})

    def test_OPEN_45_ultimo_administrador_ativo_nao_e_inativado_nem_rebaixado(self):
        admin = next(u for u in self.uow.usuarios.listar() if u.perfil is Perfil.ADMINISTRADOR)
        with self.assertRaisesRegex(OperacaoRecusada, "OPEN-45"):
            self.acesso.inativar_usuario(self.admin, admin.id)
        with self.assertRaisesRegex(OperacaoRecusada, "OPEN-45"):
            self.acesso.alterar_perfil(self.admin, admin.id, Perfil.DONO)
        with self.assertRaisesRegex(OperacaoRecusada, "OPEN-53"):
            self.acesso.retirar_permissao(self.admin, Perfil.ADMINISTRADOR, Operacao.ADMINISTRAR_USUARIOS)
        segundo = self.cadastrar("Bruno Admin", "bruno@exemplo.com", Perfil.ADMINISTRADOR)
        self.acesso.inativar_usuario(self.admin, segundo.id)
        self.assertTrue(self.uow.usuarios.obter(admin.id).ativo)

    def test_OPEN_57_o_cliente_nao_e_perfil_e_nao_e_cadastrado_como_usuario(self):
        with self.assertRaises(OperacaoRecusada) as ctx:
            self.cadastrar("Sérgio Tavares", "sergio@exemplo.com", "Cliente")
        self.assertEqual(set(ctx.exception.campos), {"perfil"})

    def test_OPEN_47_entrar_e_sair_sao_auditados_sem_senha_nem_sessao(self):
        usuario, sessao = self.usuario_e_sessao(Perfil.CONTADOR, "helena@exemplo.com")
        self.acesso.sair(sessao)
        registros = [r for r in self.uow.auditoria.registros if r.campo == "sessão" and r.usuario_id == usuario.id]
        self.assertEqual(
            [(r.operacao, r.valor_anterior, r.valor_novo) for r in registros],
            [("entrar no sistema", None, "aberta"), ("sair do sistema", "aberta", "encerrada")],
        )
        texto = repr(self.uow.auditoria.registros)
        self.assertNotIn(SENHA, texto)
        self.assertNotIn(sessao, texto)

    def test_sair_encerra_a_sessao(self):
        _, sessao = self.usuario_e_sessao(Perfil.CONTADOR, "helena@exemplo.com")
        self.acesso.sair(sessao)
        with self.assertRaises(SessaoInvalida):
            self.acesso.sessao_ativa(sessao)

    def test_OPEN_43_sessao_vale_8_horas(self):
        _, sessao = self.usuario_e_sessao(Perfil.CONTADOR, "helena@exemplo.com")
        self.relogio.momento += DURACAO_DA_SESSAO - timedelta(seconds=1)
        self.acesso.sessao_ativa(sessao)
        self.relogio.momento += timedelta(seconds=1)
        with self.assertRaises(SessaoInvalida):
            self.acesso.sessao_ativa(sessao)

    def test_o_identificador_da_sessao_nao_fica_no_armazenamento(self):
        _, sessao = self.usuario_e_sessao(Perfil.CONTADOR, "helena@exemplo.com")
        self.assertNotIn(sessao, repr(self.uow.sessoes.dados))


class PontoUnicoDeAutorizacao(unittest.TestCase):
    def test_INV_5_somente_a_execucao_chama_a_autorizacao(self):
        for arquivo in RAIZ.rglob("*.py"):
            chamadas = [
                no for no in ast.walk(ast.parse(arquivo.read_text(encoding="utf-8")))
                if isinstance(no, ast.Call) and getattr(no.func, "attr", None) == "exigir"
                and getattr(getattr(no.func, "value", None), "attr", None) == "_autorizacao"
            ]
            with self.subTest(arquivo=arquivo.name):
                self.assertEqual(len(chamadas), 1 if arquivo.name == "execucao.py" else 0)


if __name__ == "__main__":
    unittest.main()
