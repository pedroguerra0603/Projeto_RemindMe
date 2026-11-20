"""Casos de uso da Spec 010: calendário de obrigações, cumprimento, evidência e alertas (UC-09).

Toda operação de usuário recebe a sessão de quem a solicita e exige "Gerenciar obrigações" (RB-04; Spec 002). A
verificação automática roda pelo agendador, sem usuário (OPEN-13, OPEN-48), e é a única que chama o canal.
"""

import uuid
from dataclasses import dataclass
from datetime import date, datetime
from typing import Dict, List, Optional, Tuple

from remindme.aplicacao.acesso import Autorizacao
from remindme.aplicacao.auditoria import OperacaoAuditada, RegistroErrosNoLog
from remindme.aplicacao.execucao import Execucao
from remindme.aplicacao.modelos_de_mensagem import mensagem_de_aviso_de_obrigacao, mensagem_de_escalonamento
from remindme.aplicacao.portas import CanalNotificacao, Mensagem, RegistroErros, Relogio, UnidadeDeTrabalho
from remindme.aplicacao.tempo import data_local
from remindme.dominio.erros import OperacaoRecusada
from remindme.dominio.obrigacao import (
    ArquivoDeEvidencia,
    EstadoObrigacao,
    Evidencia,
    Obrigacao,
    Periodicidade,
    TipoAlerta,
    TipoObrigacao,
    responsavel_valido,
)
from remindme.dominio.operacoes import Operacao
from remindme.dominio.usuario import Perfil, Usuario

ROTINA_DE_OBRIGACOES = "verificação de obrigações"
_GERENCIAR = Operacao.GERENCIAR_OBRIGACOES


@dataclass(frozen=True)
class VisaoObrigacao:
    """O que o calendário apresenta de cada obrigação (RF-43)."""

    id: str
    nome: str
    tipo: TipoObrigacao
    periodicidade: Periodicidade
    prazo: date
    estado: EstadoObrigacao
    responsavel_id: str
    responsavel_nome: str
    responsavel_ativo: bool
    exige_evidencia: bool
    aguarda_evidencia: bool


