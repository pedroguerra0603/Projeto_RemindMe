"""Persistência em SQLite (Spec 017, ADR-007): contrato dos repositórios, transação real e auditoria imutável."""

import sqlite3
import tempfile
import unittest
from contextlib import closing
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


class ContasAPagarNoSQLite(ComBanco):
    """Spec 018: fornecedores e contas a pagar no banco, e a migração de um banco anterior (CA-17)."""

    def test_fornecedor_e_conta_com_pagamentos_ida_e_volta(self):
        from remindme.dominio.conta_pagar import ContaPagar, EstadoContaPagar
        from remindme.dominio.fornecedor import Fornecedor

        conta = ContaPagar.cadastrar("cp1", "f1", "20 pneus", Decimal("300.00"), HOJE, "Boleto")
        conta.registrar_pagamento("p1", Decimal("100.00"), HOJE, hoje=HOJE, pedido_id="x")
        conta.registrar_pagamento("p2", Decimal("200.00"), HOJE, hoje=HOJE)
        conta.estornar_pagamento("p1", "Erro", HOJE)
        with self.uow as uow:
            uow.fornecedores.salvar(Fornecedor("f1", "Distribuidora", "11222333000181", "v@d.example"))
            uow.contas_pagar.salvar(conta)
        with self.uow as uow:
            self.assertEqual(uow.fornecedores.obter_por_documento("11222333000181").nome, "Distribuidora")
            self.assertTrue(uow.fornecedores.existe("f1"))
            self.assertFalse(uow.fornecedores.existe("f2"))
            lida = uow.contas_pagar.obter("cp1")
            self.assertEqual(lida, conta)
            self.assertEqual((lida.estado, lida.saldo), (EstadoContaPagar.ABERTA, Decimal("100.00")))
            self.assertEqual(uow.contas_pagar.listar(), [conta])

    def test_conta_exige_fornecedor_existente_no_banco(self):
        from remindme.dominio.conta_pagar import ContaPagar

        with self.assertRaises(sqlite3.IntegrityError):
            with self.uow as uow:
                uow.contas_pagar.salvar(ContaPagar.cadastrar("cp1", "nao-existe", "x", Decimal("1.00"), HOJE))

    def test_CA_17_banco_antigo_ganha_tabelas_e_permissoes(self):
        antigo = str(Path(self._pasta.name) / "versao3.db")
        conexao = sqlite3.connect(antigo, isolation_level=None)
        try:
            for script in MIGRACOES[:3]:
                for comando in _comandos(script):
                    conexao.execute(comando)
            conexao.execute("INSERT INTO permissoes VALUES ('CONSULTAR_TITULOS', 'CLIENTE')")
            conexao.execute("PRAGMA user_version = 3")
        finally:
            conexao.close()
        preparar_banco(antigo)
        with UnidadeDeTrabalhoSQLite(antigo) as uow:
            matriz = uow.permissoes.obter()
            self.assertEqual(uow.contas_pagar.listar(), [])
            self.assertEqual(uow.fornecedores.listar(), [])
        self.assertTrue(matriz.permite(Perfil.OPERADOR_FINANCEIRO, Operacao.PAGAR_CONTA))
        self.assertTrue(matriz.permite(Perfil.CONTADOR, Operacao.CONSULTAR_CONTAS_PAGAR))
        self.assertFalse(matriz.permite(Perfil.CONTADOR, Operacao.CADASTRAR_CONTA_PAGAR))
        # Fechada logo: no Windows, um arquivo aberto não pode ser apagado com a pasta temporária.
        with closing(sqlite3.connect(antigo)) as conexao:
            perfis = {linha[0] for linha in conexao.execute("SELECT perfil FROM permissoes")}
        self.assertNotIn("CLIENTE", perfis)  # OPEN-57

    def test_CA_08_o_agendador_tambem_vence_as_contas_a_pagar(self):
        from remindme.inicializacao import montar

        sistema = montar(self.caminho, RelogioFixo(datetime(2026, 10, 3, 15, 0, tzinfo=timezone.utc)), CIFRADOR_DE_TESTE)
        acesso = sistema.servicos.acesso
        acesso.criar_primeiro_administrador("Ana", "ana@exemplo.com", SENHA)
        admin = acesso.entrar("ana@exemplo.com", SENHA).identificador
        fornecedor = sistema.servicos.fornecedores.cadastrar_fornecedor(admin, "Distribuidora", "11222333000181", "v@d.example")
        conta = sistema.servicos.contas_pagar.cadastrar_conta(admin, fornecedor.id, "Pneus", Decimal("10.00"), HOJE - timedelta(days=1))
        self.assertEqual(sistema.agendador.executar_uma_vez(), [conta.id])
        self.assertEqual(sistema.agendador.executar_uma_vez(), [])


