"""Casos de uso da Spec 002: login, sessão, autorização por perfil e administração de usuários.

`autorizar` é o único ponto em que a permissão é verificada (INV-5, DT-06).
"""

import hashlib
import re
import secrets
import uuid
from dataclasses import dataclass
from typing import Dict, FrozenSet, List, Optional

from remindme.aplicacao import senhas
from remindme.aplicacao.auditoria import Auditoria, RegistroErrosNoLog
from remindme.aplicacao.portas import RegistroErros, Relogio, UnidadeDeTrabalhoCompleta
from remindme.dominio.acesso import Operacao, exigir_permissao_alteravel, permissoes_efetivas
from remindme.dominio.erros import AcessoNegado, EntradaInvalida, OperacaoRecusada
from remindme.dominio.usuario import Perfil, Usuario

CREDENCIAIS_INVALIDAS = "E-mail ou senha inválidos."
USUARIO_INATIVO = "Usuário inativo. Procure o Administrador do sistema."
SEM_SESSAO = "Sessão ausente ou encerrada. Entre novamente."
TAMANHO_MINIMO_SENHA = 8
_EMAIL = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


@dataclass(frozen=True)
class Sessao:
    token: str
    usuario: Usuario
    operacoes: FrozenSet[Operacao]


class ServicoAcesso:
    def __init__(
        self, uow: UnidadeDeTrabalhoCompleta, relogio: Relogio, erros: Optional[RegistroErros] = None
    ):
        self._uow = uow
        self._relogio = relogio
        self._auditoria = Auditoria(uow, relogio, erros or RegistroErrosNoLog())

    # Sessão

    def entrar(self, email: Optional[str], senha: Optional[str]) -> Sessao:
        """Fluxo principal, E1 e E2. A mensagem não revela qual campo está errado (RF-66)."""
        email = _normalizar_email(email)
        with self._uow as uow:
            usuario = uow.usuarios.obter_por_email(email) if email else None
            hash_guardado = uow.usuarios.hash_senha(usuario.id) if usuario else None
        if not senhas.conferir(senha or "", hash_guardado or senhas.HASH_FICTICIO) or usuario is None:
            raise AcessoNegado(CREDENCIAIS_INVALIDAS)
        if not usuario.ativo:
            raise AcessoNegado(USUARIO_INATIVO)
        token = secrets.token_urlsafe(32)
        with self._uow as uow:
            uow.sessoes.criar(_chave(token), usuario.id, self._relogio.agora())
        return Sessao(token, usuario, self.operacoes_permitidas(usuario.perfil))

    def sair(self, token: Optional[str]) -> None:
        if token:
            with self._uow as uow:
                uow.sessoes.encerrar(_chave(token))

    def usuario_da_sessao(self, token: Optional[str]) -> Usuario:
        """E3: sem sessão, sessão desconhecida ou usuário inativo."""
        if not token:
            raise AcessoNegado(SEM_SESSAO)
        with self._uow as uow:
            usuario_id = uow.sessoes.usuario_id(_chave(token))
            usuario = uow.usuarios.obter(usuario_id) if usuario_id else None
        if usuario is None or not usuario.ativo:
            raise AcessoNegado(SEM_SESSAO)
        return usuario

    def operacoes_permitidas(self, perfil: Perfil) -> FrozenSet[Operacao]:
        """RF-65. Lido a cada chamada: a alteração vale na operação seguinte (RF-03, A4)."""
        with self._uow as uow:
            return permissoes_efetivas(perfil, uow.permissoes.configuradas(perfil))

    def autorizar(self, token: Optional[str], *operacoes: Operacao) -> Usuario:
        """INV-2: sessão válida de usuário ativo e permissão explícita de ao menos uma das operações."""
        usuario = self.usuario_da_sessao(token)
        permitidas = self.operacoes_permitidas(usuario.perfil)
        if not any(operacao in permitidas for operacao in operacoes):
            nomes = " ou ".join(f"“{operacao.value}”" for operacao in operacoes)
            raise AcessoNegado(f"O perfil {usuario.perfil.value} não tem permissão para {nomes} (RF-67).")
        return usuario

    # Administração (UC-02)

    def instalar_administrador(self, nome: str, email: str, senha: str) -> Usuario:
        """Pré-condição da Spec 002: o primeiro Administrador é criado na instalação, sem usuário."""
        with self._uow as uow:
            if any(u.perfil is Perfil.ADMINISTRADOR and u.ativo for u in uow.usuarios.listar()):
                raise OperacaoRecusada("Já existe um Administrador ativo.")
        return self._criar_usuario(None, nome, email, senha, Perfil.ADMINISTRADOR.value)

    def cadastrar_usuario(
        self,
        token: Optional[str],
        nome: Optional[str],
        email: Optional[str],
        senha: Optional[str],
        perfil: Optional[str],
    ) -> Usuario:
        """A1, E6, E7. A senha inicial é informada pelo Administrador (OPEN-35)."""
        administrador = self.autorizar(token, Operacao.ADMINISTRAR_USUARIOS)
        return self._criar_usuario(administrador, nome, email, senha, perfil)

    def alterar_perfil(self, token: Optional[str], usuario_id: str, perfil: Optional[str]) -> Usuario:
        """A2. A auditoria guarda o perfil anterior e o novo (CA-15)."""
        administrador = self.autorizar(token, Operacao.ADMINISTRAR_USUARIOS)
        novo = _perfil(perfil)
        if novo is None:
            raise EntradaInvalida({"perfil": "obrigatório"})
        with self._auditoria.operacao("alterar perfil", administrador) as op:
            usuario = self._obter(op.uow, usuario_id)
            if usuario.id == administrador.id:
                raise OperacaoRecusada("O Administrador não altera o próprio perfil (OPEN-36).")
            if usuario.perfil is novo:
                return usuario
            alterado = _copiar(usuario, perfil=novo)
            op.uow.usuarios.salvar(alterado)
            op.registrar(_ref(usuario), "perfil", usuario.perfil.value, novo.value)
        return alterado

    def inativar_usuario(self, token: Optional[str], usuario_id: str) -> Usuario:
        """A3. As sessões do usuário deixam de valer; o histórico é preservado (CA-14)."""
        return self._mudar_atividade(token, usuario_id, False)

    def reativar_usuario(self, token: Optional[str], usuario_id: str) -> Usuario:
        return self._mudar_atividade(token, usuario_id, True)

    def alterar_permissao(
        self, token: Optional[str], perfil: Perfil, operacao: Operacao, permitida: bool
    ) -> None:
        """A4, E5."""
        administrador = self.autorizar(token, Operacao.ADMINISTRAR_USUARIOS)
        exigir_permissao_alteravel(perfil, operacao)
        with self._auditoria.operacao("alterar permissão", administrador) as op:
            atuais = op.uow.permissoes.configuradas(perfil)
            if (operacao in atuais) == permitida:
                return
            novas = atuais | {operacao} if permitida else atuais - {operacao}
            op.uow.permissoes.definir(perfil, frozenset(novas))
            op.registrar(
                f"perfil {perfil.value}",
                operacao.value,
                _sim_nao(not permitida),
                _sim_nao(permitida),
            )

    def listar_usuarios(self, token: Optional[str]) -> List[Usuario]:
        self.autorizar(token, Operacao.ADMINISTRAR_USUARIOS)
        with self._uow as uow:
            return sorted(uow.usuarios.listar(), key=lambda u: u.nome.lower())

    def obter_usuario(self, token: Optional[str], usuario_id: str) -> Usuario:
        self.autorizar(token, Operacao.ADMINISTRAR_USUARIOS)
        with self._uow as uow:
            return self._obter(uow, usuario_id)

    def matriz(self, token: Optional[str]) -> Dict[Perfil, FrozenSet[Operacao]]:
        self.autorizar(token, Operacao.ADMINISTRAR_USUARIOS)
        return {perfil: self.operacoes_permitidas(perfil) for perfil in Perfil}

    def nomes_dos_usuarios(self) -> Dict[str, str]:
        """Para apresentar quem fez cada operação na auditoria. Chamado depois de `autorizar`."""
        with self._uow as uow:
            return {u.id: u.nome for u in uow.usuarios.listar()}

    def _criar_usuario(
        self,
        administrador: Optional[Usuario],
        nome: Optional[str],
        email: Optional[str],
        senha: Optional[str],
        perfil: Optional[str],
    ) -> Usuario:
        nome = (nome or "").strip()
        email = _normalizar_email(email)
        perfil_escolhido = _perfil(perfil)
        erros = {}
        if not nome:
            erros["nome"] = "obrigatório"
        if not email:
            erros["e-mail"] = "obrigatório"
        elif not _EMAIL.match(email):
            erros["e-mail"] = "formato inválido"
        if not senha:
            erros["senha"] = "obrigatória"
        elif len(senha) < TAMANHO_MINIMO_SENHA:
            erros["senha"] = f"deve ter ao menos {TAMANHO_MINIMO_SENHA} caracteres"
        if perfil_escolhido is None:
            erros["perfil"] = "obrigatório" if not perfil else "perfil inexistente"
        if erros:
            raise EntradaInvalida(erros)
        with self._auditoria.operacao("cadastrar usuário", administrador, rotina="instalação") as op:
            if op.uow.usuarios.obter_por_email(email) is not None:
                raise EntradaInvalida({"e-mail": "já cadastrado"})
            usuario = Usuario(uuid.uuid4().hex, nome, perfil_escolhido, email, True)
            op.uow.usuarios.salvar(usuario)
            op.uow.usuarios.definir_hash_senha(usuario.id, senhas.gerar_hash(senha))
            # INV-3: a auditoria registra o perfil, nunca a senha.
            op.registrar(_ref(usuario), "perfil", None, perfil_escolhido.value)
        return usuario

    def _mudar_atividade(self, token: Optional[str], usuario_id: str, ativo: bool) -> Usuario:
        administrador = self.autorizar(token, Operacao.ADMINISTRAR_USUARIOS)
        nome = "reativar usuário" if ativo else "inativar usuário"
        with self._auditoria.operacao(nome, administrador) as op:
            usuario = self._obter(op.uow, usuario_id)
            if usuario.id == administrador.id:
                raise OperacaoRecusada("O Administrador não inativa o próprio usuário (OPEN-36).")
            if usuario.ativo is ativo:
                return usuario
            alterado = _copiar(usuario, ativo=ativo)
            op.uow.usuarios.salvar(alterado)
            if not ativo:
                op.uow.sessoes.encerrar_do_usuario(usuario.id)
            op.registrar(_ref(usuario), "ativo", _sim_nao(not ativo), _sim_nao(ativo))
        return alterado

    @staticmethod
    def _obter(uow, usuario_id: str) -> Usuario:
        usuario = uow.usuarios.obter(usuario_id)
        if usuario is None:
            raise OperacaoRecusada("Usuário não encontrado.")
        return usuario


def _chave(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def _normalizar_email(email: Optional[str]) -> str:
    return (email or "").strip().lower()


def _perfil(nome: Optional[str]) -> Optional[Perfil]:
    for perfil in Perfil:
        if nome in (perfil.value, perfil.name):
            return perfil
    return None


def _copiar(usuario: Usuario, **alteracoes) -> Usuario:
    dados = dict(
        id=usuario.id, nome=usuario.nome, perfil=usuario.perfil, email=usuario.email, ativo=usuario.ativo
    )
    dados.update(alteracoes)
    return Usuario(**dados)


def _ref(usuario: Usuario) -> str:
    return f"usuario {usuario.id}"


def _sim_nao(verdadeiro: bool) -> str:
    return "sim" if verdadeiro else "não"
