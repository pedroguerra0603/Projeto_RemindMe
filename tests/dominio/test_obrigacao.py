"""Regras da obrigação (Spec 010), só com o domínio: estados, cumprimento, evidência, recorrência e alertas."""

import unittest
from datetime import date, datetime, timedelta

from remindme.dominio.erros import OperacaoRecusada
from remindme.dominio.obrigacao import (
    ArquivoDeEvidencia,
    EstadoObrigacao,
    Evidencia,
    Obrigacao,
    Periodicidade,
    TipoEvento,
    TipoObrigacao,
)
from remindme.dominio.usuario import Perfil, Usuario

HOJE = date(2026, 11, 20)
AGORA = datetime(2026, 11, 20, 9, 0)
DONO = Usuario("dono", "Carla Menezes", Perfil.DONO, "carla@demo.example")
OPERADOR = Usuario("operador", "Diego Ramos", Perfil.OPERADOR_FINANCEIRO, "diego@demo.example")
CONTADOR = Usuario("contador", "Helena Prado", Perfil.CONTADOR, "helena@demo.example")
INATIVO = Usuario("inativo", "Ex Operador", Perfil.OPERADOR_FINANCEIRO, "ex@demo.example", ativo=False)

PDF = b"%PDF-1.4\n%teste\n"
PNG = b"\x89PNG\r\n\x1a\n" + b"\x00" * 16
JPG = b"\xff\xd8\xff\xe0" + b"\x00" * 16


def obrigacao(
    prazo=date(2026, 12, 20),
    exige_evidencia=False,
    periodicidade="Mensal",
    responsavel=OPERADOR,
    id="o1",
) -> Obrigacao:
    return Obrigacao.cadastrar(
        id, "DAS", "Fiscal", periodicidade, prazo, responsavel, exige_evidencia, HOJE, OPERADOR.id, AGORA
    )


def evidencia(nome="das.pdf", conteudo=PDF, descricao="DAS pago, protocolo 123", id="e1") -> Evidencia:
    return Evidencia.conferir(id, ArquivoDeEvidencia(nome, conteudo), descricao, AGORA, OPERADOR.id)


def tipos(o: Obrigacao):
    return [e.tipo for e in o.historico]


