"""Implementações em memória das interfaces da aplicação. Usadas nos testes e como dublês."""

import copy
from datetime import datetime
from typing import Dict, List, Optional, Set

from remindme.aplicacao.portas import RegistroErro, Sessao
from remindme.dominio.auditoria import RegistroAuditoria
from remindme.dominio.cliente import Cliente
from remindme.dominio.empresa import Empresa
from remindme.dominio.orcamento import Orcamento
from remindme.dominio.permissoes import MatrizPermissoes
from remindme.dominio.titulo import Titulo
from remindme.dominio.usuario import Usuario


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

    def _estado(self):
        return copy.deepcopy(self.dados)

    def _restaurar(self, estado) -> None:
        self.dados = estado


class RepositorioOrcamentosEmMemoria:
    def __init__(self):
        self.dados: Dict[str, Orcamento] = {}

    def obter(self, orcamento_id: str) -> Optional[Orcamento]:
        orcamento = self.dados.get(orcamento_id)
        return copy.deepcopy(orcamento) if orcamento else None

    def salvar(self, orcamento: Orcamento) -> None:
        self.dados[orcamento.id] = copy.deepcopy(orcamento)

    def listar(self) -> List[Orcamento]:
        return [copy.deepcopy(o) for o in self.dados.values()]

    def _estado(self):
        return copy.deepcopy(self.dados)

    def _restaurar(self, estado) -> None:
        self.dados = estado


class RepositorioEmpresaEmMemoria:
    def __init__(self):
        self.dados: Optional[Empresa] = None

    def obter(self) -> Optional[Empresa]:
        return self.dados

    def salvar(self, empresa: Empresa) -> None:
        self.dados = empresa

    def _estado(self):
        return self.dados

    def _restaurar(self, estado) -> None:
        self.dados = estado


class RepositorioClientesEmMemoria:
    def __init__(self):
        self.dados: Dict[str, Cliente] = {}

    def obter(self, cliente_id: str) -> Optional[Cliente]:
        return self.dados.get(cliente_id)

    def obter_por_documento(self, documento: str) -> Optional[Cliente]:
        return next((c for c in self.dados.values() if c.documento == documento), None)

    def salvar(self, cliente: Cliente) -> None:
        self.dados[cliente.id] = cliente

    def listar(self) -> List[Cliente]:
        return list(self.dados.values())

    def existe(self, cliente_id: str) -> bool:
        return cliente_id in self.dados

    def _estado(self):
        return dict(self.dados)

    def _restaurar(self, estado) -> None:
        self.dados = estado


class AuditoriaEmMemoria:
    """Somente inclusão (ADR-004, RB-30). `falhar` simula falha na gravação (CA-23; Spec 001, CA-05)."""

    def __init__(self):
        self._registros: List[RegistroAuditoria] = []
        self.falhar = False

    def registrar(self, registro: RegistroAuditoria) -> None:
        if self.falhar:
            raise RuntimeError("Falha simulada na gravação da auditoria.")
        self._registros.append(registro)

    @property
    def registros(self) -> List[RegistroAuditoria]:
        """Leitura na ordem de gravação (INV-4). Devolve uma cópia: mexer nela não altera o armazenado."""
        return list(self._registros)

    def listar(self) -> List[RegistroAuditoria]:
        return self.registros

    def _estado(self):
        return list(self._registros)

    def _restaurar(self, estado) -> None:
        self._registros = estado


class RepositorioUsuariosEmMemoria:
    def __init__(self):
        self.dados: Dict[str, Usuario] = {}
        self.hashes: Dict[str, str] = {}

    def obter(self, usuario_id: str) -> Optional[Usuario]:
        return self.dados.get(usuario_id)

    def obter_por_email(self, email: str) -> Optional[Usuario]:
        return next((u for u in self.dados.values() if u.email == email), None)

    def salvar(self, usuario: Usuario) -> None:
        self.dados[usuario.id] = usuario

    def listar(self) -> List[Usuario]:
        return list(self.dados.values())

    def guardar_hash(self, usuario_id: str, hash_da_senha: str) -> None:
        self.hashes[usuario_id] = hash_da_senha

    def hash_de(self, usuario_id: str) -> Optional[str]:
        return self.hashes.get(usuario_id)

    def _estado(self):
        return dict(self.dados), dict(self.hashes)

    def _restaurar(self, estado) -> None:
        self.dados, self.hashes = estado


