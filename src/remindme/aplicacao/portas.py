"""Interfaces que a aplicação usa e a infraestrutura implementa."""

from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional, Protocol

from remindme.dominio.auditoria import RegistroAuditoria
from remindme.dominio.cliente import Cliente
from remindme.dominio.orcamento import Orcamento
from remindme.dominio.permissoes import MatrizPermissoes
from remindme.dominio.titulo import Titulo
from remindme.dominio.usuario import Usuario


class RepositorioTitulos(Protocol):
    def obter(self, titulo_id: str) -> Optional[Titulo]: ...
    def salvar(self, titulo: Titulo) -> None: ...
    def listar(self) -> List[Titulo]: ...


class RepositorioOrcamentos(Protocol):
    def obter(self, orcamento_id: str) -> Optional[Orcamento]: ...
    def salvar(self, orcamento: Orcamento) -> None: ...
    def listar(self) -> List[Orcamento]: ...


class RepositorioClientes(Protocol):
    """Também responde à consulta de existência usada pelo cadastro de títulos (Spec 003, INV-5)."""

    def obter(self, cliente_id: str) -> Optional[Cliente]: ...
    def obter_por_documento(self, documento: str) -> Optional[Cliente]: ...
    def salvar(self, cliente: Cliente) -> None: ...
    def listar(self) -> List[Cliente]: ...
    def existe(self, cliente_id: str) -> bool: ...


class RepositorioAuditoria(Protocol):
    """Somente inclusão e leitura: não há operação de alteração nem de exclusão (RB-30, RNF-06)."""

    def registrar(self, registro: RegistroAuditoria) -> None: ...
    def listar(self) -> List[RegistroAuditoria]: ...


class RepositorioUsuarios(Protocol):
    """A senha fica só como hash, guardado à parte do usuário (RNF-04, INV-3)."""

    def obter(self, usuario_id: str) -> Optional[Usuario]: ...
    def obter_por_email(self, email: str) -> Optional[Usuario]: ...
    def salvar(self, usuario: Usuario) -> None: ...
    def listar(self) -> List[Usuario]: ...
    def guardar_hash(self, usuario_id: str, hash_da_senha: str) -> None: ...
    def hash_de(self, usuario_id: str) -> Optional[str]: ...


@dataclass(frozen=True)
class Sessao:
    """Sessão guardada no servidor (OPEN-03). `chave` é o resumo do identificador entregue ao navegador:
    quem lê o armazenamento não obtém o identificador. `protecao` acompanha os formulários (CSRF)."""

    chave: str
    usuario_id: str
    aberta_em: datetime
    expira_em: datetime
    protecao: str


class RepositorioSessoes(Protocol):
    def obter(self, chave: str) -> Optional[Sessao]: ...
    def salvar(self, sessao: Sessao) -> None: ...
    def remover(self, chave: str) -> None: ...
    def remover_do_usuario(self, usuario_id: str) -> None: ...


class RepositorioPermissoes(Protocol):
    def obter(self) -> MatrizPermissoes: ...
    def salvar(self, matriz: MatrizPermissoes) -> None: ...


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
    """Transação: tudo o que é feito dentro do bloco é gravado junto, ou nada é (RNF-09).

    Um bloco aberto dentro de outro participa da mesma transação.
    """

    titulos: RepositorioTitulos
    clientes: RepositorioClientes
    orcamentos: RepositorioOrcamentos
    auditoria: RepositorioAuditoria
    usuarios: RepositorioUsuarios
    sessoes: RepositorioSessoes
    permissoes: RepositorioPermissoes

    def __enter__(self) -> "UnidadeDeTrabalho": ...
    def __exit__(self, tipo, valor, rastro) -> None: ...


class Relogio(Protocol):
    def agora(self) -> datetime: ...


class CifradorDeSenha(Protocol):
    def gerar(self, senha: str) -> str: ...
    def conferir(self, senha: str, guardado: str) -> bool: ...