class Cadastro(unittest.TestCase):
    def test_RF_40_cadastro_nasce_pendente_com_os_dados_e_o_evento(self):
        o = obrigacao(exige_evidencia=True)
        self.assertEqual(
            (o.nome, o.tipo, o.periodicidade, o.prazo, o.responsavel_id, o.exige_evidencia, o.estado),
            ("DAS", TipoObrigacao.FISCAL, Periodicidade.MENSAL, date(2026, 12, 20), OPERADOR.id, True, EstadoObrigacao.PENDENTE),
        )
        self.assertEqual((o.dia_base, o.prazo_referencia, o.serie), (20, date(2026, 12, 20), "o1"))
        self.assertIs(o.historico[0].tipo, TipoEvento.CADASTRADA)
        self.assertEqual((o.historico[0].quando, o.historico[0].usuario_id), (AGORA, OPERADOR.id))

    def test_estados_tipos_e_periodicidades_sao_os_da_spec(self):
        self.assertEqual([e.value for e in EstadoObrigacao], ["Pendente", "Aguardando Evidência", "Atrasada", "Cumprida"])
        self.assertEqual([t.value for t in TipoObrigacao], ["Fiscal", "Trabalhista", "Contratual", "Outra"])
        self.assertEqual(
            [(p.value, p.meses) for p in Periodicidade],
            [("Única", 0), ("Mensal", 1), ("Trimestral", 3), ("Semestral", 6), ("Anual", 12)],
        )

    def test_cadastro_aceita_os_enums(self):
        o = Obrigacao.cadastrar(
            "o1", "FGTS", TipoObrigacao.TRABALHISTA, Periodicidade.UNICA, HOJE, DONO, False, HOJE, DONO.id, AGORA
        )
        self.assertEqual((o.tipo, o.periodicidade), (TipoObrigacao.TRABALHISTA, Periodicidade.UNICA))

    def test_E1_cadastro_recusa_todos_os_campos_de_uma_vez(self):
        with self.assertRaises(OperacaoRecusada) as ctx:
            Obrigacao.cadastrar("o1", " ", "Imposto", "Semanal", None, CONTADOR, False, HOJE, OPERADOR.id, AGORA)
        self.assertEqual(set(ctx.exception.campos), {"nome", "tipo", "periodicidade", "prazo", "responsavel"})
        self.assertEqual(ctx.exception.campos["nome"], "Informe o nome da obrigação.")
        self.assertEqual(ctx.exception.campos["tipo"], "Escolha o tipo: Fiscal, Trabalhista, Contratual ou Outra.")
        self.assertEqual(
            ctx.exception.campos["periodicidade"],
            "Escolha a periodicidade: Única, Mensal, Trimestral, Semestral ou Anual.",
        )
        self.assertEqual(ctx.exception.campos["prazo"], "Informe o prazo.")
        self.assertEqual(
            ctx.exception.campos["responsavel"], "Escolha um usuário ativo, Dono ou Operador Financeiro (OPEN-64)."
        )

    def test_E1_responsavel_inativo_ausente_e_nome_longo_sao_recusados(self):
        for responsavel in (INATIVO, None):
            with self.subTest(responsavel=responsavel), self.assertRaises(OperacaoRecusada) as ctx:
                obrigacao(responsavel=responsavel)
            self.assertEqual(set(ctx.exception.campos), {"responsavel"})
        with self.assertRaises(OperacaoRecusada) as ctx:
            Obrigacao.cadastrar("o1", "x" * 121, "Fiscal", "Mensal", HOJE, OPERADOR, False, HOJE, OPERADOR.id, AGORA)
        self.assertEqual(ctx.exception.campos, {"nome": "O nome tem no máximo 120 caracteres."})

    def test_nome_com_espacos_e_aparado(self):
        o = Obrigacao.cadastrar("o1", "  DAS   mensal ", "Fiscal", "Mensal", HOJE, OPERADOR, False, HOJE, OPERADOR.id, AGORA)
        self.assertEqual(o.nome, "DAS mensal")

    def test_A7_cadastro_com_prazo_passado_nasce_atrasada(self):
        o = obrigacao(prazo=HOJE - timedelta(days=1))
        self.assertIs(o.estado, EstadoObrigacao.ATRASADA)
        self.assertEqual(tipos(o), [TipoEvento.CADASTRADA, TipoEvento.ATRASADA])


