"""Persistência em SQLite (Spec 017, ADR-007): contrato dos repositórios, transação real e auditoria imutável."""

import sqlite3
import tempfile
import unittest
from dataclasses import replace
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path

from remindme.aplicacao.acesso import nova_sessao
from remindme.aplicacao.servico_acesso import ServicoAcesso
from remindme.aplicacao.servico_clientes import ServicoClientes
from remindme.aplicacao.servico_titulos import ServicoTitulos
from remindme.dominio.auditoria import RegistroAuditoria
from remindme.dominio.cliente import Cliente
from remindme.dominio.operacoes import Operacao
from remindme.dominio.permissoes import MatrizPermissoes
from remindme.dominio.titulo import EstadoTitulo, Titulo
from remindme.dominio.usuario import Perfil, Usuario
from remindme.infraestrutura.memoria import RelogioFixo
from remindme.infraestrutura.sqlite import (
    MIGRACOES,
    RepositorioTitulosSQLite,
    UnidadeDeTrabalhoSQLite,
    _comandos,
    preparar_banco,
)
from tests.apoio import CIFRADOR_DE_TESTE
from tests.integracao.test_integracao import ContratoRepositorioTitulos

HOJE = date(2026, 10, 3)
SENHA = "senha-de-teste"


class ComBanco(unittest.TestCase):
    def setUp(self):
        self._pasta = tempfile.TemporaryDirectory()
        self.caminho = str(Path(self._pasta.name) / "remindme.db")
        preparar_banco(self.caminho)
        self.uow = UnidadeDeTrabalhoSQLite(self.caminho)
        with self.uow as uow:
            uow.clientes.salvar(Cliente("c1", "Cliente Um", "52998224725", "a@b.com"))

    def tearDown(self):
        self._pasta.cleanup()

    def sql(self, comando, parametros=()):
        conexao = sqlite3.connect(self.caminho)
        try:
            resultado = conexao.execute(comando, parametros).fetchall()
            conexao.commit()
            return resultado
        finally:
            conexao.close()


class _RepositorioEmTransacao:
    """Cada chamada roda na sua própria transação, como o contrato espera de um repositório."""

    def __init__(self, uow):
        self._uow = uow

    def __getattr__(self, nome):
        def chamar(*argumentos):
            with self._uow as uow:
                return getattr(uow.titulos, nome)(*argumentos)

        return chamar


class RepositorioSQLiteCumpreOContrato(ContratoRepositorioTitulos, ComBanco):
    def criar_repositorio(self):
        return _RepositorioEmTransacao(self.uow)


class Esquema(ComBanco):
    def test_ADR_007_migracao_e_idempotente_e_numerada(self):
        preparar_banco(self.caminho)
        self.assertEqual(self.sql("PRAGMA user_version"), [(len(MIGRACOES),)])

    def test_ADR_007_banco_da_versao_1_e_atualizado_sem_perder_dados(self):
        """Um banco criado antes da Spec 004 (por exemplo, uma demonstração) ganha as tabelas de orçamento."""
        antigo = str(Path(self._pasta.name) / "antigo.db")
        conexao = sqlite3.connect(antigo, isolation_level=None)
        try:
            for comando in _comandos(MIGRACOES[0]):
                conexao.execute(comando)
            conexao.execute("INSERT INTO clientes VALUES ('c9', 'Cliente Antigo', '52998224725', 'a@b.com')")
            conexao.execute("PRAGMA user_version = 1")
        finally:
            conexao.close()
        preparar_banco(antigo)
        with UnidadeDeTrabalhoSQLite(antigo) as uow:
            self.assertEqual(uow.clientes.obter("c9").nome, "Cliente Antigo")
            self.assertEqual(uow.orcamentos.listar(), [])

    def test_OPEN_32_a_matriz_inicial_e_gravada_na_criacao(self):
        with self.uow as uow:
            self.assertEqual(uow.permissoes.obter(), MatrizPermissoes.inicial())

    def test_acesso_fora_da_unidade_de_trabalho_e_um_erro(self):
        with self.assertRaises(RuntimeError):
            self.uow.titulos.listar()


