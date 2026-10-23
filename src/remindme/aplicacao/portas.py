"""Interfaces que a aplicação usa e a infraestrutura implementa."""

from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional, Protocol

from remindme.dominio.auditoria import RegistroAuditoria
from remindme.dominio.titulo import Titulo


class RepositorioTitulos(Protocol):
    def obter(self, titulo_id: str) -> Optional[Titulo]: ...
    def salvar(self, titulo: Titulo) -> None: ...
    def listar(self) -> List[Titulo]: ...


class RepositorioAuditoria(Protocol):
    def registrar(self, registro: RegistroAuditoria) -> None: ...


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


class Relogio(Protocol):
    def agora(self) -> datetime: ...
