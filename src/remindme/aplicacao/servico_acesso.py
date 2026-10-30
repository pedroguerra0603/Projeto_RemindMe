"""Casos de uso da Spec 002: entrar, sair, administrar usuários e permissões (UC-01, UC-02)."""

import secrets
import uuid
from dataclasses import dataclass, replace
from datetime import datetime
from typing import Dict, FrozenSet, List, Optional

from remindme.aplicacao.acesso import Autorizacao, chave_da_sessao, nova_sessao
from remindme.aplicacao.auditoria import OperacaoAuditada, RegistroErrosNoLog
from remindme.aplicacao.execucao import Execucao
from remindme.aplicacao.portas import CifradorDeSenha, RegistroErros, Relogio, Sessao, UnidadeDeTrabalho
from remindme.aplicacao.senhas import CifradorScrypt, motivo_da_senha
from remindme.dominio.erros import OperacaoRecusada, recusar_campos
from remindme.dominio.operacoes import Operacao
from remindme.dominio.permissoes import Celula
from remindme.dominio.usuario import Perfil, Usuario, normalizar_email

CREDENCIAIS_INVALIDAS = "E-mail ou senha incorretos."
USUARIO_INATIVO = "Usuário inativo ou aguardando ativação. Procure o Administrador."
ROTINA_DE_INSTALACAO = "instalação"
ROTINA_DE_CRIAR_CONTA = "criar conta pela entrada"


@dataclass(frozen=True)
class SessaoAberta:
    """RF-65: a sessão criada e as operações que o perfil pode executar."""

    identificador: str
    protecao: str
    usuario: Usuario
    operacoes: FrozenSet[Operacao]


@dataclass(frozen=True)
class SessaoAtiva:
    usuario: Usuario
    operacoes: FrozenSet[Operacao]
    protecao: str
    expira_em: datetime


@dataclass(frozen=True)
class LinhaDaMatriz:
    operacao: Operacao
    celulas: Dict[Perfil, Celula]


