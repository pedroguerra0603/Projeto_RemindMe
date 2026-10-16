"""Interfaces que a aplicação usa e a infraestrutura implementa."""

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