class Spec005NoSQLite(ComBanco):
    """Migração 5: prazo e decisão do orçamento, vínculo do título e caixa de saída (Spec 005)."""

    def orcamento_convertido(self):
        from remindme.dominio.orcamento import Orcamento

        o = Orcamento.criar("o1", "c1", "u1", date(2026, 11, 2), "Boleto")
        o.incluir_item("i1", "Revisão", Decimal("1"), Decimal("900.00"))
        o.alterar_prazo(30)
        o.marcar_enviado(date(2026, 11, 2))
        o.registrar_decisao(True, date(2026, 11, 7), date(2026, 11, 7))
        titulo = Titulo.gerar_de_orcamento("t1", o)
        o.converter("t1")
        return o, titulo

    def test_spec_005_orcamento_e_titulo_guardam_os_campos_novos(self):
        o, titulo = self.orcamento_convertido()
        rejeitado = replace(o, id="o2", estado=o.estado.REJEITADO, titulo_id=None, motivo_rejeicao="Achou caro", itens=[])
        with self.uow as uow:
            uow.usuarios.salvar(Usuario("u1", "Diego", Perfil.OPERADOR_FINANCEIRO))
            uow.titulos.salvar(titulo)
            uow.orcamentos.salvar(o)
            uow.orcamentos.salvar(rejeitado)
        with self.uow as uow:
            lido = uow.orcamentos.obter("o1")
            self.assertEqual(
                (lido.prazo_pagamento_dias, lido.enviado_em, lido.decidido_em, lido.titulo_id, lido.motivo_rejeicao),
                (30, date(2026, 11, 2), date(2026, 11, 7), "t1", None),
            )
            self.assertEqual(uow.orcamentos.obter("o2").motivo_rejeicao, "Achou caro")
            lido_titulo = uow.titulos.obter("t1")
            self.assertEqual((lido_titulo.origem, lido_titulo.orcamento_id), ("orcamento", "o1"))

    def test_INV_1_indice_unico_barra_segundo_titulo_do_orcamento(self):
        _, titulo = self.orcamento_convertido()
        with self.uow as uow:
            uow.titulos.salvar(titulo)
        with self.assertRaises(sqlite3.IntegrityError):
            with self.uow as uow:
                uow.titulos.salvar(replace(titulo, id="t2"))
        with self.uow as uow:
            self.assertEqual([t.id for t in uow.titulos.listar()], ["t1"])

    def test_spec_005_mensagens_ida_e_volta(self):
        from remindme.aplicacao.portas import Mensagem

        enviada = Mensagem("m1", "c1", "a@b.com", "Assunto", "Linha 1\nLinha 2", datetime(2026, 11, 7, 12, 0), "enviada", "orcamento o1")
        falhou = replace(enviada, id="m2", resultado="falhou", enviada_em=datetime(2026, 11, 7, 13, 0))
        with self.uow as uow:
            uow.mensagens.registrar(enviada)
            uow.mensagens.registrar(falhou)
        with self.uow as uow:
            self.assertEqual(uow.mensagens.listar(), [enviada, falhou])

    def test_spec_005_banco_da_versao_4_ganha_colunas_tabela_e_permissao(self):
        antigo = str(Path(self._pasta.name) / "versao4.db")
        with closing(sqlite3.connect(antigo, isolation_level=None)) as conexao:
            for script in MIGRACOES[:4]:
                for comando in _comandos(script):
                    conexao.execute(comando)
            conexao.execute("INSERT INTO clientes VALUES ('c9', 'Cliente Antigo', '52998224725', 'a@b.com')")
            conexao.execute(
                "INSERT INTO titulos VALUES ('t9', 'c9', '10.00', '2026-10-10', 'manual', NULL, 'ABERTO')"
            )
            conexao.execute(
                "INSERT INTO orcamentos VALUES ('o9', 'c9', 'u9', '2026-10-01', 'RASCUNHO', NULL, '0.00', NULL, NULL, NULL, NULL)"
            )
            conexao.execute("PRAGMA user_version = 4")
        preparar_banco(antigo)
        with UnidadeDeTrabalhoSQLite(antigo) as uow:
            orcamento = uow.orcamentos.obter("o9")
            titulo = uow.titulos.obter("t9")
            matriz = uow.permissoes.obter()
            self.assertEqual(uow.mensagens.listar(), [])
        self.assertEqual(
            (orcamento.prazo_pagamento_dias, orcamento.enviado_em, orcamento.titulo_id, titulo.orcamento_id),
            (None, None, None, None),
        )
        self.assertTrue(matriz.permite(Perfil.OPERADOR_FINANCEIRO, Operacao.CONSULTAR_MENSAGENS))
        self.assertTrue(matriz.permite(Perfil.DONO, Operacao.CONSULTAR_MENSAGENS))
        self.assertFalse(matriz.permite(Perfil.CONTADOR, Operacao.CONSULTAR_MENSAGENS))
        with closing(sqlite3.connect(antigo)) as conexao:
            self.assertEqual(conexao.execute("PRAGMA user_version").fetchone()[0], 5)