class Cumprimento(unittest.TestCase):
    def test_RF_45_A1_cumprimento_sem_exigencia_fica_cumprida(self):
        o = obrigacao()
        o.registrar_cumprimento(HOJE, HOJE, OPERADOR.id, AGORA)
        self.assertIs(o.estado, EstadoObrigacao.CUMPRIDA)
        self.assertEqual(tipos(o)[-2:], [TipoEvento.CUMPRIMENTO_REGISTRADO, TipoEvento.CUMPRIDA])

    def test_RF_47_INV_3_cumprida_guarda_data_e_usuario(self):
        o = obrigacao()
        o.registrar_cumprimento(HOJE - timedelta(days=2), HOJE, DONO.id, AGORA)
        self.assertEqual((o.cumprimento_em, o.cumprimento_por), (HOJE - timedelta(days=2), DONO.id))

    def test_RB_29_cumprimento_com_evidencia_fica_cumprida(self):
        o = obrigacao(exige_evidencia=True)
        o.registrar_cumprimento(HOJE, HOJE, OPERADOR.id, AGORA, evidencia())
        self.assertIs(o.estado, EstadoObrigacao.CUMPRIDA)
        self.assertEqual([e.id for e in o.evidencias], ["e1"])
        self.assertIn(TipoEvento.EVIDENCIA_ANEXADA, tipos(o))

    def test_A1_obrigacao_sem_exigencia_aceita_anexo_opcional(self):
        o = obrigacao()
        o.registrar_cumprimento(HOJE, HOJE, OPERADOR.id, AGORA, evidencia())
        self.assertEqual((o.estado, len(o.evidencias)), (EstadoObrigacao.CUMPRIDA, 1))

    def test_A2_RB_13_cumprimento_sem_a_evidencia_exigida_aguarda(self):
        o = obrigacao(exige_evidencia=True)
        o.registrar_cumprimento(HOJE, HOJE, OPERADOR.id, AGORA)
        self.assertIs(o.estado, EstadoObrigacao.AGUARDANDO_EVIDENCIA)
        self.assertTrue(o.aguarda_evidencia)
        o.anexar_evidencia(evidencia(), AGORA)
        self.assertIs(o.estado, EstadoObrigacao.CUMPRIDA)
        self.assertFalse(o.aguarda_evidencia)
        self.assertEqual(tipos(o)[-2:], [TipoEvento.EVIDENCIA_ANEXADA, TipoEvento.CUMPRIDA])

    def test_anexo_antes_do_cumprimento_nao_cumpre(self):
        o = obrigacao(exige_evidencia=True)
        o.anexar_evidencia(evidencia(), AGORA)
        self.assertIs(o.estado, EstadoObrigacao.PENDENTE)
        o.registrar_cumprimento(HOJE, HOJE, OPERADOR.id, AGORA)
        self.assertIs(o.estado, EstadoObrigacao.CUMPRIDA)

    def test_A4_atrasada_sem_evidencia_continua_atrasada_ate_o_anexo(self):
        o = obrigacao(prazo=HOJE - timedelta(days=3), exige_evidencia=True)
        o.registrar_cumprimento(HOJE, HOJE, OPERADOR.id, AGORA)
        self.assertIs(o.estado, EstadoObrigacao.ATRASADA)
        self.assertTrue(o.aguarda_evidencia)
        o.anexar_evidencia(evidencia(), AGORA)
        self.assertIs(o.estado, EstadoObrigacao.CUMPRIDA)

    def test_A4_atrasada_com_cumprimento_completo_fica_cumprida(self):
        o = obrigacao(prazo=HOJE - timedelta(days=3))
        o.registrar_cumprimento(HOJE, HOJE, OPERADOR.id, AGORA)
        self.assertIs(o.estado, EstadoObrigacao.CUMPRIDA)

    def test_A5_aguardando_evidencia_que_estoura_vira_atrasada_mantendo_o_cumprimento(self):
        o = obrigacao(prazo=HOJE, exige_evidencia=True)
        o.registrar_cumprimento(HOJE, HOJE, OPERADOR.id, AGORA)
        self.assertTrue(o.marcar_atrasada(HOJE + timedelta(days=1), AGORA))
        self.assertIs(o.estado, EstadoObrigacao.ATRASADA)
        self.assertEqual((o.cumprimento_em, o.cumprimento_por), (HOJE, OPERADOR.id))
        o.anexar_evidencia(evidencia(), AGORA)
        self.assertIs(o.estado, EstadoObrigacao.CUMPRIDA)

    def test_RF_48_marcar_atrasada_so_depois_do_prazo(self):
        no_prazo = obrigacao(prazo=HOJE)
        self.assertFalse(no_prazo.marcar_atrasada(HOJE, AGORA))
        self.assertIs(no_prazo.estado, EstadoObrigacao.PENDENTE)
        estourada = obrigacao(prazo=date(2026, 11, 25))
        self.assertTrue(estourada.marcar_atrasada(date(2026, 11, 26), AGORA))
        self.assertIs(estourada.estado, EstadoObrigacao.ATRASADA)
        self.assertFalse(estourada.marcar_atrasada(date(2026, 11, 27), AGORA))
        self.assertEqual(tipos(estourada).count(TipoEvento.ATRASADA), 1)
        cumprida = obrigacao(prazo=HOJE)
        cumprida.registrar_cumprimento(HOJE, HOJE, OPERADOR.id, AGORA)
        self.assertFalse(cumprida.marcar_atrasada(HOJE + timedelta(days=5), AGORA))
        self.assertIs(cumprida.estado, EstadoObrigacao.CUMPRIDA)

    def test_E3_operacoes_fora_do_estado(self):
        cumprida = obrigacao()
        cumprida.registrar_cumprimento(HOJE, HOJE, OPERADOR.id, AGORA)
        atrasada = obrigacao(prazo=HOJE - timedelta(days=1))
        casos = [
            ("Obrigação Cumprida não aceita cumprimento.", lambda: cumprida.registrar_cumprimento(HOJE, HOJE, OPERADOR.id, AGORA)),
            ("Obrigação Cumprida não aceita evidência.", lambda: cumprida.anexar_evidencia(evidencia(), AGORA)),
            ("Obrigação Cumprida não aceita alteração de prazo.", lambda: cumprida.alterar_prazo(HOJE, HOJE, OPERADOR.id, AGORA)),
            ("Obrigação Atrasada não aceita alteração de prazo.", lambda: atrasada.alterar_prazo(HOJE, HOJE, OPERADOR.id, AGORA)),
            (
                "Obrigação Cumprida não aceita alteração de responsável.",
                lambda: cumprida.alterar_responsavel(DONO, OPERADOR.id, AGORA),
            ),
        ]
        for motivo, acao in casos:
            with self.subTest(motivo=motivo), self.assertRaises(OperacaoRecusada) as ctx:
                acao()
            self.assertEqual(ctx.exception.motivo, motivo)
        self.assertEqual(len(cumprida.evidencias), 0)

    def test_E4_data_do_cumprimento(self):
        for data, motivo in (
            (None, "Informe a data do cumprimento."),
            (HOJE + timedelta(days=1), "A data do cumprimento não pode ser posterior a hoje."),
        ):
            o = obrigacao()
            with self.subTest(data=data), self.assertRaises(OperacaoRecusada) as ctx:
                o.registrar_cumprimento(data, HOJE, OPERADOR.id, AGORA)
            self.assertEqual(ctx.exception.campos, {"data": motivo})
            self.assertIs(o.estado, EstadoObrigacao.PENDENTE)

    def test_E3_cumprimento_ja_registrado_nao_se_registra_de_novo(self):
        o = obrigacao(exige_evidencia=True)
        o.registrar_cumprimento(HOJE, HOJE, OPERADOR.id, AGORA)
        with self.assertRaises(OperacaoRecusada):
            o.registrar_cumprimento(HOJE, HOJE, DONO.id, AGORA)
        self.assertEqual(o.cumprimento_por, OPERADOR.id)