class ServicoObrigacoes:
    def __init__(
        self,
        uow: UnidadeDeTrabalho,
        relogio: Relogio,
        erros: Optional[RegistroErros] = None,
        autorizacao: Optional[Autorizacao] = None,
        canal: Optional[CanalNotificacao] = None,
    ):
        self._relogio = relogio
        self._canal = canal  # injetado pela montagem (ADR-001, ADR-002); sem canal, não há alertas
        self._execucao = Execucao(
            uow, relogio, erros or RegistroErrosNoLog(), autorizacao or Autorizacao(relogio)
        )

    # Operações do usuário

    def cadastrar_obrigacao(
        self,
        sessao: Optional[str],
        nome: object,
        tipo: object,
        periodicidade: object,
        prazo: Optional[date],
        responsavel_id: object,
        exige_evidencia: bool,
    ) -> Obrigacao:
        """RF-40. Prazo passado nasce Atrasada (A7) e é escalada na rodada seguinte do agendador."""
        with self._execucao.operacao("cadastrar obrigação", sessao, _GERENCIAR) as op:
            agora = self._relogio.agora()
            obrigacao = Obrigacao.cadastrar(
                _novo_id(), nome, tipo, periodicidade, prazo, _usuario(op, responsavel_id), exige_evidencia,
                data_local(agora), op.usuario.id, agora,
            )
            _auditar_cadastro(op, obrigacao)
            op.uow.obrigacoes.salvar(obrigacao)
        return obrigacao

    def alterar_prazo(self, sessao: Optional[str], obrigacao_id: str, prazo: Optional[date]) -> Obrigacao:
        """RF-41, A3: vale só para esta ocorrência (OPEN-70)."""
        with self._execucao.operacao("alterar prazo da obrigação", sessao, _GERENCIAR) as op:
            obrigacao = _obter(op, obrigacao_id)
            agora = self._relogio.agora()
            anterior = obrigacao.alterar_prazo(prazo, data_local(agora), op.usuario.id, agora)
            op.registrar(_ref(obrigacao), "prazo", anterior.isoformat(), obrigacao.prazo.isoformat())
            op.uow.obrigacoes.salvar(obrigacao)
        return obrigacao

    def alterar_responsavel(self, sessao: Optional[str], obrigacao_id: str, responsavel_id: object) -> Obrigacao:
        """RF-41, A3."""
        with self._execucao.operacao("alterar responsável da obrigação", sessao, _GERENCIAR) as op:
            obrigacao = _obter(op, obrigacao_id)
            anterior = obrigacao.alterar_responsavel(_usuario(op, responsavel_id), op.usuario.id, self._relogio.agora())
            op.registrar(_ref(obrigacao), "responsavel", anterior, obrigacao.responsavel_id)
            op.uow.obrigacoes.salvar(obrigacao)
        return obrigacao

    def registrar_cumprimento(
        self,
        sessao: Optional[str],
        obrigacao_id: str,
        data: Optional[date],
        arquivo: Optional[ArquivoDeEvidencia] = None,
        descricao: object = None,
    ) -> Obrigacao:
        """RF-45 a RF-47, RB-29. Qualquer usuário autorizado registra (OPEN-69). Cumprida e recorrente: a próxima
        ocorrência nasce na mesma operação (RF-42). Tudo ou nada (RNF-09)."""
        with self._execucao.operacao("registrar cumprimento de obrigação", sessao, _GERENCIAR) as op:
            obrigacao = _obter(op, obrigacao_id)
            agora = self._relogio.agora()
            anterior = obrigacao.estado
            if arquivo is None and isinstance(descricao, str) and descricao.strip():
                mensagem = "Escolha o arquivo da evidência ou deixe a descrição em branco."
                raise OperacaoRecusada(mensagem, {"arquivo": mensagem})
            evidencia = (
                Evidencia.conferir(_novo_id(), arquivo, descricao, agora, op.usuario.id) if arquivo is not None else None
            )
            obrigacao.registrar_cumprimento(data, data_local(agora), op.usuario.id, agora, evidencia)
            op.registrar(_ref(obrigacao), "cumprimento_em", None, obrigacao.cumprimento_em.isoformat())
            if evidencia is not None:
                _guardar_evidencia(op, obrigacao, evidencia, arquivo)
            self._concluir(op, obrigacao, anterior, agora)
        return obrigacao

    def anexar_evidencia(
        self, sessao: Optional[str], obrigacao_id: str, arquivo: ArquivoDeEvidencia, descricao: object
    ) -> Obrigacao:
        """RF-46, A2: com o cumprimento já registrado, o anexo leva a Cumprida e gera a próxima ocorrência."""
        with self._execucao.operacao("anexar evidência de obrigação", sessao, _GERENCIAR) as op:
            obrigacao = _obter(op, obrigacao_id)
            agora = self._relogio.agora()
            anterior = obrigacao.estado
            if not isinstance(arquivo, ArquivoDeEvidencia):
                raise OperacaoRecusada("Anexe o arquivo da evidência.", {"arquivo": "Escolha o arquivo da evidência."})
            evidencia = Evidencia.conferir(_novo_id(), arquivo, descricao, agora, op.usuario.id)
            obrigacao.anexar_evidencia(evidencia, agora)
            _guardar_evidencia(op, obrigacao, evidencia, arquivo)
            self._concluir(op, obrigacao, anterior, agora)
        return obrigacao

    def consultar_calendario(
        self, sessao: Optional[str], estado: Optional[EstadoObrigacao] = None
    ) -> List[VisaoObrigacao]:
        """RF-43, RB-04: o calendário único da empresa, por prazo."""
        with self._execucao.operacao("consultar obrigações", sessao, _GERENCIAR) as op:
            obrigacoes = op.uow.obrigacoes.listar()
            usuarios = {u.id: u for u in op.uow.usuarios.listar()}
        return [
            _visao(o, usuarios.get(o.responsavel_id))
            for o in sorted(obrigacoes, key=lambda o: (o.prazo, o.nome, o.id))
            if estado is None or o.estado is estado
        ]

    def aguardando_evidencia(self, sessao: Optional[str]) -> List[VisaoObrigacao]:
        """RF-77, RB-13: cumprimento registrado sem a evidência exigida, Aguardando Evidência ou Atrasada."""
        return [v for v in self.consultar_calendario(sessao) if v.aguarda_evidencia]

    def obter_obrigacao(self, sessao: Optional[str], obrigacao_id: str) -> Obrigacao:
        """RF-50: a obrigação com o histórico e as evidências."""
        with self._execucao.operacao("consultar obrigações", sessao, _GERENCIAR) as op:
            return _obter(op, obrigacao_id)

    def ocorrencias_da_serie(self, sessao: Optional[str], serie: str) -> List[Obrigacao]:
        """RF-50: as ocorrências geradas a partir do mesmo cadastro, por prazo."""
        with self._execucao.operacao("consultar obrigações", sessao, _GERENCIAR) as op:
            obrigacoes = op.uow.obrigacoes.listar()
        return sorted((o for o in obrigacoes if o.serie == serie), key=lambda o: (o.prazo, o.id))

    def conteudo_da_evidencia(
        self, sessao: Optional[str], obrigacao_id: str, evidencia_id: str
    ) -> Tuple[Evidencia, bytes]:
        """Download da evidência, só para quem gerencia obrigações."""
        with self._execucao.operacao("consultar obrigações", sessao, _GERENCIAR) as op:
            obrigacao = _obter(op, obrigacao_id)
            evidencia = next((e for e in obrigacao.evidencias if e.id == evidencia_id), None)
            conteudo = op.uow.obrigacoes.conteudo_de(evidencia_id) if evidencia is not None else None
        if evidencia is None or conteudo is None:
            raise OperacaoRecusada("Evidência não encontrada.")
        return evidencia, conteudo

    def responsaveis_possiveis(self, sessao: Optional[str]) -> List[Usuario]:
        """OPEN-69: usuários ativos, Dono ou Operador Financeiro, por nome."""
        with self._execucao.operacao("consultar obrigações", sessao, _GERENCIAR) as op:
            usuarios = op.uow.usuarios.listar()
        return sorted((u for u in usuarios if responsavel_valido(u)), key=lambda u: (u.nome, u.id))

    def nomes_dos_usuarios(self, sessao: Optional[str]) -> Dict[str, str]:
        """Os nomes de todos os usuários, ativos ou não, para o histórico e a caixa de saída."""
        with self._execucao.operacao("consultar obrigações", sessao, _GERENCIAR) as op:
            return {u.id: u.nome for u in op.uow.usuarios.listar()}

    # Agendador

    def verificar_obrigacoes_automaticamente(self, hoje: date) -> List[str]:
        """RF-44, RF-48, RF-49, pelo agendador. Uma operação por obrigação: a falha de uma não desfaz as outras.
        Idempotente: cada destinatário recebe no máximo um aviso e um escalonamento por prazo (INV-5)."""
        with self._execucao.automatica("verificar obrigações", ROTINA_DE_OBRIGACOES) as op:
            ids = [o.id for o in op.uow.obrigacoes.listar() if o.estado is not EstadoObrigacao.CUMPRIDA]
        alteradas = []
        for obrigacao_id in ids:
            with self._execucao.automatica("verificar obrigações", ROTINA_DE_OBRIGACOES) as op:
                if self._verificar(op, obrigacao_id, hoje):
                    alteradas.append(obrigacao_id)
        return alteradas

    def _verificar(self, op: OperacaoAuditada, obrigacao_id: str, hoje: date) -> bool:
        obrigacao = _obter(op, obrigacao_id)
        agora = self._relogio.agora()
        anterior = obrigacao.estado
        mudou = obrigacao.marcar_atrasada(hoje, agora)
        if mudou:
            _auditar_estado(op, obrigacao, anterior)
        alertas = 0
        if self._canal is not None:
            usuarios = {u.id: u for u in op.uow.usuarios.listar()}
            donos = [u.id for u in usuarios.values() if u.ativo and u.perfil is Perfil.DONO]
            responsavel = usuarios.get(obrigacao.responsavel_id)
            empresa = op.uow.empresa.obter()
            for destinatario in obrigacao.destinatarios_do_escalonamento(hoje, donos):
                assunto, texto = mensagem_de_escalonamento(empresa, usuarios[destinatario], obrigacao, responsavel, hoje)
                self._alertar(op, obrigacao, TipoAlerta.ESCALONAMENTO, usuarios[destinatario], assunto, texto, agora)
                alertas += 1
            for destinatario in obrigacao.destinatarios_do_aviso(hoje, responsavel, donos):
                assunto, texto = mensagem_de_aviso_de_obrigacao(empresa, usuarios[destinatario], obrigacao, hoje)
                self._alertar(op, obrigacao, TipoAlerta.AVISO, usuarios[destinatario], assunto, texto, agora)
                alertas += 1
        if mudou or alertas:
            op.uow.obrigacoes.salvar(obrigacao)
        return bool(mudou or alertas)

    def _alertar(
        self,
        op: OperacaoAuditada,
        obrigacao: Obrigacao,
        tipo: TipoAlerta,
        usuario: Usuario,
        assunto: str,
        texto: str,
        agora: datetime,
    ) -> None:
        """ADR-002: toda tentativa fica na caixa de saída; exceção do canal conta como falha."""
        try:
            entregue = bool(self._canal.entregar(usuario.email, assunto, texto))
        except Exception:
            entregue = False
        op.uow.mensagens.registrar(
            Mensagem(
                _novo_id(), None, usuario.email, assunto, texto, agora, "enviada" if entregue else "falhou",
                _ref(obrigacao), usuario.id,
            )
        )
        obrigacao.registrar_alerta(tipo, usuario.id, entregue, agora)

    def _concluir(self, op: OperacaoAuditada, obrigacao: Obrigacao, anterior: EstadoObrigacao, agora: datetime) -> None:
        _auditar_estado(op, obrigacao, anterior)
        if obrigacao.estado is EstadoObrigacao.CUMPRIDA:
            proxima = obrigacao.gerar_proxima_ocorrencia(_novo_id(), data_local(agora), agora)
            if proxima is not None:
                _auditar_cadastro(op, proxima)
                op.uow.obrigacoes.salvar(proxima)
        op.uow.obrigacoes.salvar(obrigacao)