class Spec005ConversaoAtomicaNoSQLite(ComBanco):
    def test_CA_12_RNF_09_falha_na_auditoria_da_conversao_nao_deixa_titulo_no_banco(self):
        """Spec 005, E5: o rollback do SQLite desfaz o título já salvo quando a auditoria da conversão falha."""
        from unittest import mock

        from remindme.aplicacao.servico_orcamentos import ServicoOrcamentos
        from remindme.dominio.orcamento import EstadoOrcamento
        from remindme.infraestrutura.canal import CanalSimulado
        from tests.apoio import abrir_sessao

        relogio = RelogioFixo(datetime(2026, 11, 7, 12, 0))
        servico = ServicoOrcamentos(self.uow, relogio, canal=CanalSimulado())
        with self.uow as uow:
            sessao = abrir_sessao(uow, Usuario("u1", "Diego", Perfil.OPERADOR_FINANCEIRO))
        o = servico.criar_orcamento(sessao, "c1", "Pix")
        servico.incluir_item(sessao, o.id, "Revisão", Decimal("1"), Decimal("900.00"))
        servico.alterar_prazo(sessao, o.id, 30)
        servico.enviar_orcamento(sessao, o.id)
        registrar = self.uow.auditoria.registrar

        def falhar_na_conversao(registro):
            if registro.valor_novo == "Convertido":
                raise RuntimeError("Falha simulada na auditoria da conversão.")
            registrar(registro)

        with mock.patch.object(self.uow.auditoria, "registrar", side_effect=falhar_na_conversao):
            with self.assertRaises(RuntimeError):
                servico.registrar_decisao_do_cliente(sessao, o.id, True, date(2026, 11, 7))
        with self.uow as uow:
            self.assertIs(uow.orcamentos.obter(o.id).estado, EstadoOrcamento.ENVIADO)
            self.assertEqual([t for t in uow.titulos.listar() if t.orcamento_id], [])
