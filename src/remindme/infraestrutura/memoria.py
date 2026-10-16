"""Implementações em memória das interfaces da aplicação. Usadas nos testes e até a escolha do banco (OPEN-02)."""

import copy
from datetime import datetime
from typing import Dict, List, Optional, Set

from remindme.dominio.auditoria import RegistroAuditoria
from remindme.dominio.titulo import Titulo


class RepositorioTitulosEmMemoria:
    def __init__(self):
        self.dados: Dict[str, Titulo] = {}

    def obter(self, titulo_id: str) -> Optional[Titulo]:
        titulo = self.dados.get(titulo_id)
        return copy.deepcopy(titulo) if titulo else None

    def salvar(self, titulo: Titulo) -> None:
        self.dados[titulo.id] = copy.deepcopy(titulo)

    def listar(self) -> List[Titulo]:
        return [copy.deepcopy(t) for t in self.dados.values()]


class AuditoriaEmMemoria:
    """Somente inclusão (ADR-004). `falhar` simula falha na gravação (CA-23)."""

    def __init__(self):
        self.registros: List[RegistroAuditoria] = []
        self.falhar = False

    def registrar(self, registro: RegistroAuditoria) -> None:
        if self.falhar:
            raise RuntimeError("Falha simulada na gravação da auditoria.")
        self.registros.append(registro)


class UnidadeDeTrabalhoEmMemoria:
    """Guarda uma cópia do estado ao abrir e a restaura se o bloco falhar (RNF-09)."""

    def __init__(self, titulos: RepositorioTitulosEmMemoria, auditoria: AuditoriaEmMemoria):
        self.titulos = titulos
        self.auditoria = auditoria
        self._copia = None

    def __enter__(self):
        self._copia = (copy.deepcopy(self.titulos.dados), list(self.auditoria.registros))
        return self

    def __exit__(self, tipo, valor, rastro):
        if tipo is not None:
            self.titulos.dados, self.auditoria.registros = self._copia
        self._copia = None


class ClientesEmMemoria:
    """Até a Spec 003, os clientes existentes são informados diretamente."""

    def __init__(self, ids: Set[str]):
        self.ids = set(ids)

    def existe(self, cliente_id: str) -> bool:
        return cliente_id in self.ids


class RelogioFixo:
    def __init__(self, agora: datetime):
        self.momento = agora

    def agora(self) -> datetime:
        return self.momento