class RepositorioSessoesEmMemoria:
    def __init__(self):
        self.dados: Dict[str, Sessao] = {}

    def obter(self, chave: str) -> Optional[Sessao]:
        return self.dados.get(chave)

    def salvar(self, sessao: Sessao) -> None:
        self.dados[sessao.chave] = sessao

    def remover(self, chave: str) -> None:
        self.dados.pop(chave, None)

    def remover_do_usuario(self, usuario_id: str) -> None:
        self.dados = {c: s for c, s in self.dados.items() if s.usuario_id != usuario_id}

    def _estado(self):
        return dict(self.dados)

    def _restaurar(self, estado) -> None:
        self.dados = estado


class RepositorioPermissoesEmMemoria:
    def __init__(self, matriz: Optional[MatrizPermissoes] = None):
        self.matriz = matriz or MatrizPermissoes.inicial()

    def obter(self) -> MatrizPermissoes:
        return self.matriz

    def salvar(self, matriz: MatrizPermissoes) -> None:
        self.matriz = matriz

    def _estado(self):
        return self.matriz

    def _restaurar(self, estado) -> None:
        self.matriz = estado


class RegistroErrosEmMemoria:
    """Registro de erro não tratado (RNF-21). Fica fora da unidade de trabalho e não é desfeito."""

    def __init__(self):
        self._registros: List[RegistroErro] = []

    def registrar(self, registro: RegistroErro) -> None:
        self._registros.append(registro)

    @property
    def registros(self) -> List[RegistroErro]:
        return list(self._registros)


class UnidadeDeTrabalhoEmMemoria:
    """Guarda uma cópia do estado ao abrir e a restaura se o bloco falhar (RNF-09).

    Um bloco aberto dentro de outro participa da mesma transação: só o mais externo grava ou desfaz.
    """

    def __init__(
        self,
        titulos: Optional[RepositorioTitulosEmMemoria] = None,
        auditoria: Optional[AuditoriaEmMemoria] = None,
        usuarios: Optional[RepositorioUsuariosEmMemoria] = None,
        sessoes: Optional[RepositorioSessoesEmMemoria] = None,
        permissoes: Optional[RepositorioPermissoesEmMemoria] = None,
        clientes: Optional[RepositorioClientesEmMemoria] = None,
        orcamentos: Optional[RepositorioOrcamentosEmMemoria] = None,
    ):
        self.titulos = titulos if titulos is not None else RepositorioTitulosEmMemoria()
        self.clientes = clientes if clientes is not None else RepositorioClientesEmMemoria()
        self.orcamentos = orcamentos if orcamentos is not None else RepositorioOrcamentosEmMemoria()
        self.empresa = RepositorioEmpresaEmMemoria()
        self.auditoria = auditoria if auditoria is not None else AuditoriaEmMemoria()
        self.usuarios = usuarios if usuarios is not None else RepositorioUsuariosEmMemoria()
        self.sessoes = sessoes if sessoes is not None else RepositorioSessoesEmMemoria()
        self.permissoes = permissoes if permissoes is not None else RepositorioPermissoesEmMemoria()
        self._copia = None
        self._profundidade = 0

    def _repositorios(self):
        return (
            self.titulos, self.clientes, self.orcamentos, self.empresa, self.auditoria, self.usuarios, self.sessoes,
            self.permissoes,
        )

    def __enter__(self):
        if self._profundidade == 0:
            self._copia = [r._estado() for r in self._repositorios()]
        self._profundidade += 1
        return self

    def __exit__(self, tipo, valor, rastro):
        self._profundidade -= 1
        if self._profundidade == 0:
            if tipo is not None:
                for repositorio, estado in zip(self._repositorios(), self._copia):
                    repositorio._restaurar(estado)
            self._copia = None


class ClientesEmMemoria:
    """Consulta de clientes existentes informados diretamente, para os testes que não cadastram clientes."""

    def __init__(self, ids: Set[str]):
        self.ids = set(ids)

    def existe(self, cliente_id: str) -> bool:
        return cliente_id in self.ids


class RelogioFixo:
    def __init__(self, agora: datetime):
        self.momento = agora

    def agora(self) -> datetime:
        return self.momento
