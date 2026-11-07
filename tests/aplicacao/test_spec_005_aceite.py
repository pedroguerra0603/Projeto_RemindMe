"""Critérios de aceitação da Spec 005: envio, decisão do cliente e conversão em título (UC-04, passos 5 a 9)."""

import unittest
from datetime import date, datetime
from decimal import Decimal

from remindme.aplicacao.modelos_de_mensagem import mensagem_de_orcamento
from remindme.aplicacao.servico_mensagens import ServicoMensagens
from remindme.aplicacao.servico_orcamentos import ServicoOrcamentos
from remindme.dominio.cliente import Cliente
from remindme.dominio.empresa import Empresa
from remindme.dominio.erros import OperacaoNegada, OperacaoRecusada
from remindme.dominio.orcamento import EstadoOrcamento
from remindme.dominio.titulo import EstadoTitulo, Titulo
from remindme.dominio.usuario import Perfil, Usuario
from remindme.infraestrutura.canal import CanalSimulado
from remindme.infraestrutura.memoria import RelogioFixo, UnidadeDeTrabalhoEmMemoria
from tests.apoio import CanalQueFalha, CanalQueLanca, ComSessoes

HOJE = date(2026, 11, 7)
OPERADOR = Usuario("operador", "Diego Ramos", Perfil.OPERADOR_FINANCEIRO)
DONO = Usuario("dono", "Carla Menezes", Perfil.DONO)
CONTADOR = Usuario("contador", "Helena Prado", Perfil.CONTADOR)
EMPRESA = Empresa(
    razao_social="Menezes Serviços Ltda", nome_fantasia="Menezes", cnpj="11222333000181",
    telefone="1133224455", email="contato@menezes.com.br", endereco="Rua A, 1",
)
FALHA_NO_CANAL = "O canal de notificação não entregou o orçamento. Ele continua em Rascunho; tente enviar de novo."


class Base(ComSessoes, unittest.TestCase):
    canal = None

    def setUp(self):
        self.uow = UnidadeDeTrabalhoEmMemoria()
        self.uow.clientes.salvar(Cliente("c1", "Padaria Pão Quente Ltda", "11222333000181", "a@padaria.com.br"))
        self.uow.clientes.salvar(Cliente("c2", "Sérgio Tavares", "52998224725", "11987654321"))
        self.uow.empresa.salvar(EMPRESA)
        self.relogio = RelogioFixo(datetime(2026, 11, 7, 12, 0))
        self.servico = ServicoOrcamentos(self.uow, self.relogio, canal=self.canal or CanalSimulado())
        self.mensagens = ServicoMensagens(self.uow, self.relogio)
        self.operador = self.sessao(OPERADOR)
        self.dono = self.sessao(DONO)
        self.contador = self.sessao(CONTADOR)

    def criar(self, cliente="c1"):
        o = self.servico.criar_orcamento(self.operador, cliente, "Boleto")
        return self.servico.incluir_item(self.operador, o.id, "Revisão do forno", Decimal("1"), Decimal("1000.00"))

    def pronto(self, prazo=30):
        """R$ 1.000,00 com 10% de desconto: R$ 900,00 líquidos."""
        o = self.criar()
        self.servico.informar_desconto(self.operador, o.id, Decimal("10"))
        return self.servico.alterar_prazo(self.operador, o.id, prazo)

    def enviado(self, prazo=30):
        return self.servico.enviar_orcamento(self.operador, self.pronto(prazo).id)

    def registros(self, referencia, campo=None):
        return [
            r for r in self.uow.auditoria.registros
            if r.registro_afetado == referencia and (campo is None or r.campo == campo)
        ]

    def estados(self, referencia):
        return [(r.valor_anterior, r.valor_novo) for r in self.registros(referencia, "estado")]


