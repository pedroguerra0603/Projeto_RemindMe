"""Critérios de aceitação da Spec 010: calendário de obrigações (UC-09)."""

import unittest
from dataclasses import replace
from datetime import date, datetime

from remindme.aplicacao.modelos_de_mensagem import mensagem_de_aviso_de_obrigacao
from remindme.aplicacao.servico_obrigacoes import ServicoObrigacoes
from remindme.aplicacao.servico_titulos import ServicoTitulos
from remindme.dominio.erros import OperacaoNegada, OperacaoRecusada
from remindme.dominio.obrigacao import ArquivoDeEvidencia, EstadoObrigacao, TipoEvento
from remindme.dominio.usuario import Perfil, Usuario
from remindme.entradas.agendador import AgendadorDeVencimentos
from remindme.infraestrutura.canal import CanalSimulado
from remindme.infraestrutura.memoria import RelogioFixo, UnidadeDeTrabalhoEmMemoria
from tests.apoio import CanalQueFalha, ComSessoes

HOJE = date(2026, 11, 20)
DONO = Usuario("dono", "Carla Menezes", Perfil.DONO, "carla@demo.example")
DONO2 = Usuario("dono2", "Paulo Menezes", Perfil.DONO, "paulo@demo.example")
DONO_INATIVO = Usuario("dono3", "Ex Sócia", Perfil.DONO, "ex@demo.example", ativo=False)
OPERADOR = Usuario("operador", "Diego Ramos", Perfil.OPERADOR_FINANCEIRO, "diego@demo.example")
OPERADOR2 = Usuario("operador2", "Lia Souza", Perfil.OPERADOR_FINANCEIRO, "lia@demo.example")
CONTADOR = Usuario("contador", "Helena Prado", Perfil.CONTADOR, "helena@demo.example")

PDF = b"%PDF-1.4\n%teste\n"


def no_dia(dia: date) -> datetime:
    return datetime(dia.year, dia.month, dia.day, 9, 0)


class Base(ComSessoes, unittest.TestCase):
    def setUp(self):
        self.uow = UnidadeDeTrabalhoEmMemoria()
        self.relogio = RelogioFixo(no_dia(HOJE))
        self.canal = CanalSimulado()
        self.servico = ServicoObrigacoes(self.uow, self.relogio, canal=self.canal)
        self.operador = self.sessao(OPERADOR)
        self.dono = self.sessao(DONO)
        self.contador = self.sessao(CONTADOR)
        for usuario in (DONO2, DONO_INATIVO, OPERADOR2):
            self.uow.usuarios.salvar(usuario)

    def em(self, dia: date) -> None:
        self.relogio.momento = no_dia(dia)

    def cadastrar(self, prazo=date(2026, 12, 20), periodicidade="Mensal", exige=False, responsavel=OPERADOR, nome="DAS"):
        return self.servico.cadastrar_obrigacao(self.operador, nome, "Fiscal", periodicidade, prazo, responsavel.id, exige)

    def cumprir(self, obrigacao, data=None, arquivo=None, descricao=None):
        return self.servico.registrar_cumprimento(self.operador, obrigacao.id, data or self.relogio.agora().date(), arquivo, descricao)

    def agendador(self, servico=None):
        titulos = ServicoTitulos(self.uow, self.uow.clientes, self.relogio)
        return AgendadorDeVencimentos(titulos, self.relogio, obrigacoes=servico or self.servico)

    def enviadas(self, usuario_id=None):
        return [
            m for m in self.uow.mensagens.listar()
            if m.resultado == "enviada" and (usuario_id is None or m.usuario_id == usuario_id)
        ]

    def obter(self, obrigacao):
        return self.uow.obrigacoes.obter(obrigacao.id)

    def auditoria_de(self, referencia):
        return [r for r in self.uow.auditoria.registros if r.registro_afetado == referencia]


