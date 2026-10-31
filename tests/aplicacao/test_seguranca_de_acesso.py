"""Segurança de acesso e isolamento de dados (ISO/IEC 25010, Funcionalidade). Issue #75.

Foco só em autorização, isolamento e exposição de dados; as regras de negócio estão em outros arquivos.
As operações são chamadas direto no serviço, sem interface (RNF-03). A matriz perfil × operação e os casos
pendentes estão em docs/qualidade/seguranca-de-acesso.md.
"""

import dataclasses
import inspect
import unittest
from datetime import date, datetime, timedelta
from decimal import Decimal

from remindme.aplicacao import portas
from remindme.aplicacao.servico_titulos import ServicoTitulos
from remindme.dominio.auditoria import RegistroAuditoria
from remindme.dominio.erros import OperacaoNegada, OperacaoRecusada
from remindme.dominio.titulo import EstadoTitulo
from remindme.dominio.usuario import Perfil, Usuario
from remindme.infraestrutura.memoria import (
    AuditoriaEmMemoria,
    ClientesEmMemoria,
    RelogioFixo,
    RepositorioTitulosEmMemoria,
    UnidadeDeTrabalhoEmMemoria,
)
from tests.apoio import ComSessoes

HOJE = date(2026, 10, 3)
FUTURO = HOJE + timedelta(days=30)
DONO = Usuario("dono", "Dono", Perfil.DONO)

PERMITIDO, NEGADO = "permitido", "negado"

# Resultado esperado de cada operação para cada perfil: RB-02, OPEN-16, a matriz da Spec 002 (RB-03) e o
# Administrador global (OPEN-53).
MATRIZ = {
    "estornar pagamento": {
        Perfil.DONO: PERMITIDO,
        Perfil.OPERADOR_FINANCEIRO: NEGADO,
        Perfil.CONTADOR: NEGADO,
        Perfil.ADMINISTRADOR: PERMITIDO,
    },
    "cancelar título": {
        Perfil.DONO: PERMITIDO,
        Perfil.OPERADOR_FINANCEIRO: NEGADO,
        Perfil.CONTADOR: NEGADO,
        Perfil.ADMINISTRADOR: PERMITIDO,
    },
    **{
        operacao: {
            Perfil.DONO: PERMITIDO,
            Perfil.OPERADOR_FINANCEIRO: PERMITIDO,
            Perfil.CONTADOR: NEGADO,
                Perfil.ADMINISTRADOR: PERMITIDO,
        }
        for operacao in ("cadastrar título", "registrar pagamento", "verificar vencimentos")
    },
}


def usuario(perfil):
    return Usuario(perfil.name.lower(), perfil.value, perfil)


class Base(ComSessoes, unittest.TestCase):
    def setUp(self):
        self.titulos = RepositorioTitulosEmMemoria()
        self.auditoria = AuditoriaEmMemoria()
        self.uow = UnidadeDeTrabalhoEmMemoria(self.titulos, self.auditoria)
        self.servico = ServicoTitulos(
            self.uow,
            ClientesEmMemoria({"c1", "c2"}),
            RelogioFixo(datetime(2026, 10, 3, 10, 0)),
        )
        self.titulo = self.servico.cadastrar_titulo(self.sessao(DONO), "c1", Decimal("1234.56"), FUTURO)
        self.titulo = self.servico.registrar_pagamento(self.sessao(DONO), self.titulo.id, Decimal("10.00"), HOJE)
        self.pagamento = self.titulo.pagamentos[0].id
        self.registros_antes = list(self.auditoria.registros)

    def operacao(self, nome, usuario_, titulo_id=None):
        titulo_id = titulo_id or self.titulo.id
        return {
            "estornar pagamento": lambda: self.servico.estornar_pagamento(
                self.sessao(usuario_), titulo_id, self.pagamento, "motivo", HOJE
            ),
            "cancelar título": lambda: self.servico.cancelar_titulo(self.sessao(usuario_), titulo_id, "motivo"),
            "cadastrar título": lambda: self.servico.cadastrar_titulo(
                self.sessao(usuario_), "c1", Decimal("10.00"), FUTURO
            ),
            "registrar pagamento": lambda: self.servico.registrar_pagamento(
                self.sessao(usuario_), titulo_id, Decimal("10.00"), HOJE
            ),
            "verificar vencimentos": lambda: self.servico.verificar_vencimentos(self.sessao(usuario_), HOJE),
        }[nome]()