class Spec005(Base):
    def test_CA_01_OPEN_61_prazo_gravado_e_auditado(self):
        o = self.servico.alterar_prazo(self.operador, self.criar().id, 30)
        self.assertEqual(self.uow.orcamentos.obter(o.id).prazo_pagamento_dias, 30)
        (registro,) = self.registros(f"orcamento {o.id}", "prazo para pagamento")
        self.assertEqual((registro.valor_anterior, registro.valor_novo, registro.usuario_id), (None, "30", "operador"))

    def test_CA_02_E6_prazo_invalido_e_recusado_no_campo(self):
        o = self.criar()
        auditoria = len(self.uow.auditoria.registros)
        for invalido in (-1, 366, "2,5"):
            with self.assertRaises(OperacaoRecusada) as ctx:
                self.servico.alterar_prazo(self.operador, o.id, invalido)
            self.assertEqual(list(ctx.exception.campos), ["prazo"])
        self.assertIsNone(self.uow.orcamentos.obter(o.id).prazo_pagamento_dias)
        self.assertEqual(len(self.uow.auditoria.registros), auditoria)

    def test_CA_03_RF_08_envio_passa_a_enviado_e_deixa_mensagem(self):
        o = self.enviado()
        guardado = self.uow.orcamentos.obter(o.id)
        self.assertEqual((guardado.estado, guardado.enviado_em), (EstadoOrcamento.ENVIADO, HOJE))
        (mensagem,) = self.uow.mensagens.listar()
        self.assertEqual(
            (mensagem.cliente_id, mensagem.contato, mensagem.resultado, mensagem.origem, mensagem.enviada_em),
            ("c1", "a@padaria.com.br", "enviada", f"orcamento {o.id}", datetime(2026, 11, 7, 12, 0)),
        )
        self.assertEqual(self.estados(f"orcamento {o.id}")[-1], ("Rascunho", "Enviado"))

    def test_CA_04_E1_orcamento_que_nao_pode_sair_de_rascunho_nao_e_enviado(self):
        sem_prazo = self.criar()
        sem_item = self.servico.criar_orcamento(self.operador, "c1")
        self.servico.alterar_prazo(self.operador, sem_item.id, 30)
        pendente = self.criar()
        self.servico.alterar_prazo(self.operador, pendente.id, 30)
        self.servico.informar_desconto(self.operador, pendente.id, Decimal("50"))
        for o, regra in ((sem_prazo, "OPEN-61"), (sem_item, "RB-24"), (pendente, "RB-15")):
            estado = self.uow.orcamentos.obter(o.id).estado
            with self.assertRaises(OperacaoRecusada) as ctx:
                self.servico.enviar_orcamento(self.operador, o.id)
            self.assertIn(regra, ctx.exception.motivo)
            self.assertIs(self.uow.orcamentos.obter(o.id).estado, estado)
        self.assertEqual(self.uow.mensagens.listar(), [])

    def test_CA_06_RB_27_texto_e_o_do_modelo(self):
        o = self.enviado()
        (mensagem,) = self.uow.mensagens.listar()
        assunto, texto = mensagem_de_orcamento(EMPRESA, self.uow.clientes.obter("c1"), self.uow.orcamentos.obter(o.id))
        self.assertEqual((mensagem.assunto, mensagem.texto), (assunto, texto))
        for trecho in ("Menezes", o.id[:8].upper(), "Revisão do forno", "Valor líquido: R$ 900,00", "30 dias"):
            self.assertIn(trecho, mensagem.texto)

    def test_CA_07_RF_11_RF_19_aprovacao_gera_o_titulo_e_converte(self):
        o = self.enviado()
        o = self.servico.registrar_decisao_do_cliente(self.operador, o.id, True, HOJE)
        self.assertIs(o.estado, EstadoOrcamento.CONVERTIDO)
        (titulo,) = self.uow.titulos.listar()
        self.assertEqual(
            (titulo.cliente_id, titulo.valor, titulo.condicao_pagamento, titulo.vencimento, titulo.origem,
             titulo.orcamento_id, titulo.estado),
            ("c1", Decimal("900.00"), "Boleto", date(2026, 12, 7), "orcamento", o.id, EstadoTitulo.ABERTO),
        )
        self.assertEqual(self.uow.orcamentos.obter(o.id).titulo_id, titulo.id)
        self.assertEqual(
            self.estados(f"orcamento {o.id}")[-2:], [("Enviado", "Aprovado"), ("Aprovado", "Convertido")]
        )
        self.assertEqual(self.estados(f"titulo {titulo.id}"), [(None, "Aberto")])

    def test_CA_08_A2_aprovacao_registrada_com_atraso_gera_titulo_vencido(self):
        self.relogio.momento = datetime(2026, 10, 28, 12, 0)
        o = self.enviado(prazo=5)
        self.relogio.momento = datetime(2026, 11, 7, 12, 0)
        self.servico.registrar_decisao_do_cliente(self.operador, o.id, True, date(2026, 10, 28))
        (titulo,) = self.uow.titulos.listar()
        self.assertEqual((titulo.vencimento, titulo.estado), (date(2026, 11, 2), EstadoTitulo.VENCIDO))
        self.assertEqual(self.estados(f"titulo {titulo.id}"), [(None, "Aberto"), ("Aberto", "Vencido")])

    def test_CA_09_A1_rejeicao_nao_gera_titulo(self):
        o = self.enviado()
        o = self.servico.registrar_decisao_do_cliente(self.operador, o.id, False, HOJE, "Achou caro")
        guardado = self.uow.orcamentos.obter(o.id)
        self.assertEqual(
            (guardado.estado, guardado.decidido_em, guardado.motivo_rejeicao),
            (EstadoOrcamento.REJEITADO, HOJE, "Achou caro"),
        )
        self.assertEqual(self.uow.titulos.listar(), [])
        self.assertEqual(self.estados(f"orcamento {o.id}")[-1], ("Enviado", "Rejeitado"))

    def test_CA_10_E3_decisao_fora_de_enviado_e_recusada(self):
        rascunho = self.pronto()
        rejeitado = self.enviado()
        self.servico.registrar_decisao_do_cliente(self.operador, rejeitado.id, False, HOJE)
        convertido = self.enviado()
        self.servico.registrar_decisao_do_cliente(self.operador, convertido.id, True, HOJE)
        cancelado = self.pronto()
        self.servico.cancelar_orcamento(self.operador, cancelado.id, "Desistiu")
        for o in (rascunho, rejeitado, convertido, cancelado):
            estado = self.uow.orcamentos.obter(o.id).estado
            with self.assertRaises(OperacaoRecusada) as ctx:
                self.servico.registrar_decisao_do_cliente(self.operador, o.id, True, HOJE)
            self.assertIn(estado.value, ctx.exception.motivo)
            self.assertIs(self.uow.orcamentos.obter(o.id).estado, estado)
        self.assertEqual(len(self.uow.titulos.listar()), 1)

    def test_CA_11_E4_data_da_decisao_futura_ou_anterior_ao_envio(self):
        o = self.enviado()
        for data in (date(2026, 11, 8), date(2026, 11, 6)):
            with self.assertRaises(OperacaoRecusada) as ctx:
                self.servico.registrar_decisao_do_cliente(self.operador, o.id, True, data)
            self.assertEqual(list(ctx.exception.campos), ["data"])
        self.assertIs(self.uow.orcamentos.obter(o.id).estado, EstadoOrcamento.ENVIADO)

    def test_CA_12_E5_RNF_09_falha_na_auditoria_desfaz_a_conversao(self):
        o = self.enviado()
        self.uow.auditoria.falhar = True
        with self.assertRaises(RuntimeError):
            self.servico.registrar_decisao_do_cliente(self.operador, o.id, True, HOJE)
        self.uow.auditoria.falhar = False
        self.assertIs(self.uow.orcamentos.obter(o.id).estado, EstadoOrcamento.ENVIADO)
        self.assertEqual(self.uow.titulos.listar(), [])

    def test_CA_13_E7_RB_03_contador_nao_envia_nao_decide_nem_ve_a_caixa(self):
        enviado = self.enviado()
        pronto = self.pronto()
        with self.assertRaises(OperacaoNegada):
            self.servico.enviar_orcamento(self.contador, pronto.id)
        with self.assertRaises(OperacaoNegada):
            self.servico.registrar_decisao_do_cliente(self.contador, enviado.id, True, HOJE)
        with self.assertRaises(OperacaoNegada):
            self.mensagens.consultar(self.contador)
        self.assertIs(self.uow.orcamentos.obter(pronto.id).estado, EstadoOrcamento.RASCUNHO)
        self.assertIs(self.uow.orcamentos.obter(enviado.id).estado, EstadoOrcamento.ENVIADO)

    def test_CA_14_INV_1_segundo_titulo_e_recusado(self):
        o = self.enviado()
        self.servico.registrar_decisao_do_cliente(self.operador, o.id, True, HOJE)
        with self.assertRaises(OperacaoRecusada):
            Titulo.gerar_de_orcamento("outro", self.uow.orcamentos.obter(o.id))
        self.assertEqual(len(self.uow.titulos.listar()), 1)

    def test_caixa_de_saida_do_operador_mostra_a_mais_recente_primeiro(self):
        primeiro = self.enviado()
        self.relogio.momento = datetime(2026, 11, 7, 15, 0)
        segundo = self.enviado()
        self.assertEqual(
            [m.origem for m in self.mensagens.consultar(self.operador)],
            [f"orcamento {segundo.id}", f"orcamento {primeiro.id}"],
        )
        self.assertEqual(len(self.mensagens.consultar(self.dono)), 2)