class ServicoAcesso:
    def __init__(
        self,
        uow: UnidadeDeTrabalho,
        relogio: Relogio,
        erros: Optional[RegistroErros] = None,
        cifrador: Optional[CifradorDeSenha] = None,
        autorizacao: Optional[Autorizacao] = None,
    ):
        self._relogio = relogio
        self._cifrador = cifrador or CifradorScrypt()
        self._autorizacao = autorizacao or Autorizacao(relogio)
        self._execucao = Execucao(uow, relogio, erros or RegistroErrosNoLog(), self._autorizacao)
        self._hash_ficticio: Optional[str] = None

    # UC-01

    def entrar(self, email: object, senha: object) -> SessaoAberta:
        """RF-65. E1 e E2. Entrar é auditado, sem a senha e sem o identificador da sessão (OPEN-47)."""
        with self._execucao.do_usuario("entrar no sistema", lambda uow: self._autenticar(uow, email, senha)) as op:
            identificador, sessao = nova_sessao(op.usuario.id, self._relogio.agora())
            op.uow.sessoes.salvar(sessao)
            op.registrar(_ref(op.usuario), "sessão", None, "aberta")
            operacoes = op.uow.permissoes.obter().operacoes(op.usuario.perfil)
        return SessaoAberta(identificador, sessao.protecao, op.usuario, operacoes)

    def sair(self, sessao: Optional[str]) -> None:
        with self._execucao.do_usuario("sair do sistema", lambda uow: self._autorizacao.sessao(uow, sessao)[1]) as op:
            op.uow.sessoes.remover(chave_da_sessao(sessao))
            op.registrar(_ref(op.usuario), "sessão", "aberta", "encerrada")

    def sessao_ativa(self, sessao: Optional[str]) -> SessaoAtiva:
        """A sessão vale para o usuário ativo, com as permissões atuais do perfil (A2, A4)."""
        encontrada: List[Sessao] = []

        def identificar(uow: UnidadeDeTrabalho) -> Usuario:
            dados, usuario = self._autorizacao.sessao(uow, sessao)
            encontrada.append(dados)
            return usuario

        with self._execucao.do_usuario("consultar sessão", identificar) as op:
            operacoes = op.uow.permissoes.obter().operacoes(op.usuario.perfil)
        return SessaoAtiva(op.usuario, operacoes, encontrada[0].protecao, encontrada[0].expira_em)

    def exigir(self, sessao: Optional[str], operacao: Operacao) -> None:
        """RF-67: confere a permissão antes de a interface mostrar o formulário de uma operação."""
        with self._execucao.operacao("conferir permissão", sessao, operacao):
            pass

    # UC-02

    def cadastrar_usuario(
        self, sessao: Optional[str], nome: object, email: object, perfil: object, senha_provisoria: object
    ) -> Usuario:
        """A1, RF-02. E6, E7. A senha provisória (OPEN-35) fica só como hash (RNF-04, INV-3)."""
        with self._execucao.operacao("cadastrar usuário", sessao, Operacao.ADMINISTRAR_USUARIOS) as op:
            return self._cadastrar(op, nome, email, perfil, senha_provisoria)

    def criar_primeiro_administrador(self, nome: object, email: object, senha: object) -> Usuario:
        """OPEN-39: na instalação, só quando ainda não há Administrador ativo."""
        with self._execucao.automatica("cadastrar usuário", ROTINA_DE_INSTALACAO) as op:
            if any(u.ativo and u.perfil is Perfil.ADMINISTRADOR for u in op.uow.usuarios.listar()):
                raise OperacaoRecusada("Já existe um Administrador ativo. Os demais usuários são cadastrados por ele.")
            return self._cadastrar(op, nome, email, Perfil.ADMINISTRADOR, senha)

    def criar_conta(self, nome: object, email: object, perfil: object, senha: object) -> Usuario:
        """OPEN-55: qualquer pessoa pede uma conta pela tela de entrada. Ela nasce inativa, e só entra depois
        que um Administrador a ativa; o perfil Administrador não pode ser pedido assim."""
        with self._execucao.automatica("criar conta", ROTINA_DE_CRIAR_CONTA) as op:
            recusa_do_perfil = "O perfil Administrador é dado só por outro Administrador." if perfil is Perfil.ADMINISTRADOR else ""
            return self._cadastrar(op, nome, email, perfil, senha, ativo=False, recusa_do_perfil=recusa_do_perfil)

    def ativar_usuario(self, sessao: Optional[str], usuario_id: str) -> Usuario:
        """OPEN-55: libera a entrada de quem criou a conta (ou volta a liberar um inativado)."""
        with self._execucao.operacao("ativar usuário", sessao, Operacao.ADMINISTRAR_USUARIOS) as op:
            ativo = self._usuario(op.uow, usuario_id).ativado()
            op.uow.usuarios.salvar(ativo)
            op.registrar(_ref(ativo), "ativo", "não", "sim")
        return ativo

    def alterar_perfil(self, sessao: Optional[str], usuario_id: str, perfil: object) -> Usuario:
        """A2: a operação seguinte do usuário já usa o novo perfil. RF-05: auditoria do anterior e do novo."""
        with self._execucao.operacao("alterar perfil", sessao, Operacao.ADMINISTRAR_USUARIOS) as op:
            usuario = self._usuario(op.uow, usuario_id)
            alterado = usuario.com_perfil(perfil)
            if usuario.perfil is Perfil.ADMINISTRADOR:
                _exigir_outro_administrador(op.uow, usuario)
            op.uow.usuarios.salvar(alterado)
            op.registrar(_ref(usuario), "perfil", usuario.perfil.value, alterado.perfil.value)
        return alterado

    def inativar_usuario(self, sessao: Optional[str], usuario_id: str) -> Usuario:
        """A3: as sessões do usuário deixam de valer, e o histórico é preservado."""
        with self._execucao.operacao("inativar usuário", sessao, Operacao.ADMINISTRAR_USUARIOS) as op:
            usuario = self._usuario(op.uow, usuario_id)
            inativo = usuario.inativado()
            if usuario.perfil is Perfil.ADMINISTRADOR:
                _exigir_outro_administrador(op.uow, usuario)
            op.uow.usuarios.salvar(inativo)
            op.uow.sessoes.remover_do_usuario(usuario.id)
            op.registrar(_ref(usuario), "ativo", "sim", "não")
        return inativo

    def listar_usuarios(self, sessao: Optional[str]) -> List[Usuario]:
        with self._execucao.operacao("consultar usuários", sessao, Operacao.ADMINISTRAR_USUARIOS) as op:
            return sorted(op.uow.usuarios.listar(), key=lambda u: (u.nome.casefold(), u.email))

    def obter_usuario(self, sessao: Optional[str], usuario_id: str) -> Usuario:
        with self._execucao.operacao("consultar usuários", sessao, Operacao.ADMINISTRAR_USUARIOS) as op:
            return self._usuario(op.uow, usuario_id)

    def matriz(self, sessao: Optional[str]) -> List[LinhaDaMatriz]:
        with self._execucao.operacao("consultar permissões", sessao, Operacao.ADMINISTRAR_USUARIOS) as op:
            matriz = op.uow.permissoes.obter()
        return [LinhaDaMatriz(o, {p: matriz.celula(o, p) for p in Perfil}) for o in Operacao]

    def conceder_permissao(self, sessao: Optional[str], perfil: object, operacao: object) -> None:
        """A4, RF-03: vale na operação seguinte, inclusive com a sessão já aberta. E5: célula fixada não muda."""
        with self._execucao.operacao("conceder permissão", sessao, Operacao.ADMINISTRAR_USUARIOS) as op:
            perfil, operacao = _celula(perfil, operacao)
            op.uow.permissoes.salvar(op.uow.permissoes.obter().conceder(perfil, operacao))
            op.registrar("permissões", f"{perfil.value}: {operacao.value}", "não", "sim")

    def retirar_permissao(self, sessao: Optional[str], perfil: object, operacao: object) -> None:
        with self._execucao.operacao("retirar permissão", sessao, Operacao.ADMINISTRAR_USUARIOS) as op:
            perfil, operacao = _celula(perfil, operacao)
            op.uow.permissoes.salvar(op.uow.permissoes.obter().retirar(perfil, operacao))
            op.registrar("permissões", f"{perfil.value}: {operacao.value}", "sim", "não")

    def _cadastrar(
        self, op: OperacaoAuditada, nome: object, email: object, perfil: object, senha: object, ativo: bool = True,
        recusa_do_perfil: str = "",
    ) -> Usuario:
        campos: Dict[str, str] = {}
        usuario: Optional[Usuario] = None
        try:
            usuario = Usuario.cadastrar(uuid.uuid4().hex, nome, email, perfil)
        except OperacaoRecusada as recusa:
            campos.update(recusa.campos)
        email_normalizado = normalizar_email(email)
        if "email" not in campos and op.uow.usuarios.obter_por_email(email_normalizado) is not None:
            campos["email"] = "Já existe um usuário com este e-mail."
        motivo = motivo_da_senha(senha)
        if motivo:
            campos["senha"] = motivo
        if recusa_do_perfil:
            campos["perfil"] = recusa_do_perfil
        recusar_campos(campos)
        if not ativo:
            usuario = replace(usuario, ativo=False)
        op.uow.usuarios.salvar(usuario)
        op.uow.usuarios.guardar_hash(usuario.id, self._cifrador.gerar(senha))
        for campo, valor in (
            ("nome", usuario.nome),
            ("email", usuario.email),
            ("perfil", usuario.perfil.value),
            ("ativo", "sim" if ativo else "não"),
        ):
            op.registrar(_ref(usuario), campo, None, valor)
        return usuario

    def _autenticar(self, uow: UnidadeDeTrabalho, email: object, senha: object) -> Usuario:
        """E1 (RF-66): a mesma mensagem para e-mail inexistente e senha errada, com o mesmo trabalho de
        conferência nos dois casos. E2: o usuário inativo só é revelado a quem acerta a senha."""
        usuario = uow.usuarios.obter_por_email(normalizar_email(email))
        guardado = uow.usuarios.hash_de(usuario.id) if usuario else None
        confere = self._cifrador.conferir(senha if isinstance(senha, str) else "", guardado or self._ficticio())
        if usuario is None or guardado is None or not confere:
            raise OperacaoRecusada(CREDENCIAIS_INVALIDAS)
        if not usuario.ativo:
            raise OperacaoRecusada(USUARIO_INATIVO)
        return usuario

    def _ficticio(self) -> str:
        if self._hash_ficticio is None:
            self._hash_ficticio = self._cifrador.gerar(secrets.token_urlsafe(16))
        return self._hash_ficticio

    @staticmethod
    def _usuario(uow: UnidadeDeTrabalho, usuario_id: str) -> Usuario:
        usuario = uow.usuarios.obter(usuario_id) if isinstance(usuario_id, str) else None
        if usuario is None:
            raise OperacaoRecusada("Usuário não encontrado.")
        return usuario


def _exigir_outro_administrador(uow: UnidadeDeTrabalho, usuario: Usuario) -> None:
    """OPEN-45, decidida em 2026-10-23: o sistema não fica sem Administrador ativo."""
    outros = [
        u for u in uow.usuarios.listar() if u.ativo and u.perfil is Perfil.ADMINISTRADOR and u.id != usuario.id
    ]
    if usuario.ativo and not outros:
        raise OperacaoRecusada(
            "Este é o último Administrador ativo: cadastre outro antes de inativá-lo ou de mudar seu perfil (OPEN-45)."
        )


def _celula(perfil: object, operacao: object):
    if not isinstance(perfil, Perfil) or not isinstance(operacao, Operacao):
        raise OperacaoRecusada("Escolha um perfil e uma operação da matriz.")
    return perfil, operacao


def _ref(usuario: Usuario) -> str:
    return f"usuario {usuario.id}"
