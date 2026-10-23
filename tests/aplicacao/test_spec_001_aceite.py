"""Critérios de aceitação da Spec 001: fundação em camadas e auditoria de operações."""

import ast
import dataclasses
import unittest
from datetime import date, datetime, timedelta
from decimal import Decimal
from pathlib import Path

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
from tests.apoio import ComSessoes
from tests.arquitetura.test_camadas import PERMITIDAS, RAIZ, importacoes

HOJE = date(2026, 10, 3)
ONTEM = HOJE - timedelta(days=1)
FUTURO = HOJE + timedelta(days=30)
AGORA = datetime(2026, 10, 3, 10, 0)
DONO = Usuario("dono", "Dono", Perfil.DONO)
OPERADOR = Usuario("operador", "Operador", Perfil.OPERADOR_FINANCEIRO)


class RepositorioQueFalha(RepositorioTitulosEmMemoria):
    def __init__(self):
        super().__init__()
        self.falhar = False

    def salvar(self, titulo):
        if self.falhar:
            raise RuntimeError("Falha simulada na gravação do título.")
        super().salvar(titulo)


class ClientesQueFalham:
    def existe(self, cliente_id):
        raise ConnectionError("Consulta de clientes indisponível.")


class Spec001(ComSessoes, unittest.TestCase):
    def setUp(self):
        self.titulos = RepositorioQueFalha()
        self.auditoria = AuditoriaEmMemoria()
        self.erros = RegistroErrosEmMemoria()
        self.relogio = RelogioFixo(AGORA)
        self.uow = UnidadeDeTrabalhoEmMemoria(self.titulos, self.auditoria)
        self.servico = ServicoTitulos(self.uow, ClientesEmMemoria({"c1"}), self.relogio, self.erros)

    def novo_titulo(self, valor="100.00", vencimento=FUTURO):
        return self.servico.cadastrar_titulo(self.sessao(OPERADOR), "c1", Decimal(valor), vencimento)

    def fotografia(self):
        return (
            {i: (t.estado, t.saldo, len(t.pagamentos)) for i, t in self.titulos.dados.items()},
            self.auditoria.registros,
        )

    def test_CA_01_cadastro_de_titulo_e_auditado_com_o_estado_inicial(self):
        t = self.novo_titulo()
        [registro] = self.auditoria.registros
        self.assertEqual(registro.usuario_id, OPERADOR.id)
        self.assertEqual(registro.data_hora, AGORA)
        self.assertEqual(registro.operacao, "cadastrar título")
        self.assertEqual(registro.registro_afetado, f"titulo {t.id}")
        self.assertEqual((registro.campo, registro.valor_anterior, registro.valor_novo), ("estado", None, "Aberto"))
        self.assertFalse(registro.automatica)

    def test_CA_02_pagamento_gera_registro_do_pagamento_e_da_mudanca_de_estado(self):
        t = self.novo_titulo()
        antes = len(self.auditoria.registros)
        t = self.servico.registrar_pagamento(self.sessao(OPERADOR), t.id, Decimal("100.00"), HOJE)
        pagamento, estado = self.auditoria.registros[antes:]
        self.assertEqual(pagamento.registro_afetado, f"titulo {t.id}, pagamento {t.pagamentos[0].id}")
        self.assertEqual((pagamento.campo, pagamento.valor_anterior, pagamento.valor_novo), ("valor", None, "100.00"))
        self.assertEqual(estado.registro_afetado, f"titulo {t.id}")
        self.assertEqual((estado.campo, estado.valor_anterior, estado.valor_novo), ("estado", "Aberto", "Baixado"))

    def test_CA_03_RB_01_estorno_audita_o_pagamento_com_motivo_e_o_estado_do_titulo(self):
        t = self.novo_titulo()
        t = self.servico.registrar_pagamento(self.sessao(OPERADOR), t.id, Decimal("100.00"), HOJE)
        pagamento_id = t.pagamentos[0].id
        antes = len(self.auditoria.registros)
        self.servico.estornar_pagamento(self.sessao(DONO), t.id, pagamento_id, "cheque devolvido", HOJE)
        pagamento, estado = self.auditoria.registros[antes:]
        self.assertEqual(pagamento.registro_afetado, f"titulo {t.id}, pagamento {pagamento_id}")
        self.assertEqual((pagamento.campo, pagamento.valor_anterior, pagamento.valor_novo), ("estornado", "não", "sim"))
        self.assertEqual(pagamento.motivo, "cheque devolvido")
        self.assertEqual(pagamento.usuario_id, DONO.id)
        self.assertEqual((estado.registro_afetado, estado.campo), (f"titulo {t.id}", "estado"))
        self.assertEqual((estado.valor_anterior, estado.valor_novo), ("Baixado", "Aberto"))

    def test_CA_04_operacao_recusada_nao_grava_auditoria(self):
        t = self.novo_titulo()
        t = self.servico.registrar_pagamento(self.sessao(OPERADOR), t.id, Decimal("100.00"), HOJE)
        antes = self.auditoria.registros
        with self.assertRaises(OperacaoRecusada):
            self.servico.registrar_pagamento(self.sessao(OPERADOR), t.id, Decimal("10.00"), HOJE)
        self.assertEqual(self.auditoria.registros, antes)
        self.assertEqual(self.erros.registros, [])

    def test_CA_05_falha_na_auditoria_desfaz_o_pagamento(self):
        t = self.novo_titulo()
        antes = self.fotografia()
        self.auditoria.falhar = True
        with self.assertRaises(RuntimeError):
            self.servico.registrar_pagamento(self.sessao(OPERADOR), t.id, Decimal("100.00"), HOJE)
        self.assertEqual(self.fotografia(), antes)
        self.assertIs(self.titulos.obter(t.id).estado, EstadoTitulo.ABERTO)

    def test_CA_06_falha_na_gravacao_do_titulo_desfaz_a_auditoria_ja_gravada(self):
        t = self.novo_titulo()
        antes = self.fotografia()
        self.titulos.falhar = True
        with self.assertRaises(RuntimeError):
            self.servico.registrar_pagamento(self.sessao(OPERADOR), t.id, Decimal("100.00"), HOJE)
        self.assertEqual(self.fotografia(), antes)

    def test_CA_07_RB_30_registro_gravado_nao_e_alterado(self):
        self.novo_titulo()
        lido = self.auditoria.registros[0]
        for campo in (f.name for f in dataclasses.fields(RegistroAuditoria)):
            with self.subTest(campo=campo):
                with self.assertRaises(dataclasses.FrozenInstanceError):
                    setattr(lido, campo, "adulterado")
        with self.assertRaises(AttributeError):
            self.auditoria.registros = []
        self.assertEqual(self.auditoria.registros, [lido])

    def test_CA_08_RB_30_nao_ha_exclusao_de_registro(self):
        self.novo_titulo()
        lidos = self.auditoria.registros
        lidos.clear()
        del self.auditoria.registros[0]
        self.assertEqual(len(self.auditoria.registros), 1)
        publicos = {n for n in dir(self.auditoria) if not n.startswith("_")}
        self.assertFalse({n for n in publicos if any(p in n for p in ("excluir", "apagar", "remover", "alterar"))})

    def test_CA_09_verificacao_de_vencimento_sem_usuario_e_automatica(self):
        t = self.novo_titulo(vencimento=ONTEM)
        self.assertEqual(self.servico.verificar_vencimentos_automaticamente(HOJE), [t.id])
        self.assertIs(self.titulos.obter(t.id).estado, EstadoTitulo.VENCIDO)
        registro = self.auditoria.registros[-1]
        self.assertIsNone(registro.usuario_id)
        self.assertTrue(registro.automatica)
        self.assertEqual(registro.rotina, "verificação de vencimento")
        self.assertEqual((registro.campo, registro.valor_anterior, registro.valor_novo), ("estado", "Aberto", "Vencido"))

    def test_CA_10_erro_nao_tratado_e_registrado_desfeito_e_repassado(self):
        servico = ServicoTitulos(self.uow, ClientesQueFalham(), self.relogio, self.erros)
        antes = self.fotografia()
        with self.assertRaises(ConnectionError) as ctx:
            servico.cadastrar_titulo(self.sessao(OPERADOR), "c1", Decimal("100.00"), FUTURO)
        self.assertEqual(self.fotografia(), antes)
        [erro] = self.erros.registros
        self.assertEqual((erro.data_hora, erro.operacao, erro.usuario_id), (AGORA, "cadastrar título", OPERADOR.id))
        self.assertTrue(erro.correlacao)
        self.assertIn(erro.correlacao, " ".join(ctx.exception.__notes__))

    def test_CA_11_registros_sao_lidos_na_ordem_de_gravacao(self):
        a = self.novo_titulo()
        self.relogio.momento += timedelta(minutes=1)
        b = self.novo_titulo()
        self.assertEqual(
            [(r.registro_afetado, r.data_hora.minute) for r in self.auditoria.registros],
            [(f"titulo {a.id}", 0), (f"titulo {b.id}", 1)],
        )

    def test_CA_12_dominio_e_aplicacao_nao_importam_camadas_externas(self):
        for camada in ("dominio", "aplicacao"):
            for arquivo in (RAIZ / camada).rglob("*.py"):
                for modulo in importacoes(arquivo):
                    partes = modulo.split(".")
                    if partes[0] == "remindme":
                        with self.subTest(arquivo=arquivo.name, importa=modulo):
                            self.assertIn(partes[1], PERMITIDAS[camada])

    def test_CA_13_codigo_nao_le_variavel_de_ambiente_nem_credencial(self):
        """A suíte inteira também é executada sem nenhuma variável de credencial (seção 8 da spec)."""
        for arquivo in RAIZ.rglob("*.py"):
            texto = arquivo.read_text(encoding="utf-8")
            with self.subTest(arquivo=arquivo.name):
                self.assertNotIn("environ", texto)
                self.assertNotIn("getenv", texto)
        fluxos = Path(__file__).resolve().parents[2] / ".github" / "workflows"
        for fluxo in fluxos.glob("*.yml"):
            with self.subTest(fluxo=fluxo.name):
                self.assertNotIn("secrets.", fluxo.read_text(encoding="utf-8"))