class SemCanal(Base):
    def test_ADR_001_servico_sem_canal_configurado_nao_envia(self):
        """O canal vem da montagem (inicializacao); a aplicação não escolhe a infraestrutura."""
        servico = ServicoOrcamentos(self.uow, self.relogio)
        o = self.pronto()
        with self.assertRaises(RuntimeError):
            servico.enviar_orcamento(self.operador, o.id)
        self.assertIs(self.uow.orcamentos.obter(o.id).estado, EstadoOrcamento.RASCUNHO)
        self.assertEqual(self.uow.mensagens.listar(), [])


class FalhaNoCanal(Base):
    canal = CanalQueFalha()

    def test_CA_05_E2_canal_que_falha_deixa_rascunho_e_mensagem_que_falhou(self):
        o = self.pronto()
        with self.assertRaises(OperacaoRecusada) as ctx:
            self.servico.enviar_orcamento(self.operador, o.id)
        self.assertEqual(ctx.exception.motivo, FALHA_NO_CANAL)
        self.assertIs(self.uow.orcamentos.obter(o.id).estado, EstadoOrcamento.RASCUNHO)
        (mensagem,) = self.uow.mensagens.listar()
        self.assertEqual((mensagem.resultado, mensagem.origem), ("falhou", f"orcamento {o.id}"))


class CanalQueLancaExcecao(Base):
    canal = CanalQueLanca()

    def test_foco_4_canal_que_lanca_excecao_conta_como_falha(self):
        o = self.pronto()
        with self.assertRaises(OperacaoRecusada) as ctx:
            self.servico.enviar_orcamento(self.operador, o.id)
        self.assertEqual(ctx.exception.motivo, FALHA_NO_CANAL)
        self.assertIs(self.uow.orcamentos.obter(o.id).estado, EstadoOrcamento.RASCUNHO)
        self.assertEqual([m.resultado for m in self.uow.mensagens.listar()], ["falhou"])


if __name__ == "__main__":
    unittest.main()