class Cadastro(Base):
    def test_CA_01_RF_40_cadastro_pendente_com_historico_e_auditoria(self):
        o = self.cadastrar(exige=True)
        gravada = self.obter(o)
        self.assertEqual(
            (gravada.nome, gravada.tipo.value, gravada.periodicidade.value, gravada.prazo, gravada.responsavel_id),
            ("DAS", "Fiscal", "Mensal", date(2026, 12, 20), OPERADOR.id),
        )
        self.assertEqual((gravada.exige_evidencia, gravada.estado, gravada.dia_base), (True, EstadoObrigacao.PENDENTE, 20))
        self.assertEqual([e.tipo for e in gravada.historico], [TipoEvento.CADASTRADA])
        campos = {(r.campo, r.valor_anterior, r.valor_novo, r.usuario_id) for r in self.auditoria_de(f"obrigacao {o.id}")}
        self.assertEqual(
            campos,
            {
                ("nome", None, "DAS", OPERADOR.id),
                ("tipo", None, "Fiscal", OPERADOR.id),
                ("periodicidade", None, "Mensal", OPERADOR.id),
                ("prazo", None, "2026-12-20", OPERADOR.id),
                ("responsavel", None, OPERADOR.id, OPERADOR.id),
                ("exige_evidencia", None, "sim", OPERADOR.id),
                ("estado", None, "Pendente", OPERADOR.id),
            },
        )

    def test_CA_02_E1_dados_invalidos_sao_recusados_no_campo(self):
        casos = [
            ("nome", dict(nome=" ")),
            ("tipo", dict(tipo="Imposto")),
            ("periodicidade", dict(periodicidade="Semanal")),
            ("prazo", dict(prazo=None)),
            ("responsavel", dict(responsavel=CONTADOR.id)),
            ("responsavel", dict(responsavel=DONO_INATIVO.id)),
            ("responsavel", dict(responsavel="inexistente")),
        ]
        for campo, troca in casos:
            dados = dict(nome="DAS", tipo="Fiscal", periodicidade="Mensal", prazo=date(2026, 12, 20), responsavel=OPERADOR.id)
            dados.update(troca)
            with self.subTest(troca=troca), self.assertRaises(OperacaoRecusada) as ctx:
                self.servico.cadastrar_obrigacao(
                    self.operador, dados["nome"], dados["tipo"], dados["periodicidade"], dados["prazo"], dados["responsavel"], False
                )
            self.assertEqual(set(ctx.exception.campos), {campo})
        self.assertEqual(self.uow.obrigacoes.listar(), [])

    def test_CA_03_RF_43_RB_04_calendario_ordenado_por_prazo(self):
        for nome, prazo in (("FGTS", date(2026, 12, 5)), ("DAS", date(2026, 11, 25)), ("IPVA", date(2027, 1, 1))):
            self.cadastrar(prazo=prazo, nome=nome)
        calendario = self.servico.consultar_calendario(self.dono)
        self.assertEqual([(v.nome, v.prazo) for v in calendario], [("DAS", date(2026, 11, 25)), ("FGTS", date(2026, 12, 5)), ("IPVA", date(2027, 1, 1))])
        self.assertEqual(calendario[0].responsavel_nome, OPERADOR.nome)


