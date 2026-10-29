"""Persistência em SQLite, da biblioteca padrão (OPEN-02).

Uma conexão por banco, protegida por trava: cada unidade de trabalho é uma transação `BEGIN IMMEDIATE`, e
blocos aninhados na mesma thread participam da transação de fora (RNF-09). A auditoria é somente inclusão,
garantida também por gatilhos no próprio banco (RB-30, RNF-06).
"""

import secrets
import sqlite3
import threading
from datetime import date, datetime
from decimal import Decimal
from typing import FrozenSet, List, Optional

from remindme.aplicacao.portas import FiltroAuditoria
from remindme.dominio.acesso import MATRIZ_INICIAL, Operacao
from remindme.dominio.auditoria import RegistroAuditoria
from remindme.dominio.cliente import Cliente
from remindme.dominio.titulo import EstadoTitulo, Pagamento, Titulo
from remindme.dominio.usuario import Perfil, Usuario

ESQUEMA = """
CREATE TABLE IF NOT EXISTS configuracao (
    chave TEXT PRIMARY KEY,
    valor TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS clientes (
    id TEXT PRIMARY KEY,
    nome TEXT NOT NULL,
    documento TEXT NOT NULL UNIQUE,
    email TEXT NOT NULL DEFAULT '',
    telefone TEXT NOT NULL DEFAULT ''
);
CREATE TABLE IF NOT EXISTS titulos (
    id TEXT PRIMARY KEY,
    cliente_id TEXT NOT NULL,
    valor TEXT NOT NULL,
    vencimento TEXT NOT NULL,
    origem TEXT NOT NULL,
    condicao_pagamento TEXT,
    estado TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS titulos_por_cliente ON titulos (cliente_id);
CREATE TABLE IF NOT EXISTS pagamentos (
    id TEXT PRIMARY KEY,
    titulo_id TEXT NOT NULL REFERENCES titulos (id),
    ordem INTEGER NOT NULL,
    valor TEXT NOT NULL,
    data TEXT NOT NULL,
    estornado INTEGER NOT NULL,
    motivo_estorno TEXT
);
CREATE INDEX IF NOT EXISTS pagamentos_por_titulo ON pagamentos (titulo_id);
CREATE TABLE IF NOT EXISTS auditoria (
    sequencia INTEGER PRIMARY KEY AUTOINCREMENT,
    usuario_id TEXT,
    data_hora TEXT NOT NULL,
    operacao TEXT NOT NULL,
    registro_afetado TEXT NOT NULL,
    valor_anterior TEXT,
    valor_novo TEXT,
    motivo TEXT,
    campo TEXT,
    automatica INTEGER NOT NULL,
    rotina TEXT
);
CREATE TRIGGER IF NOT EXISTS auditoria_nao_altera BEFORE UPDATE ON auditoria
BEGIN SELECT RAISE(ABORT, 'Registros de auditoria não são alterados (RB-30).'); END;
CREATE TRIGGER IF NOT EXISTS auditoria_nao_exclui BEFORE DELETE ON auditoria
BEGIN SELECT RAISE(ABORT, 'Registros de auditoria não são excluídos (RB-30).'); END;
CREATE TABLE IF NOT EXISTS usuarios (
    id TEXT PRIMARY KEY,
    nome TEXT NOT NULL,
    email TEXT NOT NULL UNIQUE,
    perfil TEXT NOT NULL,
    ativo INTEGER NOT NULL,
    hash_senha TEXT
);
CREATE TABLE IF NOT EXISTS sessoes (
    chave TEXT PRIMARY KEY,
    usuario_id TEXT NOT NULL REFERENCES usuarios (id),
    criada_em TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS permissoes (
    perfil TEXT NOT NULL,
    operacao TEXT NOT NULL,
    PRIMARY KEY (perfil, operacao)
);
"""


