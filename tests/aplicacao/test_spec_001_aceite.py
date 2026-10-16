"""Critérios de aceitação da Spec 001: fundação em camadas e auditoria de operações.

Cada teste leva o identificador do critério (CA-nn) ou da regra (RB-nn, RNF-nn) no nome.
"""

import copy
import dataclasses
import inspect
import os
import subprocess
import sys
import unittest
from datetime import date, datetime, timedelta
from decimal import Decimal
from pathlib import Path

from remindme.aplicacao import portas
from remindme.aplicacao.servico_titulos import ServicoTitulos
from remindme.dominio.auditoria import RegistroAuditoria
from remindme.dominio.erros import OperacaoRecusada
from remindme.dominio.titulo import EstadoTitulo
from remindme.dominio.usuario import Perfil, Usuario
from remindme.infraestrutura.memoria import (
    AuditoriaEmMemoria,
    ClientesEmMemoria,
    RegistroErrosEmMemoria,
    RelogioFixo,
    RepositorioTitulosEmMemoria,
    UnidadeDeTrabalhoEmMemoria,
)
from tests.arquitetura.test_camadas import importacoes

RAIZ_REPOSITORIO = Path(__file__).resolve().parents[2]
RAIZ_CODIGO = RAIZ_REPOSITORIO / "src" / "remindme"

HOJE = date(2026, 10, 16)
ONTEM = HOJE - timedelta(days=1)
FUTURO = HOJE + timedelta(days=30)
AGORA = datetime(2026, 10, 16, 9, 30)
DONO = Usuario("dono", "Dono", Perfil.DONO)
OPERADOR = Usuario("operador", "Operador Financeiro", Perfil.OPERADOR_FINANCEIRO)
R = Decimal

# Marca o processo filho de CA-13, para que ele não rode a suíte de novo.
VARIAVEL_CA_13 = "REMINDME_CA_13_PROCESSO_FILHO"


class RepositorioQueFalha(RepositorioTitulosEmMemoria):
    """Falha na gravação do título a partir da n-ésima chamada a `salvar`."""

    def __init__(self):
        super().__init__()
        self.falhar_a_partir_de = None
        self.gravacoes = 0

    def salvar(self, titulo):
        self.gravacoes += 1
        if self.falhar_a_partir_de is not None and self.gravacoes >= self.falhar_a_partir_de:
            raise RuntimeError("Falha simulada na gravação do título.")
        super().salvar(titulo)


class AuditoriaQueFalhaNoSegundoRegistro(AuditoriaEmMemoria):
    """Grava o primeiro registro da operação e falha no segundo."""

    def __init__(self):
        super().__init__()
        self.armada = False
        self.tentativas = 0

    def registrar(self, registro):
        if self.armada:
            self.tentativas += 1
            if self.tentativas == 2:
                raise RuntimeError("Falha simulada na gravação da auditoria.")
        super().registrar(registro)


class Base(unittest.TestCase):
    auditoria_classe = AuditoriaEmMemoria

    def setUp(self):
        self.titulos = RepositorioQueFalha()
        self.auditoria = self.auditoria_classe()
        self.erros = RegistroErrosEmMemoria()
        self.relogio = RelogioFixo(AGORA)
        self.servico = ServicoTitulos(
            UnidadeDeTrabalhoEmMemoria(self.titulos, self.auditoria),
            ClientesEmMemoria({"c1"}),
            self.relogio,
            erros=self.erros,
        )

    def novo_titulo(self, valor="100.00", vencimento=FUTURO):
        return self.servico.cadastrar_titulo(OPERADOR, "c1", R(valor), vencimento)

    def fotografia(self):
        return copy.deepcopy(self.titulos.dados), self.auditoria.registros