class Avisos(Base):
    def test_CA_04_RF_44_RB_07_aviso_unico_com_o_texto_do_modelo(self):
        o = self.cadastrar(prazo=date(2026, 11, 27))
        self.agendador().executar_uma_vez()
        self.agendador().executar_uma_vez()
        enviadas = self.enviadas()
        self.assertEqual([(m.usuario_id, m.cliente_id, m.contato, m.origem) for m in enviadas], [(OPERADOR.id, None, OPERADOR.email, f"obrigacao {o.id}")])
        assunto, texto = mensagem_de_aviso_de_obrigacao(None, OPERADOR, self.obter(o), HOJE)
        self.assertEqual((enviadas[0].assunto, enviadas[0].texto), (assunto, texto))
        self.assertEqual([e.tipo for e in self.obter(o).historico].count(TipoEvento.AVISO_ENVIADO), 1)

    def test_CA_05_RB_07_fora_da_janela_nao_avisa(self):
        self.cadastrar(prazo=date(2026, 11, 28))
        self.agendador().executar_uma_vez()
        self.assertEqual(self.uow.mensagens.listar(), [])

    def test_CA_15_A6_responsavel_inativo_avisa_os_donos(self):
        o = self.cadastrar(prazo=date(2026, 11, 23), responsavel=OPERADOR2)
        self.uow.usuarios.salvar(replace(OPERADOR2, ativo=False))
        self.agendador().executar_uma_vez()
        self.assertEqual(sorted(m.usuario_id for m in self.enviadas()), [DONO.id, DONO2.id])
        visao = next(v for v in self.servico.consultar_calendario(self.dono) if v.id == o.id)
        self.assertFalse(visao.responsavel_ativo)

    def test_CA_23_ADR_002_canal_que_falha_e_tentado_de_novo(self):
        o = self.cadastrar(prazo=date(2026, 11, 27))
        falho = ServicoObrigacoes(self.uow, self.relogio, canal=CanalQueFalha())
        self.agendador(falho).executar_uma_vez()
        self.assertEqual([m.resultado for m in self.uow.mensagens.listar()], ["falhou"])
        self.assertIn(TipoEvento.AVISO_FALHOU, [e.tipo for e in self.obter(o).historico])
        self.agendador().executar_uma_vez()
        self.agendador().executar_uma_vez()
        self.assertEqual([m.resultado for m in self.uow.mensagens.listar()], ["falhou", "enviada"])
        self.assertEqual(len(self.enviadas(OPERADOR.id)), 1)

    def test_ADR_001_servico_sem_canal_nao_envia_alertas_mas_marca_atrasada(self):
        self.em(date(2026, 11, 18))
        o = self.cadastrar(prazo=date(2026, 11, 19))
        self.em(HOJE)
        sem_canal = ServicoObrigacoes(self.uow, self.relogio)
        self.agendador(sem_canal).executar_uma_vez()
        self.assertIs(self.obter(o).estado, EstadoObrigacao.ATRASADA)
        self.assertEqual(self.uow.mensagens.listar(), [])