class BancoSQLite:
    def __init__(self, caminho: str = ":memory:"):
        self.conexao = sqlite3.connect(caminho, check_same_thread=False, isolation_level=None)
        self.conexao.execute("PRAGMA foreign_keys = ON")
        if caminho != ":memory:":
            self.conexao.execute("PRAGMA journal_mode = WAL")
        self.trava = threading.RLock()
        with self.trava:
            self.conexao.executescript(ESQUEMA)
            self._semear_permissoes()

    def _semear_permissoes(self) -> None:
        """Matriz inicial (OPEN-32), gravada uma única vez; depois vale o que o Administrador configurar."""
        if self.conexao.execute("SELECT 1 FROM configuracao WHERE chave = 'permissoes'").fetchone():
            return
        self.conexao.execute("BEGIN IMMEDIATE")
        self.conexao.executemany(
            "INSERT OR IGNORE INTO permissoes (perfil, operacao) VALUES (?, ?)",
            [(perfil.name, operacao.name) for perfil, ops in MATRIZ_INICIAL.items() for operacao in ops],
        )
        self.conexao.execute("INSERT INTO configuracao (chave, valor) VALUES ('permissoes', 'iniciadas')")
        self.conexao.execute("COMMIT")

    def segredo(self) -> bytes:
        """Chave que assina formulários e avisos da interface. Gerada na primeira execução e guardada no banco."""
        with self.trava:
            linha = self.conexao.execute("SELECT valor FROM configuracao WHERE chave = 'segredo'").fetchone()
            if linha is None:
                valor = secrets.token_hex(32)
                self.conexao.execute("INSERT INTO configuracao (chave, valor) VALUES ('segredo', ?)", (valor,))
                return bytes.fromhex(valor)
            return bytes.fromhex(linha[0])

    def fechar(self) -> None:
        self.conexao.close()


class _Repositorio:
    def __init__(self, banco: BancoSQLite):
        self._banco = banco

    def _executar(self, sql: str, parametros=()):
        return self._banco.conexao.execute(sql, parametros)