class Auditoria(Base):
    def test_CA_01_cadastro_de_titulo_gera_registro_com_estado_inicial(self):
        t = self.novo_titulo()
        [registro] = self.auditoria.registros
        self.assertEqual(registro.usuario_id, OPERADOR.id)
        self.assertEqual(registro.data_hora, AGORA)
        self.assertEqual(registro.operacao, "cadastrar título")
        self.assertEqual(registro.registro_afetado, f"titulo {t.id}")
        self.assertEqual(registro.campo, "estado")
        self.assertIsNone(registro.valor_anterior)
        self.assertEqual(registro.valor_novo, "Aberto")
        self.assertFalse(registro.automatica)

    def test_CA_02_pagamento_gera_registro_do_pagamento_e_da_mudanca_de_estado(self):
        t = self.novo_titulo()
        t = self.servico.registrar_pagamento(OPERADOR, t.id, R("100.00"), HOJE)
        pagamento, estado = self.auditoria.registros[1:]
        self.assertEqual(pagamento.operacao, "registrar pagamento")
        self.assertEqual(pagamento.usuario_id, OPERADOR.id)
        self.assertEqual(pagamento.registro_afetado, f"titulo {t.id}")
        self.assertIsNone(pagamento.valor_anterior)
        self.assertIn(t.pagamentos[0].id, pagamento.valor_novo)
        self.assertEqual(
            (estado.registro_afetado, estado.campo, estado.valor_anterior, estado.valor_novo),
            (f"titulo {t.id}", "estado", "Aberto", "Baixado"),
        )
        self.assertEqual(estado.usuario_id, OPERADOR.id)

    def test_CA_03_estorno_gera_registro_do_pagamento_e_da_mudanca_de_estado(self):
        t = self.novo_titulo()
        t = self.servico.registrar_pagamento(OPERADOR, t.id, R("100.00"), HOJE)
        pagamento_id = t.pagamentos[0].id
        antes = len(self.auditoria.registros)
        self.servico.estornar_pagamento(DONO, t.id, pagamento_id, "cheque devolvido", HOJE)
        pagamento, estado = self.auditoria.registros[antes:]
        self.assertEqual(
            (pagamento.usuario_id, pagamento.operacao, pagamento.registro_afetado, pagamento.campo,
             pagamento.valor_anterior, pagamento.valor_novo, pagamento.motivo),
            ("dono", "estornar pagamento", f"pagamento {pagamento_id}", "estornado",
             "não", "sim", "cheque devolvido"),
        )
        self.assertEqual(
            (estado.usuario_id, estado.registro_afetado, estado.campo, estado.valor_anterior,
             estado.valor_novo, estado.motivo),
            ("dono", f"titulo {t.id}", "estado", "Baixado", "Aberto", "cheque devolvido"),
        )

    def test_CA_04_RB_01_pagamento_recusado_nao_grava_auditoria(self):
        t = self.novo_titulo()
        self.servico.registrar_pagamento(OPERADOR, t.id, R("100.00"), HOJE)
        antes = self.fotografia()
        with self.assertRaises(OperacaoRecusada):
            self.servico.registrar_pagamento(OPERADOR, t.id, R("1.00"), HOJE)
        self.assertEqual(self.fotografia(), antes)
        self.assertEqual(self.erros.registros, [])

    def test_CA_06_falha_ao_gravar_o_titulo_depois_da_auditoria_desfaz_a_auditoria(self):
        """O primeiro título é gravado e auditado; a gravação do segundo falha na mesma operação."""
        primeiro = self.novo_titulo(vencimento=ONTEM)
        segundo = self.novo_titulo(vencimento=ONTEM)
        antes = self.fotografia()
        self.titulos.falhar_a_partir_de = self.titulos.gravacoes + 2
        with self.assertRaises(RuntimeError):
            self.servico.verificar_vencimentos(OPERADOR, HOJE)
        self.assertEqual(self.fotografia(), antes)
        for t in (primeiro, segundo):
            self.assertIs(self.titulos.obter(t.id).estado, EstadoTitulo.ABERTO)

    def test_CA_06_falha_ao_gravar_o_titulo_no_cadastro_nao_deixa_auditoria(self):
        antes = self.fotografia()
        self.titulos.falhar_a_partir_de = self.titulos.gravacoes + 1
        with self.assertRaises(RuntimeError):
            self.novo_titulo()
        self.assertEqual(self.fotografia(), antes)

    def test_CA_09_verificacao_de_vencimento_sem_usuario_e_automatica(self):
        t = self.novo_titulo(vencimento=ONTEM)
        self.assertEqual(self.servico.verificar_vencimentos(None, HOJE), [t.id])
        self.assertIs(self.titulos.obter(t.id).estado, EstadoTitulo.VENCIDO)
        registro = self.auditoria.registros[-1]
        self.assertIsNone(registro.usuario_id)
        self.assertTrue(registro.automatica)
        self.assertEqual(registro.rotina, "verificação de vencimento")
        self.assertEqual(
            (registro.registro_afetado, registro.campo, registro.valor_anterior, registro.valor_novo),
            (f"titulo {t.id}", "estado", "Aberto", "Vencido"),
        )

    def test_CA_09_verificacao_de_vencimento_com_usuario_nao_e_automatica(self):
        self.novo_titulo(vencimento=ONTEM)
        self.servico.verificar_vencimentos(OPERADOR, HOJE)
        registro = self.auditoria.registros[-1]
        self.assertEqual(registro.usuario_id, OPERADOR.id)
        self.assertFalse(registro.automatica)
        self.assertIsNone(registro.rotina)

    def test_CA_11_registros_aparecem_na_ordem_de_gravacao(self):
        primeiro = self.novo_titulo()
        self.relogio.momento = AGORA + timedelta(minutes=1)
        segundo = self.novo_titulo()
        self.relogio.momento = AGORA + timedelta(minutes=2)
        self.servico.cancelar_titulo(DONO, primeiro.id, "desistência")
        self.assertEqual(
            [(r.registro_afetado, r.data_hora.minute) for r in self.auditoria.registros],
            [(f"titulo {primeiro.id}", 30), (f"titulo {segundo.id}", 31), (f"titulo {primeiro.id}", 32)],
        )

    def test_RF_05_cada_registro_guarda_campo_valor_anterior_e_novo_valor(self):
        t = self.novo_titulo()
        self.servico.cancelar_titulo(DONO, t.id, "desistência")
        registro = self.auditoria.registros[-1]
        self.assertEqual(
            (registro.campo, registro.valor_anterior, registro.valor_novo, registro.motivo),
            ("estado", "Aberto", "Cancelado", "desistência"),
        )