class Cumprimento(Base):
    def test_CA_06_RF_45_RF_47_cumprimento_sem_exigencia(self):
        o = self.cadastrar(periodicidade="Única")
        self.cumprir(o)
        gravada = self.obter(o)
        self.assertEqual((gravada.estado, gravada.cumprimento_em, gravada.cumprimento_por), (EstadoObrigacao.CUMPRIDA, HOJE, OPERADOR.id))
        self.assertEqual([e.tipo for e in gravada.historico][-2:], [TipoEvento.CUMPRIMENTO_REGISTRADO, TipoEvento.CUMPRIDA])
        estados = [(r.valor_anterior, r.valor_novo) for r in self.auditoria_de(f"obrigacao {o.id}") if r.campo == "estado"]
        self.assertEqual(estados[-1], ("Pendente", "Cumprida"))

    def test_CA_07_RF_46_RB_29_cumprimento_com_pdf(self):
        o = self.cadastrar(exige=True, periodicidade="Única")
        self.cumprir(o, arquivo=ArquivoDeEvidencia("das.pdf", PDF), descricao="DAS pago, protocolo 123")
        gravada = self.obter(o)
        self.assertIs(gravada.estado, EstadoObrigacao.CUMPRIDA)
        evidencia, conteudo = self.servico.conteudo_da_evidencia(self.operador, o.id, gravada.evidencias[0].id)
        self.assertEqual((evidencia.nome_arquivo, evidencia.descricao, conteudo), ("das.pdf", "DAS pago, protocolo 123", PDF))
        self.assertTrue(self.auditoria_de(f"obrigacao {o.id}, evidencia {evidencia.id}"))

    def test_CA_08_A2_RF_77_aguardando_evidencia_ate_o_anexo(self):
        o = self.cadastrar(exige=True, periodicidade="Única")
        self.cumprir(o)
        self.assertIs(self.obter(o).estado, EstadoObrigacao.AGUARDANDO_EVIDENCIA)
        self.assertEqual([v.id for v in self.servico.aguardando_evidencia(self.operador)], [o.id])
        self.servico.anexar_evidencia(self.operador, o.id, ArquivoDeEvidencia("das.pdf", PDF), "Comprovante")
        self.assertIs(self.obter(o).estado, EstadoObrigacao.CUMPRIDA)
        self.assertEqual(self.servico.aguardando_evidencia(self.operador), [])

    def test_CA_09_E2_evidencia_invalida_e_recusada_no_campo(self):
        o = self.cadastrar(exige=True)
        casos = [
            ("arquivo", ArquivoDeEvidencia("das.pdf", b""), "DAS"),
            ("arquivo", ArquivoDeEvidencia("das.pdf", b"%PDF-" + b"0" * (5 * 1024 * 1024 - 4)), "DAS"),
            ("arquivo", ArquivoDeEvidencia("das.txt", b"texto"), "DAS"),
            ("arquivo", ArquivoDeEvidencia("das.pdf", b"isto e texto"), "DAS"),
            ("descricao", ArquivoDeEvidencia("das.pdf", PDF), " "),
        ]
        for campo, arquivo, descricao in casos:
            with self.subTest(arquivo=arquivo.nome, tamanho=len(arquivo.conteudo)), self.assertRaises(OperacaoRecusada) as ctx:
                self.cumprir(o, arquivo=arquivo, descricao=descricao)
            self.assertIn(campo, ctx.exception.campos)
        gravada = self.obter(o)
        self.assertEqual((gravada.estado, gravada.evidencias, gravada.cumprimento_em), (EstadoObrigacao.PENDENTE, [], None))

    def test_descricao_sem_arquivo_e_recusada_no_campo_arquivo(self):
        for exige in (True, False):
            o = self.cadastrar(exige=exige)
            with self.subTest(exige=exige), self.assertRaises(OperacaoRecusada) as ctx:
                self.cumprir(o, descricao="Guia paga")
            self.assertEqual(ctx.exception.campos, {"arquivo": "Escolha o arquivo da evidência ou deixe a descrição em branco."})
            self.assertEqual((self.obter(o).estado, self.obter(o).cumprimento_em), (EstadoObrigacao.PENDENTE, None))

    def test_CA_19_E4_data_de_amanha_e_recusada(self):
        o = self.cadastrar()
        with self.assertRaises(OperacaoRecusada) as ctx:
            self.cumprir(o, data=date(2026, 11, 21))
        self.assertIn("data", ctx.exception.campos)

    def test_CA_20_E5_RNF_09_falha_na_auditoria_desfaz_o_cumprimento(self):
        o = self.cadastrar(exige=True)
        registrar = self.uow.auditoria.registrar

        def falhar_no_cumprimento(registro):
            if registro.campo == "estado" and registro.valor_novo == "Cumprida":
                raise RuntimeError("Falha simulada na auditoria do cumprimento.")
            registrar(registro)

        self.uow.auditoria.registrar = falhar_no_cumprimento
        try:
            with self.assertRaises(RuntimeError):
                self.cumprir(o, arquivo=ArquivoDeEvidencia("das.pdf", PDF), descricao="DAS")
        finally:
            self.uow.auditoria.registrar = registrar
        gravada = self.obter(o)
        self.assertEqual((gravada.estado, gravada.evidencias, gravada.proxima_id), (EstadoObrigacao.PENDENTE, [], None))
        self.assertEqual(len(self.uow.obrigacoes.listar()), 1)
        self.assertEqual(self.uow.obrigacoes.conteudos, {})


class Recorrencia(Base):
    def test_CA_10_RF_42_mensal_no_fim_do_mes(self):
        o = self.cadastrar(prazo=date(2027, 1, 31))
        self.cumprir(o)
        fevereiro = self.uow.obrigacoes.obter(self.obter(o).proxima_id)
        self.cumprir(fevereiro)
        marco = self.uow.obrigacoes.obter(self.obter(fevereiro).proxima_id)
        self.assertEqual([(x.prazo, x.serie) for x in (fevereiro, marco)], [(date(2027, 2, 28), o.id), (date(2027, 3, 31), o.id)])
        self.assertIs(marco.estado, EstadoObrigacao.PENDENTE)
        self.assertTrue(self.auditoria_de(f"obrigacao {marco.id}"))

    def test_CA_11_RF_42_prazo_conta_do_anterior_e_unica_nao_gera(self):
        o = self.cadastrar(prazo=date(2026, 10, 20))
        self.assertIs(o.estado, EstadoObrigacao.ATRASADA)
        self.cumprir(o)
        proxima = self.uow.obrigacoes.obter(self.obter(o).proxima_id)
        self.assertEqual((proxima.prazo, proxima.estado), (date(2026, 11, 20), EstadoObrigacao.PENDENTE))
        unica = self.cadastrar(periodicidade="Única")
        self.cumprir(unica)
        self.assertIsNone(self.obter(unica).proxima_id)
        self.assertEqual(len(self.uow.obrigacoes.listar()), 3)

    def test_CA_24_A3_alteracao_de_prazo_vale_so_para_a_ocorrencia(self):
        o = self.cadastrar(prazo=date(2026, 12, 20))
        self.servico.alterar_prazo(self.operador, o.id, date(2027, 1, 5))
        self.cumprir(o)
        self.assertEqual(self.uow.obrigacoes.obter(self.obter(o).proxima_id).prazo, date(2027, 1, 20))


