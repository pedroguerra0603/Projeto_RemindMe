"""Interfaces que a aplicação usa e a infraestrutura implementa."""

from dataclasses import dataclass
from datetime import date, datetime
from typing import FrozenSet, List, Optional, Protocol

from remindme.dominio.acesso import Operacao
from remindme.dominio.auditoria import RegistroAuditoria
from remindme.dominio.cliente import Cliente
from remindme.dominio.titulo import Titulo
from remindme.dominio.usuario import Perfil, Usuario


class RepositorioTitulos(Protocol):
    def obter(self, titulo_id: str) -> Optional[Titulo]: ...
    def salvar(self, titulo: Titulo) -> None: ...
    def listar(self) -> List[Titulo]: ...


@dataclass(frozen=True)
class FiltroAuditoria:
    """RF-64: por usuário, período e tipo de operação."""

    usuario_id: Optional[str] = None
    de: Optional[date] = None
    ate: Optional[date] = None
    operacao: Optional[str] = None
    registro_afetado: Optional[str] = None


class RepositorioAuditoria(Protocol):
    def registrar(self, registro: RegistroAuditoria) -> None: ...


class ConsultaAuditoria(Protocol):
    """Leitura da auditoria (UC-12). Separada da gravação: a porta de gravação só inclui (RB-30)."""

    def consultar(self, filtro: FiltroAuditoria, limite: int = 500) -> List[RegistroAuditoria]: ...


class RepositorioUsuarios(Protocol):
    def obter(self, usuario_id: str) -> Optional[Usuario]: ...
    def obter_por_email(self, email: str) -> Optional[Usuario]: ...
    def salvar(self, usuario: Usuario) -> None: ...
    def listar(self) -> List[Usuario]: ...
    def hash_senha(self, usuario_id: str) -> Optional[str]: ...
    def definir_hash_senha(self, usuario_id: str, hash_senha: str) -> None: ...


class RepositorioSessoes(Protocol):
    """Sessão guardada no servidor (OPEN-03). A chave é o resumo do token, nunca o token."""

    def criar(self, chave: str, usuario_id: str, criada_em: datetime) -> None: ...
    def usuario_id(self, chave: str) -> Optional[str]: ...
    def encerrar(self, chave: str) -> None: ...
    def encerrar_do_usuario(self, usuario_id: str) -> None: ...


class RepositorioPermissoes(Protocol):
    def configuradas(self, perfil: Perfil) -> FrozenSet[Operacao]: ...
    def definir(self, perfil: Perfil, operacoes: FrozenSet[Operacao]) -> None: ...


class RepositorioClientes(Protocol):
    def obter(self, cliente_id: str) -> Optional[Cliente]: ...
    def obter_por_documento(self, documento: str) -> Optional[Cliente]: ...
    def salvar(self, cliente: Cliente) -> None: ...
    def listar(self, busca: Optional[str] = None) -> List[Cliente]: ...
    def existe(self, cliente_id: str) -> bool: ...


@dataclass(frozen=True)
class RegistroErro:
    """RNF-21: data e hora, operação, usuário e identificador de correlação de um erro não tratado."""

    data_hora: datetime
    operacao: str
    usuario_id: Optional[str]
    correlacao: str
    erro: str


class RegistroErros(Protocol):
    """Fica fora da transação: o registro de erro permanece quando a operação é desfeita (RNF-21)."""

    def registrar(self, registro: RegistroErro) -> None: ...


class ConsultaClientes(Protocol):
    def existe(self, cliente_id: str) -> bool: ...


class UnidadeDeTrabalho(Protocol):
    """Transação: tudo o que é feito dentro do bloco é gravado junto, ou nada é (RNF-09)."""

    titulos: RepositorioTitulos
    auditoria: RepositorioAuditoria

    def __enter__(self) -> "UnidadeDeTrabalho": ...
    def __exit__(self, tipo, valor, rastro) -> None: ...


class UnidadeDeTrabalhoCompleta(UnidadeDeTrabalho, Protocol):
    """Unidade de trabalho com todos os repositórios, usada pela aplicação web."""

    usuarios: RepositorioUsuarios
    sessoes: RepositorioSessoes
    permissoes: RepositorioPermissoes
    clientes: RepositorioClientes
    consulta_auditoria: ConsultaAuditoria


class Relogio(Protocol):
    def agora(self) -> datetime: ...