class FalhaNaAuditoria(Base):
    auditoria_classe = AuditoriaQueFalhaNoSegundoRegistro

    def test_CA_05_falha_na_auditoria_durante_o_pagamento_desfaz_tudo(self):
        """O registro do pagamento é gravado; o da mudança de estado falha. Nada permanece."""
        t = self.novo_titulo()
        antes = self.fotografia()
        self.auditoria.armada = True
        with self.assertRaises(RuntimeError):
            self.servico.registrar_pagamento(OPERADOR, t.id, R("100.00"), HOJE)
        self.assertEqual(self.auditoria.tentativas, 2)
        self.assertEqual(self.fotografia(), antes)
        salvo = self.titulos.obter(t.id)
        self.assertEqual(salvo.pagamentos, [])
        self.assertEqual(salvo.saldo, R("100.00"))
        self.assertIs(salvo.estado, EstadoTitulo.ABERTO)


class Imutabilidade(Base):
    def setUp(self):
        super().setUp()
        self.novo_titulo()
        self.original = dataclasses.astuple(self.auditoria.registros[0])

    def test_CA_07_RB_30_registro_gravado_nao_e_alterado(self):
        registro = self.auditoria.registros[0]
        for campo in dataclasses.fields(RegistroAuditoria):
            with self.subTest(campo=campo.name):
                with self.assertRaises(dataclasses.FrozenInstanceError):
                    setattr(registro, campo.name, "adulterado")
                with self.assertRaises(dataclasses.FrozenInstanceError):
                    delattr(registro, campo.name)
        self.assertEqual(dataclasses.astuple(self.auditoria.registros[0]), self.original)

    def test_CA_07_RNF_06_burlar_o_objeto_devolvido_nao_altera_o_armazenado(self):
        """Mesmo contornando a imutabilidade do objeto lido, o registro armazenado continua igual."""
        lido = self.auditoria.registros[0]
        object.__setattr__(lido, "usuario_id", "intruso")
        object.__setattr__(lido, "valor_novo", "Baixado")
        self.assertEqual(dataclasses.astuple(self.auditoria.registros[0]), self.original)

    def test_CA_07_burlar_o_objeto_gravado_depois_de_registrar_nao_altera_o_armazenado(self):
        registro = RegistroAuditoria("u", AGORA, "operação", "titulo t9")
        self.auditoria.registrar(registro)
        object.__setattr__(registro, "operacao", "outra")
        self.assertEqual(self.auditoria.registros[-1].operacao, "operação")

    def test_CA_08_RB_30_nao_ha_operacao_de_exclusao_nem_de_alteracao(self):
        for classe in (portas.RepositorioAuditoria, AuditoriaEmMemoria):
            with self.subTest(classe=classe.__name__):
                publicos = {
                    n for n, _ in inspect.getmembers(classe, callable) if not n.startswith("_")
                }
                self.assertEqual(publicos, {"registrar"})
        servico = {n for n, _ in inspect.getmembers(ServicoTitulos, callable) if not n.startswith("_")}
        self.assertFalse({n for n in servico if "audit" in n or "excluir" in n or "apagar" in n})

    def test_CA_08_RNF_06_apagar_a_lista_lida_nao_exclui_registro(self):
        lida = self.auditoria.registros
        lida.clear()
        with self.assertRaises(AttributeError):
            self.auditoria.registros = []
        with self.assertRaises(AttributeError):
            del self.auditoria.registros
        self.assertEqual(len(self.auditoria.registros), 1)
        self.assertEqual(dataclasses.astuple(self.auditoria.registros[0]), self.original)