class Alteracoes(unittest.TestCase):
    def test_A3_RF_41_alteracoes_entram_no_historico_com_anterior_e_novo(self):
        o = obrigacao()
        self.assertEqual(o.alterar_prazo(date(2027, 1, 5), HOJE, DONO.id, AGORA), date(2026, 12, 20))
        self.assertEqual(o.prazo, date(2027, 1, 5))
        self.assertEqual((o.prazo_referencia, o.dia_base), (date(2026, 12, 20), 20))
        evento = o.historico[-1]
        self.assertEqual((evento.tipo, evento.usuario_id, evento.detalhe), (TipoEvento.PRAZO_ALTERADO, DONO.id, "20/12/2026 → 05/01/2027"))
        self.assertEqual(o.alterar_responsavel(DONO, OPERADOR.id, AGORA), OPERADOR.id)
        self.assertEqual(o.responsavel_id, DONO.id)
        self.assertEqual((o.historico[-1].tipo, o.historico[-1].detalhe), (TipoEvento.RESPONSAVEL_ALTERADO, "operador → dono"))

    def test_A3_prazo_de_ontem_e_recusado(self):
        o = obrigacao()
        with self.assertRaises(OperacaoRecusada) as ctx:
            o.alterar_prazo(HOJE - timedelta(days=1), HOJE, OPERADOR.id, AGORA)
        self.assertEqual(ctx.exception.campos, {"prazo": "O novo prazo não pode ser anterior a hoje."})
        with self.assertRaises(OperacaoRecusada) as ctx:
            o.alterar_prazo(None, HOJE, OPERADOR.id, AGORA)
        self.assertEqual(ctx.exception.campos, {"prazo": "Informe o prazo."})
        self.assertEqual(o.prazo, date(2026, 12, 20))

    def test_A3_prazo_muda_em_aguardando_evidencia_e_responsavel_em_atrasada(self):
        aguardando = obrigacao(exige_evidencia=True)
        aguardando.registrar_cumprimento(HOJE, HOJE, OPERADOR.id, AGORA)
        aguardando.alterar_prazo(date(2026, 12, 30), HOJE, OPERADOR.id, AGORA)
        self.assertEqual(aguardando.prazo, date(2026, 12, 30))
        atrasada = obrigacao(prazo=HOJE - timedelta(days=1))
        atrasada.alterar_responsavel(DONO, OPERADOR.id, AGORA)
        self.assertEqual(atrasada.responsavel_id, DONO.id)

    def test_A3_responsavel_invalido_e_recusado(self):
        o = obrigacao()
        for responsavel in (CONTADOR, INATIVO, None):
            with self.subTest(responsavel=responsavel), self.assertRaises(OperacaoRecusada) as ctx:
                o.alterar_responsavel(responsavel, OPERADOR.id, AGORA)
            self.assertIn("responsavel", ctx.exception.campos)
        self.assertEqual(o.responsavel_id, OPERADOR.id)