class InvarianteDoRegistro(unittest.TestCase):
    """INV-3: data e hora, operação, registro afetado e usuário, salvo em operação automática."""

    def test_INV_3_registro_sem_usuario_so_existe_se_automatico_e_com_rotina(self):
        for argumentos in (
            dict(usuario_id=None),
            dict(usuario_id=None, automatica=True),
            dict(usuario_id="u", automatica=True, rotina="verificação de vencimento"),
        ):
            with self.subTest(**argumentos):
                with self.assertRaises(ValueError):
                    RegistroAuditoria(data_hora=AGORA, operacao="op", registro_afetado="titulo t", **argumentos)

    def test_INV_3_registro_exige_data_operacao_e_registro_afetado(self):
        for argumentos in (
            dict(data_hora=None, operacao="op", registro_afetado="titulo t"),
            dict(data_hora=AGORA, operacao="", registro_afetado="titulo t"),
            dict(data_hora=AGORA, operacao="op", registro_afetado=""),
        ):
            with self.subTest(**argumentos):
                with self.assertRaises(ValueError):
                    RegistroAuditoria(usuario_id="u", **argumentos)

    def test_INV_3_registro_automatico_valido(self):
        registro = RegistroAuditoria(
            None, AGORA, "verificar vencimentos", "titulo t", automatica=True, rotina="verificação de vencimento"
        )
        self.assertIsNone(registro.usuario_id)


class PontoUnico(unittest.TestCase):
    def test_INV_5_somente_a_aplicacao_auditoria_cria_registro_de_auditoria(self):
        for arquivo in (RAIZ / "aplicacao").rglob("*.py"):
            chamadas = [
                no for no in ast.walk(ast.parse(arquivo.read_text(encoding="utf-8")))
                if isinstance(no, ast.Call) and getattr(no.func, "id", None) == "RegistroAuditoria"
            ]
            with self.subTest(arquivo=arquivo.name):
                self.assertEqual(len(chamadas), 1 if arquivo.name == "auditoria.py" else 0)


if __name__ == "__main__":
    unittest.main()