class ErroNaoTratado(Base):
    def test_CA_10_RNF_21_erro_nao_tratado_e_registrado_desfeito_e_propagado(self):
        t = self.novo_titulo()
        antes = self.fotografia()
        self.auditoria.falhar = True
        with self.assertRaises(RuntimeError) as contexto:
            self.servico.registrar_pagamento(OPERADOR, t.id, R("100.00"), HOJE)
        self.assertIn("Falha simulada", str(contexto.exception))
        self.auditoria.falhar = False
        self.assertEqual(self.fotografia(), antes)
        [erro] = self.erros.registros
        self.assertEqual(erro.data_hora, AGORA)
        self.assertEqual(erro.operacao, "registrar pagamento")
        self.assertEqual(erro.usuario_id, OPERADOR.id)
        self.assertTrue(erro.correlacao)
        self.assertIn(erro.correlacao, "\n".join(getattr(contexto.exception, "__notes__", [])))

    def test_CA_10_cada_erro_tem_identificador_de_correlacao_proprio(self):
        t = self.novo_titulo()
        self.titulos.falhar_a_partir_de = self.titulos.gravacoes + 1
        for _ in range(2):
            with self.assertRaises(RuntimeError):
                self.servico.registrar_pagamento(OPERADOR, t.id, R("1.00"), HOJE)
        self.assertEqual(len({e.correlacao for e in self.erros.registros}), 2)

    def test_CA_10_erro_em_operacao_automatica_e_registrado_sem_usuario(self):
        self.novo_titulo(vencimento=ONTEM)
        self.titulos.falhar_a_partir_de = self.titulos.gravacoes + 1
        with self.assertRaises(RuntimeError):
            self.servico.verificar_vencimentos(None, HOJE)
        [erro] = self.erros.registros
        self.assertIsNone(erro.usuario_id)
        self.assertEqual(erro.operacao, "verificar vencimentos")

    def test_CA_10_recusa_de_regra_de_negocio_nao_e_erro_nao_tratado(self):
        t = self.novo_titulo()
        with self.assertRaises(OperacaoRecusada):
            self.servico.cancelar_titulo(OPERADOR, t.id, "motivo")
        self.assertEqual(self.erros.registros, [])

    def test_CA_10_falha_ao_registrar_o_erro_nao_esconde_o_erro_original(self):
        class RegistroQueFalha:
            def registrar(self, registro):
                raise OSError("destino indisponível")

        servico = ServicoTitulos(
            UnidadeDeTrabalhoEmMemoria(self.titulos, self.auditoria),
            ClientesEmMemoria({"c1"}),
            self.relogio,
            erros=RegistroQueFalha(),
        )
        self.auditoria.falhar = True
        with self.assertRaisesRegex(RuntimeError, "Falha simulada"):
            servico.cadastrar_titulo(OPERADOR, "c1", R("1.00"), FUTURO)


