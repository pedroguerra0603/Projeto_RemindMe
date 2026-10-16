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
from remindme.dominio.erros import OperacaoRecusada
from remindme.dominio.titulo import EstadoTitulo
from remindme.dominio.usuario import Perfil, Usuario
from remindme.infraestrutura.memoria import (
    AuditoriaEmMemoria,
    ClientesEmMemoria,
    RelogioFixo,
    RepositorioTitulosEmMemoria,
    UnidadeDeTrabalhoEmMemoria,
)

HOJE = date(2026, 10, 3)
FUTURO = HOJE + timedelta(days=30)
DONO = Usuario("dono", "Dono", Perfil.DONO)

PERMITIDO, NEGADO, SEM_RESTRICAO = "permitido", "negado", "sem restrição na Spec 006 (Spec 002)"

# Resultado esperado de cada operação para cada perfil, conforme RB-02 e OPEN-16 (decidida em 2026-10-03).
# "Sem restrição" é o que a Spec 006 define (seção 7): a autorização geral, inclusive RB-03 (Contador só
# consulta), é da Spec 002. Estas células ficam registradas, e não testadas como se fossem a regra final.
MATRIZ = {
    "estornar pagamento": {
        Perfil.DONO: PERMITIDO,
        Perfil.OPERADOR_FINANCEIRO: NEGADO,
        Perfil.CONTADOR: NEGADO,
        Perfil.CLIENTE: NEGADO,
        Perfil.ADMINISTRADOR: NEGADO,
    },
    "cancelar título": {
        Perfil.DONO: PERMITIDO,
        Perfil.OPERADOR_FINANCEIRO: NEGADO,
        Perfil.CONTADOR: NEGADO,
        Perfil.CLIENTE: NEGADO,
        Perfil.ADMINISTRADOR: NEGADO,
    },
    "cadastrar título": {p: SEM_RESTRICAO for p in Perfil},
    "registrar pagamento": {p: SEM_RESTRICAO for p in Perfil},
    "verificar vencimentos": {p: SEM_RESTRICAO for p in Perfil},
}


def usuario(perfil):
    return Usuario(perfil.name.lower(), perfil.value, perfil)


class Base(unittest.TestCase):
    def setUp(self):
        self.titulos = RepositorioTitulosEmMemoria()
        self.auditoria = AuditoriaEmMemoria()
        self.servico = ServicoTitulos(
            UnidadeDeTrabalhoEmMemoria(self.titulos, self.auditoria),
            ClientesEmMemoria({"c1", "c2"}),
            RelogioFixo(datetime(2026, 10, 3, 10, 0)),
        )
        self.titulo = self.servico.cadastrar_titulo(DONO, "c1", Decimal("1234.56"), FUTURO)
        self.titulo = self.servico.registrar_pagamento(DONO, self.titulo.id, Decimal("10.00"), HOJE)
        self.pagamento = self.titulo.pagamentos[0].id
        self.registros_antes = list(self.auditoria.registros)

    def operacao(self, nome, usuario_, titulo_id=None):
        titulo_id = titulo_id or self.titulo.id
        return {
            "estornar pagamento": lambda: self.servico.estornar_pagamento(
                usuario_, titulo_id, self.pagamento, "motivo", HOJE
            ),
            "cancelar título": lambda: self.servico.cancelar_titulo(usuario_, titulo_id, "motivo"),
        }[nome]()


class MatrizPerfilOperacao(Base):
    def test_RNF_02_a_matriz_cobre_todos_os_perfis_para_toda_operacao(self):
        for operacao, celulas in MATRIZ.items():
            with self.subTest(operacao=operacao):
                self.assertEqual(set(celulas), set(Perfil))

    def test_RNF_02_cada_celula_negada_recusa_a_operacao_sem_passar_pela_interface(self):
        negadas = [(op, p) for op, c in MATRIZ.items() for p, r in c.items() if r == NEGADO]
        self.assertEqual(len(negadas), 8)
        for operacao, perfil in negadas:
            with self.subTest(operacao=operacao, perfil=perfil.value):
                with self.assertRaises(OperacaoRecusada):
                    self.operacao(operacao, usuario(perfil))
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
        self.servico.cancelar_titulo(DONO, self.titulo.id, "desistência")
        with self.assertRaisesRegex(OperacaoRecusada, "Somente o Dono cancela"):
            self.servico.cancelar_titulo(usuario(Perfil.OPERADOR_FINANCEIRO), self.titulo.id, None)
        with self.assertRaisesRegex(OperacaoRecusada, "Somente o Dono estorna"):
            self.servico.estornar_pagamento(
                usuario(Perfil.OPERADOR_FINANCEIRO), self.titulo.id, self.pagamento, None, HOJE
            )