class MatrizPerfilOperacao(Base):
    def test_RNF_02_a_matriz_cobre_todos_os_perfis_para_toda_operacao(self):
        for operacao, celulas in MATRIZ.items():
            with self.subTest(operacao=operacao):
                self.assertEqual(set(celulas), set(Perfil))

    def test_RNF_02_cada_celula_negada_recusa_a_operacao_sem_passar_pela_interface(self):
        negadas = [(op, p) for op, c in MATRIZ.items() for p, r in c.items() if r == NEGADO]
        self.assertEqual(len(negadas), 7)  # 12 até a retirada do perfil Cliente (OPEN-57)
        for operacao, perfil in negadas:
            with self.subTest(operacao=operacao, perfil=perfil.value):
                titulos_antes = dict(self.titulos.dados)
                with self.assertRaises(OperacaoNegada):
                    self.operacao(operacao, usuario(perfil))
                self.assertEqual(self.titulos.dados, titulos_antes)
                self.assertIs(self.titulos.obter(self.titulo.id).estado, EstadoTitulo.ABERTO)
                self.assertFalse(self.titulos.obter(self.titulo.id).pagamentos[0].estornado)
                self.assertEqual(self.auditoria.registros, self.registros_antes)

    def test_RNF_02_negar_por_padrao_qualquer_perfil_novo_nao_estorna_nem_cancela(self):
        """Um perfil que não seja o Dono, inclusive um que ainda não existe, é negado."""
        outro = Usuario("novo", "Novo", object())
        for operacao in ("estornar pagamento", "cancelar título"):
            with self.subTest(operacao=operacao):
                with self.assertRaises(OperacaoRecusada):
                    self.operacao(operacao, outro)

    def test_RNF_02_cada_celula_permitida_executa_a_operacao(self):
        for operacao, celulas in MATRIZ.items():
            for perfil, resultado in celulas.items():
                if resultado != PERMITIDO:
                    continue
                with self.subTest(operacao=operacao, perfil=perfil.value):
                    self.setUp()
                    self.operacao(operacao, usuario(perfil))

    def test_RF_67_a_recusa_informa_o_motivo(self):
        for operacao in ("estornar pagamento", "cancelar título"):
            with self.subTest(operacao=operacao):
                with self.assertRaisesRegex(OperacaoRecusada, "Somente o Dono"):
                    self.operacao(operacao, usuario(Perfil.CONTADOR))

    def test_RNF_02_a_permissao_e_verificada_antes_do_estado_e_do_motivo(self):
        """Quem não pode não descobre, pela mensagem, se o motivo faltava ou se o título estava cancelado."""
        self.servico.cancelar_titulo(self.sessao(DONO), self.titulo.id, "desistência")
        with self.assertRaisesRegex(OperacaoRecusada, "Somente o Dono cancela"):
            self.servico.cancelar_titulo(self.sessao(usuario(Perfil.OPERADOR_FINANCEIRO)), self.titulo.id, None)
        with self.assertRaisesRegex(OperacaoRecusada, "Somente o Dono estorna"):
            self.servico.estornar_pagamento(
                self.sessao(usuario(Perfil.OPERADOR_FINANCEIRO)), self.titulo.id, self.pagamento, None, HOJE
            )


class SemVazamentoNaRecusa(Base):
    def test_RNF_25_recusa_por_perfil_nao_revela_se_o_titulo_existe(self):
        existente = self.titulo.id
        for perfil in (Perfil.OPERADOR_FINANCEIRO, Perfil.CONTADOR):
            with self.subTest(perfil=perfil.value):
                mensagens = set()
                for titulo_id in (existente, "titulo-que-nao-existe"):
                    with self.assertRaises(OperacaoRecusada) as ctx:
                        self.operacao("cancelar título", usuario(perfil), titulo_id)
                    mensagens.add(ctx.exception.motivo)
                self.assertEqual(len(mensagens), 1)

    def test_RNF_25_a_mensagem_de_recusa_nao_contem_dados_do_titulo(self):
        for operacao in ("estornar pagamento", "cancelar título"):
            with self.assertRaises(OperacaoRecusada) as ctx:
                self.operacao(operacao, usuario(Perfil.CONTADOR))
            for dado in (self.titulo.id, self.pagamento, "1234.56", "c1"):
                with self.subTest(operacao=operacao, dado=dado):
                    self.assertNotIn(dado, ctx.exception.motivo)