class Arquitetura(unittest.TestCase):
    PERMITIDAS = {
        "dominio": {"dominio"},
        "aplicacao": {"dominio", "aplicacao"},
    }

    def test_CA_12_RNF_19_dominio_e_aplicacao_importam_somente_camadas_permitidas(self):
        for camada, permitidas in self.PERMITIDAS.items():
            for arquivo in (RAIZ_CODIGO / camada).rglob("*.py"):
                for modulo in importacoes(arquivo):
                    partes = modulo.split(".")
                    with self.subTest(arquivo=f"{camada}/{arquivo.name}", importa=modulo):
                        if partes[0] == "remindme":
                            self.assertIn(partes[1], permitidas)
                        else:
                            self.assertIn(partes[0], sys.stdlib_module_names)

    def test_INV_5_a_auditoria_e_gravada_em_um_unico_ponto_da_aplicacao(self):
        """Só `aplicacao/auditoria.py` cria `RegistroAuditoria` ou chama `auditoria.registrar`."""
        for arquivo in (RAIZ_CODIGO / "aplicacao").rglob("*.py"):
            texto = arquivo.read_text(encoding="utf-8")
            if arquivo.name != "auditoria.py":
                with self.subTest(arquivo=arquivo.name):
                    self.assertNotIn("RegistroAuditoria(", texto)
                    self.assertNotIn("auditoria.registrar", texto)


class SuiteSemCredencial(unittest.TestCase):
    def test_RNF_23_codigo_nao_le_variaveis_de_ambiente(self):
        for arquivo in RAIZ_CODIGO.rglob("*.py"):
            texto = arquivo.read_text(encoding="utf-8")
            with self.subTest(arquivo=arquivo.name):
                self.assertNotIn("environ", texto)
                self.assertNotIn("getenv", texto)

    @unittest.skipIf(os.environ.get(VARIAVEL_CA_13), "processo filho de CA-13")
    def test_CA_13_RNF_23_suite_inteira_passa_sem_variavel_de_credencial(self):
        """Roda a suíte em um processo com o ambiente reduzido ao mínimo para o Python funcionar."""
        minimas = ("PATH", "SYSTEMROOT", "TEMP", "TMP", "TMPDIR", "LANG")
        ambiente = {k: os.environ[k] for k in minimas if k in os.environ}
        ambiente[VARIAVEL_CA_13] = "1"
        resultado = subprocess.run(
            [sys.executable, "-m", "unittest", "discover", "-s", "tests", "-t", "."],
            cwd=RAIZ_REPOSITORIO,
            env=ambiente,
            capture_output=True,
            text=True,
            timeout=300,
        )
        self.assertEqual(resultado.returncode, 0, resultado.stderr[-3000:])
        self.assertIn("OK", resultado.stderr.splitlines()[-1])


if __name__ == "__main__":
    unittest.main()