class SemVazamentoNaRecusa(Base):
    def test_RNF_25_recusa_por_perfil_nao_revela_se_o_titulo_existe(self):
        existente = self.titulo.id
        for perfil in (Perfil.OPERADOR_FINANCEIRO, Perfil.CONTADOR, Perfil.CLIENTE):
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
                self.operacao(operacao, usuario(Perfil.CLIENTE))
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

    def test_RB_30_a_porta_de_auditoria_so_oferece_incluir(self):
        publicos = {n for n, _ in inspect.getmembers(portas.RepositorioAuditoria) if not n.startswith("_")}
        self.assertEqual(publicos, {"registrar"})

    def test_RB_30_a_auditoria_em_memoria_so_oferece_incluir(self):
        publicos = {
            n for n, _ in inspect.getmembers(AuditoriaEmMemoria, callable) if not n.startswith("_")
        }
        self.assertEqual(publicos, {"registrar"})

    def test_RB_30_o_servico_nao_oferece_alterar_nem_excluir_auditoria(self):
        publicos = {n for n, _ in inspect.getmembers(ServicoTitulos, callable) if not n.startswith("_")}
        self.assertFalse({n for n in publicos if "audit" in n or "excluir" in n or "apagar" in n})

    def test_RB_01_recusa_nao_apaga_nem_reescreve_a_auditoria_anterior(self):
        antes = list(self.auditoria.registros)
        with self.assertRaises(OperacaoRecusada):
            self.servico.cancelar_titulo(usuario(Perfil.CONTADOR), self.titulo.id, "motivo")
        self.assertEqual(self.auditoria.registros[: len(antes)], antes)

    def test_ADR_004_a_lista_devolvida_pela_auditoria_em_memoria_nao_altera_o_armazenado(self):
        """S-01 resolvida pela Spec 001 (CA-07, CA-08): `registros` devolve uma lista nova a cada leitura.
        Apagar ou trocar itens dessa lista não apaga nem altera o que está armazenado. O adaptador real
        (OPEN-02) continua precisando impedir a alteração na própria camada de persistência."""
        lida = self.auditoria.registros
        self.assertIsInstance(lida[0], RegistroAuditoria)
        quantidade = len(lida)
        lida.clear()
        self.assertEqual(len(self.auditoria.registros), quantidade)


class Pendentes(unittest.TestCase):
    """Dependem de specs ainda não aprovadas. Nenhum código é escrito antes (regra 1 do CLAUDE.md)."""

    @unittest.skip("Pendente da Spec 002: autorização geral. Contador não cria nem altera registro (RB-03, "
                   "RF-67); perfil sem permissão explícita é negado por padrão (RNF-02) em cadastro, pagamento "
                   "e verificação de vencimentos.")
    def test_RB_03_contador_nao_cadastra_nem_registra_pagamento(self):
        pass

    @unittest.skip("Pendente das Specs 002 e 009: o perfil Cliente só acessa títulos do próprio cliente "
                   "(RNF-25, RB-26). Hoje o serviço não conhece o vínculo entre usuário e cliente.")
    def test_RNF_25_cliente_nao_acessa_titulo_de_outro_cliente(self):
        pass

    @unittest.skip("Pendente da Spec 002: autenticação em toda funcionalidade (RNF-01); depende de OPEN-03.")
    def test_RNF_01_acesso_sem_sessao_e_recusado(self):
        pass

    @unittest.skip("Pendente das Specs 009 e 011: o payload enviado à IA simulada não contém nome, documento "
                   "nem contato (RNF-22). Depende do simulador de IA (#79).")
    def test_RNF_22_payload_da_ia_nao_contem_dados_pessoais(self):
        pass

    @unittest.skip("Pendente da Spec 013: consulta de auditoria por perfil (UC-12). A exclusão e a alteração "
                   "pelo banco dependem de OPEN-02.")
    def test_RNF_06_perfil_nenhum_exclui_registro_de_auditoria_no_armazenamento_real(self):
        pass


if __name__ == "__main__":
    unittest.main()