class AtrasoEEscalonamento(Base):
    def test_CA_12_RF_48_atrasada_no_dia_seguinte_ao_prazo(self):
        self.em(date(2026, 11, 18))
        ontem = self.cadastrar(prazo=date(2026, 11, 19))
        hoje = self.cadastrar(prazo=HOJE)
        self.em(HOJE)
        self.agendador().executar_uma_vez()
        self.assertEqual((self.obter(ontem).estado, self.obter(hoje).estado), (EstadoObrigacao.ATRASADA, EstadoObrigacao.PENDENTE))
        estados = [(r.valor_anterior, r.valor_novo, r.rotina) for r in self.auditoria_de(f"obrigacao {ontem.id}") if r.campo == "estado"]
        self.assertEqual(estados[-1], ("Pendente", "Atrasada", "verificação de obrigações"))

    def test_CA_13_A5_aguardando_evidencia_que_estoura(self):
        self.em(date(2026, 11, 18))
        o = self.cadastrar(prazo=date(2026, 11, 19), exige=True)
        self.cumprir(o)
        self.em(HOJE)
        self.agendador().executar_uma_vez()
        gravada = self.obter(o)
        self.assertEqual((gravada.estado, gravada.cumprimento_em), (EstadoObrigacao.ATRASADA, date(2026, 11, 18)))
        self.servico.anexar_evidencia(self.operador, o.id, ArquivoDeEvidencia("das.pdf", PDF), "Comprovante")
        self.assertIs(self.obter(o).estado, EstadoObrigacao.CUMPRIDA)

    def test_CA_14_RF_49_RB_16_escalonamento_unico_aos_donos_ativos(self):
        self.em(date(2026, 11, 18))
        o = self.cadastrar(prazo=date(2026, 11, 19))
        self.em(HOJE)
        self.agendador().executar_uma_vez()
        self.agendador().executar_uma_vez()
        self.assertEqual(sorted(m.usuario_id for m in self.enviadas()), [DONO.id, DONO2.id])
        self.assertTrue(all(m.assunto == "Obrigação atrasada: DAS" for m in self.enviadas()))
        escaladas = [e for e in self.obter(o).historico if e.tipo is TipoEvento.ESCALADA]
        self.assertEqual(sorted(e.destinatario_id for e in escaladas), [DONO.id, DONO2.id])