class UnidadeDeTrabalho(ComBanco):
    def test_RNF_09_falha_no_bloco_desfaz_tudo(self):
        with self.assertRaises(ValueError):
            with self.uow as uow:
                uow.titulos.salvar(Titulo.cadastrar_manual("t1", "c1", Decimal("10.00"), HOJE))
                raise ValueError("falha")
        with self.uow as uow:
            self.assertIsNone(uow.titulos.obter("t1"))

    def test_bloco_aninhado_participa_da_mesma_transacao(self):
        with self.assertRaises(ValueError):
            with self.uow as uow:
                with uow:
                    uow.titulos.salvar(Titulo.cadastrar_manual("t1", "c1", Decimal("10.00"), HOJE))
                raise ValueError("falha depois do bloco interno")
        with self.uow as uow:
            self.assertIsNone(uow.titulos.obter("t1"))

    def test_restricoes_do_banco(self):
        with self.assertRaises(sqlite3.IntegrityError):
            with self.uow as uow:
                uow.clientes.salvar(Cliente("c2", "Outro", "52998224725", "x@y.com"))
        with self.assertRaises(sqlite3.IntegrityError):
            with self.uow as uow:
                uow.titulos.salvar(Titulo.cadastrar_manual("t1", "sem-cliente", Decimal("10.00"), HOJE))


class Repositorios(ComBanco):
    def test_usuario_com_hash_a_parte(self):
        with self.uow as uow:
            uow.usuarios.salvar(Usuario("u1", "Diego", Perfil.OPERADOR_FINANCEIRO, "diego@exemplo.com"))
            uow.usuarios.guardar_hash("u1", "scrypt$1$2$3$sal$resumo")
        with self.uow as uow:
            self.assertEqual(uow.usuarios.obter_por_email("diego@exemplo.com").perfil, Perfil.OPERADOR_FINANCEIRO)
            self.assertEqual(uow.usuarios.hash_de("u1"), "scrypt$1$2$3$sal$resumo")
            uow.usuarios.salvar(replace(uow.usuarios.obter("u1"), ativo=False))
        with self.uow as uow:
            self.assertFalse(uow.usuarios.obter("u1").ativo)
            self.assertEqual(uow.usuarios.hash_de("u1"), "scrypt$1$2$3$sal$resumo")

    def test_sessao_ida_e_volta(self):
        agora = datetime(2026, 10, 3, 12, 0, tzinfo=timezone.utc)
        with self.uow as uow:
            uow.usuarios.salvar(Usuario("u1", "Diego", Perfil.CONTADOR, "d@e.com"))
            _, sessao = nova_sessao("u1", agora)
            uow.sessoes.salvar(sessao)
        with self.uow as uow:
            self.assertEqual(uow.sessoes.obter(sessao.chave), sessao)
            uow.sessoes.remover_do_usuario("u1")
        with self.uow as uow:
            self.assertIsNone(uow.sessoes.obter(sessao.chave))

    def test_permissoes_alteradas_persistem(self):
        with self.uow as uow:
            uow.permissoes.salvar(uow.permissoes.obter().conceder(Perfil.OPERADOR_FINANCEIRO, Operacao.CONSULTAR_AUDITORIA))
        with self.uow as uow:
            self.assertTrue(uow.permissoes.obter().permite(Perfil.OPERADOR_FINANCEIRO, Operacao.CONSULTAR_AUDITORIA))

    def test_auditoria_em_ordem_de_gravacao_com_horario_em_utc(self):
        momento = datetime(2026, 10, 3, 12, 0, tzinfo=timezone.utc)
        with self.uow as uow:
            for n in range(3):
                uow.auditoria.registrar(RegistroAuditoria("u1", momento, f"op{n}", "titulo t1", campo="estado"))
        with self.uow as uow:
            registros = uow.auditoria.listar()
        self.assertEqual([r.operacao for r in registros], ["op0", "op1", "op2"])
        self.assertEqual(registros[0].data_hora, momento)