def _usuario(op: OperacaoAuditada, usuario_id: object) -> Optional[Usuario]:
    return op.uow.usuarios.obter(usuario_id) if isinstance(usuario_id, str) and usuario_id else None


def _visao(o: Obrigacao, responsavel: Optional[Usuario]) -> VisaoObrigacao:
    return VisaoObrigacao(
        o.id, o.nome, o.tipo, o.periodicidade, o.prazo, o.estado, o.responsavel_id,
        responsavel.nome if responsavel else "—", responsavel_valido(responsavel), o.exige_evidencia,
        o.aguarda_evidencia,
    )


def _guardar_evidencia(op: OperacaoAuditada, obrigacao: Obrigacao, evidencia: Evidencia, arquivo: ArquivoDeEvidencia) -> None:
    op.uow.obrigacoes.guardar_conteudo(evidencia.id, arquivo.conteudo)
    op.registrar(
        f"{_ref(obrigacao)}, evidencia {evidencia.id}", "arquivo", None,
        f"{evidencia.nome_arquivo} ({evidencia.tamanho} bytes)",
    )


def _auditar_cadastro(op: OperacaoAuditada, obrigacao: Obrigacao) -> None:
    ref = _ref(obrigacao)
    op.registrar(ref, "nome", None, obrigacao.nome)
    op.registrar(ref, "tipo", None, obrigacao.tipo.value)
    op.registrar(ref, "periodicidade", None, obrigacao.periodicidade.value)
    op.registrar(ref, "prazo", None, obrigacao.prazo.isoformat())
    op.registrar(ref, "responsavel", None, obrigacao.responsavel_id)
    op.registrar(ref, "exige_evidencia", None, "sim" if obrigacao.exige_evidencia else "não")
    op.registrar(ref, "estado", None, EstadoObrigacao.PENDENTE.value)
    _auditar_estado(op, obrigacao, EstadoObrigacao.PENDENTE)


def _auditar_estado(op: OperacaoAuditada, obrigacao: Obrigacao, anterior: EstadoObrigacao) -> None:
    if obrigacao.estado is not anterior:
        op.registrar(_ref(obrigacao), "estado", anterior.value, obrigacao.estado.value, operacao="mudar estado")


def _obter(op: OperacaoAuditada, obrigacao_id: str) -> Obrigacao:
    obrigacao = op.uow.obrigacoes.obter(obrigacao_id) if isinstance(obrigacao_id, str) else None
    if obrigacao is None:
        raise OperacaoRecusada("Obrigação não encontrada.")
    return obrigacao


def _ref(obrigacao: Obrigacao) -> str:
    return f"obrigacao {obrigacao.id}"


def _novo_id() -> str:
    return uuid.uuid4().hex