class AuditoriaSomenteInclusao(Base):
    """RNF-06, RB-30 e ADR-004: ninguém altera nem exclui registro de auditoria."""

    def test_RNF_06_registro_de_auditoria_nao_pode_ser_alterado(self):
        registro = self.auditoria.registros[0]
        for campo in ("usuario_id", "operacao", "valor_novo", "motivo", "data_hora"):
            with self.subTest(campo=campo):
                with self.assertRaises(dataclasses.FrozenInstanceError):
                    setattr(registro, campo, "adulterado")

    def test_RNF_06_registro_de_auditoria_nao_ganha_campo_novo(self):
        with self.assertRaises(dataclasses.FrozenInstanceError):
            self.auditoria.registros[0].campo_novo = "x"

    def test_RB_30_a_porta_de_auditoria_so_oferece_incluir_e_ler(self):
        """A leitura entrou com a Spec 013 (consulta de auditoria); alteração e exclusão continuam fora."""
        publicos = {n for n, _ in inspect.getmembers(portas.RepositorioAuditoria) if not n.startswith("_")}
        self.assertEqual(publicos, {"registrar", "listar"})

    def test_RB_30_a_auditoria_em_memoria_so_oferece_incluir_e_ler(self):
        publicos = {
            n for n, _ in inspect.getmembers(AuditoriaEmMemoria, callable) if not n.startswith("_")
        }
        self.assertEqual(publicos, {"registrar", "listar"})

    def test_RB_30_o_servico_nao_oferece_alterar_nem_excluir_auditoria(self):
        publicos = {n for n, _ in inspect.getmembers(ServicoTitulos, callable) if not n.startswith("_")}
        self.assertFalse({n for n in publicos if "audit" in n or "excluir" in n or "apagar" in n})

    def test_RB_01_recusa_nao_apaga_nem_reescreve_a_auditoria_anterior(self):
        antes = list(self.auditoria.registros)
        with self.assertRaises(OperacaoRecusada):
            self.servico.cancelar_titulo(self.sessao(usuario(Perfil.CONTADOR)), self.titulo.id, "motivo")
        self.assertEqual(self.auditoria.registros[: len(antes)], antes)

    def test_ADR_004_provisorio_o_duble_em_memoria_expoe_a_lista_de_registros(self):
        """Fragilidade conhecida (S-01), e não defeito da Spec 006: `registros` é uma lista pública do dublê
        de teste, e quem tem acesso ao objeto pode apagá-la. O adaptador real (OPEN-02) precisa impedir a
        alteração na própria camada de persistência. Este teste só documenta o fato."""
        self.assertIsInstance(self.auditoria.registros, list)
        self.assertIsInstance(self.auditoria.registros[0], RegistroAuditoria)


class Pendentes(unittest.TestCase):
    """Dependem de specs ainda não aprovadas. Nenhum código é escrito antes (regra 1 do CLAUDE.md).

    RB-03 (Contador não cadastra nem paga) e RNF-01 (sem sessão) saíram daqui com a Spec 002: estão em
    `test_spec_002_aceite.py` (CA-09, CA-10) e na matriz acima."""

    @unittest.skip("Pendente das Specs 009 e 011: o payload enviado à IA simulada não contém nome, documento "
                   "nem contato (RNF-22). Depende do simulador de IA (#79).")
    def test_RNF_22_payload_da_ia_nao_contem_dados_pessoais(self):
        pass


class AuditoriaNoArmazenamentoReal(unittest.TestCase):
    """RNF-06 com o banco escolhido (OPEN-36, ADR-007) e a consulta da Spec 013: nenhum perfil altera nem exclui."""

    def test_RNF_06_perfil_nenhum_exclui_registro_de_auditoria_no_armazenamento_real(self):
        import sqlite3
        import tempfile
        from pathlib import Path

        from remindme.aplicacao.servico_acesso import ServicoAcesso
        from remindme.aplicacao.servico_auditoria import ServicoAuditoria
        from remindme.aplicacao.servico_clientes import ServicoClientes
        from remindme.infraestrutura.sqlite import UnidadeDeTrabalhoSQLite, preparar_banco

        for servico in (ServicoAcesso, ServicoAuditoria, ServicoClientes, ServicoTitulos):
            publicos = {n for n, _ in inspect.getmembers(servico, callable) if not n.startswith("_")}
            with self.subTest(servico=servico.__name__):
                self.assertFalse({n for n in publicos if "excluir" in n or "apagar" in n or "alterar_registro" in n})
        with tempfile.TemporaryDirectory() as pasta:
            caminho = str(Path(pasta).joinpath("remindme.db"))
            preparar_banco(caminho)
            with UnidadeDeTrabalhoSQLite(caminho) as uow:
                uow.auditoria.registrar(RegistroAuditoria("u1", datetime(2026, 10, 3), "operação", "titulo t1"))
            conexao = sqlite3.connect(caminho)
            try:
                for comando in ("UPDATE auditoria SET motivo = 'adulterado'", "DELETE FROM auditoria"):
                    with self.subTest(comando=comando), self.assertRaises(sqlite3.DatabaseError):
                        conexao.execute(comando)
            finally:
                conexao.close()


if __name__ == "__main__":
    unittest.main()