class RepositorioTitulosSQLite(_Repositorio):
    def obter(self, titulo_id: str) -> Optional[Titulo]:
        linha = self._executar("SELECT * FROM titulos WHERE id = ?", (titulo_id,)).fetchone()
        return self._montar(linha) if linha else None

    def salvar(self, titulo: Titulo) -> None:
        self._executar(
            """INSERT INTO titulos (id, cliente_id, valor, vencimento, origem, condicao_pagamento, estado)
               VALUES (?, ?, ?, ?, ?, ?, ?)
               ON CONFLICT (id) DO UPDATE SET cliente_id = excluded.cliente_id, valor = excluded.valor,
                 vencimento = excluded.vencimento, origem = excluded.origem,
                 condicao_pagamento = excluded.condicao_pagamento, estado = excluded.estado""",
            (
                titulo.id,
                titulo.cliente_id,
                str(titulo.valor),
                titulo.vencimento.isoformat(),
                titulo.origem,
                titulo.condicao_pagamento,
                titulo.estado.name,
            ),
        )
        self._executar("DELETE FROM pagamentos WHERE titulo_id = ?", (titulo.id,))
        self._banco.conexao.executemany(
            """INSERT INTO pagamentos (id, titulo_id, ordem, valor, data, estornado, motivo_estorno)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            [
                (p.id, titulo.id, ordem, str(p.valor), p.data.isoformat(), int(p.estornado), p.motivo_estorno)
                for ordem, p in enumerate(titulo.pagamentos)
            ],
        )

    def listar(self) -> List[Titulo]:
        linhas = self._executar("SELECT * FROM titulos ORDER BY vencimento, id").fetchall()
        pagamentos = {}
        for p in self._executar("SELECT * FROM pagamentos ORDER BY titulo_id, ordem"):
            pagamentos.setdefault(p[1], []).append(p)
        return [self._montar(linha, pagamentos.get(linha[0], [])) for linha in linhas]

    def _montar(self, linha, pagamentos=None) -> Titulo:
        id, cliente_id, valor, vencimento, origem, condicao, estado = linha
        if pagamentos is None:
            pagamentos = self._executar(
                "SELECT * FROM pagamentos WHERE titulo_id = ? ORDER BY ordem", (id,)
            ).fetchall()
        return Titulo(
            id=id,
            cliente_id=cliente_id,
            valor=Decimal(valor),
            vencimento=date.fromisoformat(vencimento),
            origem=origem,
            condicao_pagamento=condicao,
            estado=EstadoTitulo[estado],
            pagamentos=[
                Pagamento(
                    id=p[0],
                    valor=Decimal(p[3]),
                    data=date.fromisoformat(p[4]),
                    estornado=bool(p[5]),
                    motivo_estorno=p[6],
                )
                for p in pagamentos
            ],
        )


_CAMPOS_AUDITORIA = (
    "usuario_id, data_hora, operacao, registro_afetado, valor_anterior, valor_novo, motivo, campo, "
    "automatica, rotina"
)


class AuditoriaSQLite(_Repositorio):
    """Somente inclusão (ADR-004)."""

    def registrar(self, registro: RegistroAuditoria) -> None:
        self._executar(
            f"INSERT INTO auditoria ({_CAMPOS_AUDITORIA}) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                registro.usuario_id,
                registro.data_hora.isoformat(),
                registro.operacao,
                registro.registro_afetado,
                registro.valor_anterior,
                registro.valor_novo,
                registro.motivo,
                registro.campo,
                int(registro.automatica),
                registro.rotina,
            ),
        )

    @property
    def registros(self) -> List[RegistroAuditoria]:
        """Na ordem de gravação, como `AuditoriaEmMemoria.registros`."""
        return list(reversed(ConsultaAuditoriaSQLite(self._banco).consultar(FiltroAuditoria(), limite=-1)))


class ConsultaAuditoriaSQLite(_Repositorio):
    def consultar(self, filtro: FiltroAuditoria, limite: int = 500) -> List[RegistroAuditoria]:
        """RF-64. Os mais recentes primeiro."""
        condicoes, parametros = [], []
        if filtro.usuario_id is not None:
            condicoes.append("usuario_id = ?")
            parametros.append(filtro.usuario_id)
        if filtro.de is not None:
            condicoes.append("substr(data_hora, 1, 10) >= ?")
            parametros.append(filtro.de.isoformat())
        if filtro.ate is not None:
            condicoes.append("substr(data_hora, 1, 10) <= ?")
            parametros.append(filtro.ate.isoformat())
        if filtro.operacao is not None:
            condicoes.append("operacao = ?")
            parametros.append(filtro.operacao)
        if filtro.registro_afetado is not None:
            condicoes.append("instr(registro_afetado, ?) > 0")
            parametros.append(filtro.registro_afetado)
        onde = f"WHERE {' AND '.join(condicoes)}" if condicoes else ""
        linhas = self._executar(
            f"SELECT {_CAMPOS_AUDITORIA} FROM auditoria {onde} ORDER BY sequencia DESC LIMIT ?",
            (*parametros, limite),
        )
        return [
            RegistroAuditoria(
                usuario_id=l[0],
                data_hora=datetime.fromisoformat(l[1]),
                operacao=l[2],
                registro_afetado=l[3],
                valor_anterior=l[4],
                valor_novo=l[5],
                motivo=l[6],
                campo=l[7],
                automatica=bool(l[8]),
                rotina=l[9],
            )
            for l in linhas
        ]


class RepositorioUsuariosSQLite(_Repositorio):
    def obter(self, usuario_id: str) -> Optional[Usuario]:
        linha = self._executar(
            "SELECT id, nome, perfil, email, ativo FROM usuarios WHERE id = ?", (usuario_id,)
        ).fetchone()
        return _usuario(linha) if linha else None

    def obter_por_email(self, email: str) -> Optional[Usuario]:
        linha = self._executar(
            "SELECT id, nome, perfil, email, ativo FROM usuarios WHERE email = ?", (email,)
        ).fetchone()
        return _usuario(linha) if linha else None

    def salvar(self, usuario: Usuario) -> None:
        self._executar(
            """INSERT INTO usuarios (id, nome, email, perfil, ativo) VALUES (?, ?, ?, ?, ?)
               ON CONFLICT (id) DO UPDATE SET nome = excluded.nome, email = excluded.email,
                 perfil = excluded.perfil, ativo = excluded.ativo""",
            (usuario.id, usuario.nome, usuario.email, usuario.perfil.name, int(usuario.ativo)),
        )

    def listar(self) -> List[Usuario]:
        return [_usuario(l) for l in self._executar("SELECT id, nome, perfil, email, ativo FROM usuarios")]

    def hash_senha(self, usuario_id: str) -> Optional[str]:
        linha = self._executar("SELECT hash_senha FROM usuarios WHERE id = ?", (usuario_id,)).fetchone()
        return linha[0] if linha else None

    def definir_hash_senha(self, usuario_id: str, hash_senha: str) -> None:
        self._executar("UPDATE usuarios SET hash_senha = ? WHERE id = ?", (hash_senha, usuario_id))


class RepositorioSessoesSQLite(_Repositorio):
    def criar(self, chave: str, usuario_id: str, criada_em: datetime) -> None:
        self._executar(
            "INSERT INTO sessoes (chave, usuario_id, criada_em) VALUES (?, ?, ?)",
            (chave, usuario_id, criada_em.isoformat()),
        )

    def usuario_id(self, chave: str) -> Optional[str]:
        linha = self._executar("SELECT usuario_id FROM sessoes WHERE chave = ?", (chave,)).fetchone()
        return linha[0] if linha else None

    def encerrar(self, chave: str) -> None:
        self._executar("DELETE FROM sessoes WHERE chave = ?", (chave,))

    def encerrar_do_usuario(self, usuario_id: str) -> None:
        self._executar("DELETE FROM sessoes WHERE usuario_id = ?", (usuario_id,))


class RepositorioPermissoesSQLite(_Repositorio):
    def configuradas(self, perfil: Perfil) -> FrozenSet[Operacao]:
        linhas = self._executar("SELECT operacao FROM permissoes WHERE perfil = ?", (perfil.name,))
        return frozenset(Operacao[l[0]] for l in linhas if l[0] in Operacao.__members__)

    def definir(self, perfil: Perfil, operacoes: FrozenSet[Operacao]) -> None:
        self._executar("DELETE FROM permissoes WHERE perfil = ?", (perfil.name,))
        self._banco.conexao.executemany(
            "INSERT INTO permissoes (perfil, operacao) VALUES (?, ?)",
            [(perfil.name, operacao.name) for operacao in operacoes],
        )


class RepositorioClientesSQLite(_Repositorio):
    def obter(self, cliente_id: str) -> Optional[Cliente]:
        linha = self._executar("SELECT * FROM clientes WHERE id = ?", (cliente_id,)).fetchone()
        return Cliente(*linha) if linha else None

    def obter_por_documento(self, documento: str) -> Optional[Cliente]:
        linha = self._executar("SELECT * FROM clientes WHERE documento = ?", (documento,)).fetchone()
        return Cliente(*linha) if linha else None

    def salvar(self, cliente: Cliente) -> None:
        self._executar(
            """INSERT INTO clientes (id, nome, documento, email, telefone) VALUES (?, ?, ?, ?, ?)
               ON CONFLICT (id) DO UPDATE SET nome = excluded.nome, documento = excluded.documento,
                 email = excluded.email, telefone = excluded.telefone""",
            (cliente.id, cliente.nome, cliente.documento, cliente.email, cliente.telefone),
        )

    def listar(self, busca: Optional[str] = None) -> List[Cliente]:
        if not busca:
            linhas = self._executar("SELECT * FROM clientes ORDER BY nome COLLATE NOCASE")
        else:
            digitos = "".join(c for c in busca if c.isdigit())
            linhas = self._executar(
                """SELECT * FROM clientes WHERE instr(lower(nome), lower(?)) > 0
                   OR (? <> '' AND instr(documento, ?) > 0) ORDER BY nome COLLATE NOCASE""",
                (busca, digitos, digitos),
            )
        return [Cliente(*l) for l in linhas]

    def existe(self, cliente_id: str) -> bool:
        return self._executar("SELECT 1 FROM clientes WHERE id = ?", (cliente_id,)).fetchone() is not None


class UnidadeDeTrabalhoSQLite:
    """Transação sobre o banco (RNF-09). Desfaz tudo se o bloco terminar com exceção."""

    def __init__(self, banco: BancoSQLite):
        self._banco = banco
        self._local = threading.local()
        self.titulos = RepositorioTitulosSQLite(banco)
        self.auditoria = AuditoriaSQLite(banco)
        self.usuarios = RepositorioUsuariosSQLite(banco)
        self.sessoes = RepositorioSessoesSQLite(banco)
        self.permissoes = RepositorioPermissoesSQLite(banco)
        self.clientes = RepositorioClientesSQLite(banco)
        self.consulta_auditoria = ConsultaAuditoriaSQLite(banco)

    def __enter__(self):
        self._banco.trava.acquire()
        profundidade = getattr(self._local, "profundidade", 0)
        if profundidade == 0:
            try:
                self._banco.conexao.execute("BEGIN IMMEDIATE")
            except BaseException:
                self._banco.trava.release()
                raise
        self._local.profundidade = profundidade + 1
        return self

    def __exit__(self, tipo, valor, rastro):
        self._local.profundidade -= 1
        try:
            if self._local.profundidade == 0:
                self._banco.conexao.execute("ROLLBACK" if tipo is not None else "COMMIT")
        finally:
            self._banco.trava.release()


def _usuario(linha) -> Usuario:
    id, nome, perfil, email, ativo = linha
    return Usuario(id=id, nome=nome, perfil=Perfil[perfil], email=email, ativo=bool(ativo))