class Alteracoes(Base):
    def test_CA_16_RF_41_alteracao_de_prazo_e_responsavel_no_historico(self):
        o = self.cadastrar()
        self.servico.alterar_prazo(self.operador, o.id, date(2026, 12, 10))
        self.servico.alterar_responsavel(self.operador, o.id, DONO.id)
        gravada = self.obter(o)
        self.assertEqual([(e.tipo, e.detalhe) for e in gravada.historico][-2:], [
            (TipoEvento.PRAZO_ALTERADO, "20/12/2026 → 10/12/2026"),
            (TipoEvento.RESPONSAVEL_ALTERADO, f"{OPERADOR.id} → {DONO.id}"),
        ])
        alteracoes = [(r.campo, r.valor_anterior, r.valor_novo) for r in self.auditoria_de(f"obrigacao {o.id}") if r.valor_anterior]
        self.assertEqual(alteracoes, [("prazo", "2026-12-20", "2026-12-10"), ("responsavel", OPERADOR.id, DONO.id)])

    def test_CA_17_E3_alteracoes_fora_do_estado_sao_recusadas(self):
        atrasada = self.cadastrar(prazo=date(2026, 11, 1))
        cumprida = self.cadastrar(periodicidade="Única")
        self.cumprir(cumprida)
        pendente = self.cadastrar()
        tentativas = [
            lambda: self.servico.alterar_prazo(self.operador, atrasada.id, date(2026, 12, 1)),
            lambda: self.servico.alterar_prazo(self.operador, cumprida.id, date(2026, 12, 1)),
            lambda: self.servico.alterar_responsavel(self.operador, cumprida.id, DONO.id),
            lambda: self.cumprir(cumprida),
            lambda: self.servico.anexar_evidencia(self.operador, cumprida.id, ArquivoDeEvidencia("d.pdf", PDF), "D"),
            lambda: self.servico.alterar_prazo(self.operador, pendente.id, date(2026, 11, 19)),
        ]
        antes = {o.id: o for o in self.uow.obrigacoes.listar()}
        for i, tentativa in enumerate(tentativas):
            with self.subTest(i=i), self.assertRaises(OperacaoRecusada):
                tentativa()
        self.assertEqual({o.id: o for o in self.uow.obrigacoes.listar()}, antes)

    def test_CA_18_RF_50_historico_e_ocorrencias_da_serie(self):
        self.em(date(2026, 11, 13))
        o = self.cadastrar(prazo=date(2026, 11, 19))
        self.agendador().executar_uma_vez()
        self.servico.alterar_responsavel(self.operador, o.id, OPERADOR2.id)
        self.em(HOJE)
        self.agendador().executar_uma_vez()
        self.cumprir(o)
        gravada = self.servico.obter_obrigacao(self.dono, o.id)
        self.assertEqual(
            [e.tipo for e in gravada.historico],
            [
                TipoEvento.CADASTRADA, TipoEvento.AVISO_ENVIADO, TipoEvento.RESPONSAVEL_ALTERADO, TipoEvento.ATRASADA,
                TipoEvento.ESCALADA, TipoEvento.ESCALADA, TipoEvento.CUMPRIMENTO_REGISTRADO, TipoEvento.CUMPRIDA,
            ],
        )
        serie = self.servico.ocorrencias_da_serie(self.dono, gravada.serie)
        self.assertEqual([(x.id, x.prazo) for x in serie], [(o.id, date(2026, 11, 19)), (gravada.proxima_id, date(2026, 12, 19))])


class Acesso(Base):
    def test_CA_21_E6_RB_03_RB_04_contador_nao_acessa_obrigacoes(self):
        o = self.cadastrar(exige=True)
        self.cumprir(o, arquivo=ArquivoDeEvidencia("das.pdf", PDF), descricao="DAS")
        evidencia_id = self.obter(o).evidencias[0].id
        antes = self.uow.obrigacoes.listar()
        tentativas = [
            lambda: self.servico.consultar_calendario(self.contador),
            lambda: self.servico.cadastrar_obrigacao(self.contador, "X", "Fiscal", "Única", HOJE, OPERADOR.id, False),
            lambda: self.servico.alterar_prazo(self.contador, o.id, date(2027, 1, 1)),
            lambda: self.servico.registrar_cumprimento(self.contador, o.id, HOJE),
            lambda: self.servico.conteudo_da_evidencia(self.contador, o.id, evidencia_id),
            lambda: self.servico.obter_obrigacao(self.contador, o.id),
            lambda: self.servico.aguardando_evidencia(self.contador),
        ]
        for i, tentativa in enumerate(tentativas):
            with self.subTest(i=i), self.assertRaises(OperacaoNegada):
                tentativa()
        self.assertEqual(self.uow.obrigacoes.listar(), antes)

    def test_OPEN_64_qualquer_usuario_autorizado_registra_o_cumprimento(self):
        o = self.cadastrar(periodicidade="Única")
        self.servico.registrar_cumprimento(self.dono, o.id, HOJE)
        self.assertEqual(self.obter(o).cumprimento_por, DONO.id)

    def test_OPEN_64_responsaveis_possiveis_sao_donos_e_operadores_ativos(self):
        nomes = [u.nome for u in self.servico.responsaveis_possiveis(self.operador)]
        self.assertEqual(nomes, sorted([DONO.nome, DONO2.nome, OPERADOR.nome, OPERADOR2.nome]))


if __name__ == "__main__":
    unittest.main()