class EvidenciaConferida(unittest.TestCase):
    def test_OPEN_63_evidencia_conferida_pelo_conteudo(self):
        for nome, conteudo, tipo in (
            ("das.pdf", PDF, "application/pdf"),
            ("recibo.png", PNG, "image/png"),
            ("foto.jpg", JPG, "image/jpeg"),
            ("FOTO.JPEG", JPG, "image/jpeg"),
        ):
            with self.subTest(nome=nome):
                e = evidencia(nome, conteudo)
                self.assertEqual((e.nome_arquivo, e.tipo_arquivo, e.tamanho), (nome, tipo, len(conteudo)))
                self.assertEqual((e.descricao, e.anexada_em, e.usuario_id), ("DAS pago, protocolo 123", AGORA, OPERADOR.id))

    def test_E2_arquivo_invalido_e_recusado_no_campo_arquivo(self):
        grande = b"%PDF-" + b"0" * (5 * 1024 * 1024 + 1 - 5)
        for nome, conteudo, motivo in (
            ("das.pdf", b"", "O arquivo está vazio."),
            ("das.pdf", grande, "O arquivo tem no máximo 5 MB."),
            ("das.txt", b"texto", "Anexe um PDF, PNG ou JPG (OPEN-63)."),
            ("das.pdf", b"isto e texto", "Anexe um PDF, PNG ou JPG (OPEN-63)."),
            ("das.pdf", PNG, "Anexe um PDF, PNG ou JPG (OPEN-63)."),
            ("das", PDF, "Anexe um PDF, PNG ou JPG (OPEN-63)."),
        ):
            with self.subTest(nome=nome, inicio=conteudo[:8]), self.assertRaises(OperacaoRecusada) as ctx:
                evidencia(nome, conteudo)
            self.assertEqual(ctx.exception.campos, {"arquivo": motivo})

    def test_E2_arquivo_de_5_mb_exatos_e_aceito(self):
        exato = b"%PDF-" + b"0" * (5 * 1024 * 1024 - 5)
        self.assertEqual(evidencia(conteudo=exato).tamanho, 5 * 1024 * 1024)

    def test_E2_descricao_vazia_ou_longa_e_recusada(self):
        for descricao, motivo in (
            ("  ", "Descreva a evidência."),
            (None, "Descreva a evidência."),
            ("x" * 201, "A descrição tem no máximo 200 caracteres."),
        ):
            with self.subTest(descricao=descricao), self.assertRaises(OperacaoRecusada) as ctx:
                evidencia(descricao=descricao)
            self.assertEqual(ctx.exception.campos, {"descricao": motivo})

    def test_foco_1_nome_do_arquivo_fica_so_com_o_nome_base(self):
        self.assertEqual(evidencia(nome="C:\\fakepath\\DAS março.pdf").nome_arquivo, "DAS março.pdf")
        self.assertEqual(evidencia(nome='../../a"b.pdf').nome_arquivo, "ab.pdf")
        self.assertEqual(evidencia(nome="a\x00\nb.pdf").nome_arquivo, "ab.pdf")


if __name__ == "__main__":
    unittest.main()