class Spec017Persistencia(ComBanco):
    def montar(self):
        relogio = RelogioFixo(datetime(2026, 10, 3, 12, 0, tzinfo=timezone.utc))
        uow = UnidadeDeTrabalhoSQLite(self.caminho)
        acesso = ServicoAcesso(uow, relogio, cifrador=CIFRADOR_DE_TESTE)
        return uow, acesso, ServicoClientes(uow, relogio), ServicoTitulos(uow, uow.clientes, relogio)

    def test_CA_12_dados_continuam_depois_de_montar_de_novo(self):
        _, acesso, clientes, titulos = self.montar()
        acesso.criar_primeiro_administrador("Admin", "admin@exemplo.com", SENHA)
        admin = acesso.entrar("admin@exemplo.com", SENHA).identificador
        acesso.cadastrar_usuario(admin, "Diego", "diego@exemplo.com", Perfil.OPERADOR_FINANCEIRO, SENHA)
        operador = acesso.entrar("diego@exemplo.com", SENHA).identificador
        cliente = clientes.cadastrar_cliente(operador, "Padaria", "11.222.333/0001-81", "p@padaria.com")
        titulo = titulos.cadastrar_titulo(operador, cliente.id, Decimal("100.00"), HOJE)
        titulos.registrar_pagamento(operador, titulo.id, Decimal("40.00"), HOJE)

        _, acesso, _, titulos = self.montar()
        operador = acesso.entrar("diego@exemplo.com", SENHA).identificador
        salvo = titulos.obter_titulo(operador, titulo.id)
        self.assertEqual(salvo.saldo, Decimal("60.00"))
        self.assertIs(salvo.estado, EstadoTitulo.ABERTO)

    def test_CA_13_INV_5_o_banco_recusa_alterar_e_excluir_auditoria(self):
        with self.uow as uow:
            uow.auditoria.registrar(RegistroAuditoria("u1", datetime(2026, 10, 3), "op", "titulo t1"))
        for comando in ("UPDATE auditoria SET operacao = 'adulterada'", "DELETE FROM auditoria"):
            with self.subTest(comando=comando), self.assertRaisesRegex(sqlite3.DatabaseError, "RB-30"):
                self.sql(comando)
        self.assertEqual(self.sql("SELECT operacao FROM auditoria"), [("op",)])

    def test_CA_14_INV_6_falha_do_banco_no_pagamento_nao_deixa_nada(self):
        uow, acesso, _, _ = self.montar()
        acesso.criar_primeiro_administrador("Admin", "admin@exemplo.com", SENHA)
        admin = acesso.entrar("admin@exemplo.com", SENHA).identificador
        acesso.cadastrar_usuario(admin, "Diego", "diego@exemplo.com", Perfil.OPERADOR_FINANCEIRO, SENHA)
        operador = acesso.entrar("diego@exemplo.com", SENHA).identificador
        titulos = ServicoTitulos(uow, uow.clientes, RelogioFixo(datetime(2026, 10, 3, 12, 0, tzinfo=timezone.utc)))
        titulo = titulos.cadastrar_titulo(operador, "c1", Decimal("100.00"), HOJE)
        auditoria_antes = self.sql("SELECT COUNT(*) FROM auditoria")

        class TitulosQueFalham(RepositorioTitulosSQLite):
            def salvar(self, titulo):
                super().salvar(titulo)
                raise sqlite3.OperationalError("disco cheio (simulado)")

        uow.titulos = TitulosQueFalham(uow)
        with self.assertRaises(sqlite3.OperationalError):
            titulos.registrar_pagamento(operador, titulo.id, Decimal("100.00"), HOJE)
        self.assertEqual(self.sql("SELECT COUNT(*) FROM pagamentos"), [(0,)])
        self.assertEqual(self.sql("SELECT estado FROM titulos"), [("ABERTO",)])
        self.assertEqual(self.sql("SELECT COUNT(*) FROM auditoria"), auditoria_antes)

    def test_OPEN_25_pedido_repetido_tambem_e_barrado_pelo_banco(self):
        with self.uow as uow:
            titulo = Titulo.cadastrar_manual("t1", "c1", Decimal("100.00"), HOJE)
            titulo.registrar_pagamento("p1", Decimal("10.00"), HOJE, pedido_id="pedido-1")
            uow.titulos.salvar(titulo)
        with self.assertRaises(sqlite3.IntegrityError):
            self.sql(
                "INSERT INTO pagamentos (id, titulo_id, ordem, valor, data, estornado, pedido_id) "
                "VALUES ('p2', 't1', 1, '10.00', '2026-10-03', 0, 'pedido-1')"
            )


if __name__ == "__main__":
    unittest.main()
