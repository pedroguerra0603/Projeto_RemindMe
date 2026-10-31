"""Persistência em SQLite, pelo módulo `sqlite3` da biblioteca padrão (ADR-005, ADR-007, Spec 017).

Cada transação abre uma conexão com `BEGIN IMMEDIATE` (RNF-09). Valores monetários são texto decimal, datas
são texto ISO 8601 e estados, perfis e operações são guardados pelo nome do enum.
"""

import sqlite3
import threading
from datetime import date, datetime
from decimal import Decimal
from pathlib import Path
from typing import List, Optional

from remindme.aplicacao.portas import Sessao
from remindme.dominio.auditoria import RegistroAuditoria
from remindme.dominio.cliente import Cliente
from remindme.dominio.conta_pagar import ContaPagar, EstadoContaPagar
from remindme.dominio.empresa import CAMPOS as CAMPOS_DA_EMPRESA, Empresa
from remindme.dominio.fornecedor import Fornecedor
from remindme.dominio.orcamento import AprovacaoDesconto, EstadoOrcamento, ItemOrcamento, Orcamento, PendenciaDesconto
from remindme.dominio.operacoes import Operacao
from remindme.dominio.permissoes import MatrizPermissoes
from remindme.dominio.titulo import EstadoTitulo, Pagamento, Titulo
from remindme.dominio.usuario import Perfil, Usuario

_ESQUEMA_1 = """
CREATE TABLE usuarios (
    id TEXT PRIMARY KEY,
    nome TEXT NOT NULL,
    email TEXT NOT NULL UNIQUE,
    perfil TEXT NOT NULL,
    ativo INTEGER NOT NULL,
    hash_da_senha TEXT
);
CREATE TABLE sessoes (
    chave TEXT PRIMARY KEY,
    usuario_id TEXT NOT NULL REFERENCES usuarios (id),
    aberta_em TEXT NOT NULL,
    expira_em TEXT NOT NULL,
    protecao TEXT NOT NULL
);
CREATE TABLE permissoes (
    operacao TEXT NOT NULL,
    perfil TEXT NOT NULL,
    PRIMARY KEY (operacao, perfil)
);
CREATE TABLE clientes (
    id TEXT PRIMARY KEY,
    nome TEXT NOT NULL,
    documento TEXT NOT NULL UNIQUE,
    contato TEXT NOT NULL
);
CREATE TABLE titulos (
    id TEXT PRIMARY KEY,
    cliente_id TEXT NOT NULL REFERENCES clientes (id),
    valor TEXT NOT NULL,
    vencimento TEXT NOT NULL,
    origem TEXT NOT NULL,
    condicao_pagamento TEXT,
    estado TEXT NOT NULL
);
CREATE TABLE pagamentos (
    id TEXT PRIMARY KEY,
    titulo_id TEXT NOT NULL REFERENCES titulos (id),
    ordem INTEGER NOT NULL,
    valor TEXT NOT NULL,
    data TEXT NOT NULL,
    estornado INTEGER NOT NULL,
    motivo_estorno TEXT,
    pedido_id TEXT,
    UNIQUE (titulo_id, pedido_id)
);
CREATE INDEX pagamentos_do_titulo ON pagamentos (titulo_id, ordem);
CREATE TABLE auditoria (
    sequencia INTEGER PRIMARY KEY AUTOINCREMENT,
    usuario_id TEXT,
    data_hora TEXT NOT NULL,
    operacao TEXT NOT NULL,
    registro_afetado TEXT NOT NULL,
    campo TEXT,
    valor_anterior TEXT,
    valor_novo TEXT,
    motivo TEXT,
    automatica INTEGER NOT NULL,
    rotina TEXT
);
-- RB-30 e RNF-06 no próprio armazenamento: o banco recusa alterar e excluir registros de auditoria.
-- A regra continua no domínio e na porta, que só oferecem incluir e ler (ADR-004); o gatilho só recusa.
CREATE TRIGGER auditoria_nao_se_altera BEFORE UPDATE ON auditoria
BEGIN SELECT RAISE(ABORT, 'Registros de auditoria não são alterados (RB-30).'); END;
CREATE TRIGGER auditoria_nao_se_exclui BEFORE DELETE ON auditoria
BEGIN SELECT RAISE(ABORT, 'Registros de auditoria não são excluídos (RB-30).'); END;
"""

# Spec 004: orçamentos, itens e decisões de desconto.
_ESQUEMA_2 = """
CREATE TABLE orcamentos (
    id TEXT PRIMARY KEY,
    cliente_id TEXT NOT NULL REFERENCES clientes (id),
    elaborado_por TEXT NOT NULL REFERENCES usuarios (id),
    criado_em TEXT NOT NULL,
    estado TEXT NOT NULL,
    condicao_pagamento TEXT,
    percentual_desconto TEXT NOT NULL,
    pendente_percentual TEXT,
    pendente_solicitado_por TEXT,
    pendente_alcada TEXT,
    motivo_cancelamento TEXT
);
CREATE INDEX orcamentos_do_cliente ON orcamentos (cliente_id);
CREATE TABLE itens_orcamento (
    id TEXT PRIMARY KEY,
    orcamento_id TEXT NOT NULL REFERENCES orcamentos (id),
    ordem INTEGER NOT NULL,
    descricao TEXT NOT NULL,
    quantidade TEXT NOT NULL,
    valor_unitario TEXT NOT NULL
);
CREATE INDEX itens_do_orcamento ON itens_orcamento (orcamento_id, ordem);
CREATE TABLE decisoes_desconto (
    orcamento_id TEXT NOT NULL REFERENCES orcamentos (id),
    ordem INTEGER NOT NULL,
    aprovado INTEGER NOT NULL,
    percentual_solicitado TEXT NOT NULL,
    percentual_aprovado TEXT,
    decidido_por TEXT NOT NULL REFERENCES usuarios (id),
    data TEXT NOT NULL,
    PRIMARY KEY (orcamento_id, ordem)
);
"""

# OPEN-54: os dados da empresa, numa linha só (id = 1).
_ESQUEMA_3 = """
CREATE TABLE empresa (
    id INTEGER PRIMARY KEY CHECK (id = 1),
    razao_social TEXT NOT NULL,
    nome_fantasia TEXT NOT NULL,
    cnpj TEXT NOT NULL,
    telefone TEXT NOT NULL,
    email TEXT NOT NULL,
    endereco TEXT NOT NULL
);
"""

# Spec 018: fornecedores, contas a pagar e os pagamentos delas. O perfil Cliente sai da matriz (OPEN-57).
_ESQUEMA_4 = """
CREATE TABLE fornecedores (
    id TEXT PRIMARY KEY,
    nome TEXT NOT NULL,
    documento TEXT NOT NULL UNIQUE,
    contato TEXT NOT NULL
);
CREATE TABLE contas_pagar (
    id TEXT PRIMARY KEY,
    fornecedor_id TEXT NOT NULL REFERENCES fornecedores (id),
    descricao TEXT NOT NULL,
    valor TEXT NOT NULL,
    vencimento TEXT NOT NULL,
    condicao_pagamento TEXT,
    estado TEXT NOT NULL
);
CREATE INDEX contas_por_vencimento ON contas_pagar (vencimento);
CREATE TABLE pagamentos_conta (
    id TEXT PRIMARY KEY,
    conta_id TEXT NOT NULL REFERENCES contas_pagar (id),
    ordem INTEGER NOT NULL,
    valor TEXT NOT NULL,
    data TEXT NOT NULL,
    estornado INTEGER NOT NULL,
    motivo_estorno TEXT,
    pedido_id TEXT,
    UNIQUE (conta_id, pedido_id)
);
CREATE INDEX pagamentos_da_conta ON pagamentos_conta (conta_id, ordem);
DELETE FROM permissoes WHERE perfil = 'CLIENTE';
"""

# Operações novas da Spec 018: bancos criados antes as recebem como na matriz inicial.
_OPERACOES_DA_SPEC_018 = (
    Operacao.MANTER_FORNECEDORES,
    Operacao.CONSULTAR_FORNECEDORES,
    Operacao.CADASTRAR_CONTA_PAGAR,
    Operacao.PAGAR_CONTA,
    Operacao.ESTORNAR_PAGAMENTO_CONTA,
    Operacao.CANCELAR_CONTA_PAGAR,
    Operacao.CONSULTAR_CONTAS_PAGAR,
)

MIGRACOES = [_ESQUEMA_1, _ESQUEMA_2, _ESQUEMA_3, _ESQUEMA_4]


def preparar_banco(caminho: str) -> None:
    """Cria o arquivo, se preciso, e aplica as migrações que faltam (`PRAGMA user_version`)."""
    if caminho != ":memory:":
        Path(caminho).parent.mkdir(parents=True, exist_ok=True)
    conexao = sqlite3.connect(caminho, isolation_level=None)
    try:
        conexao.execute("PRAGMA journal_mode = WAL")
        versao = conexao.execute("PRAGMA user_version").fetchone()[0]
        for numero, script in enumerate(MIGRACOES[versao:], start=versao + 1):
            conexao.execute("BEGIN IMMEDIATE")
            try:
                for comando in _comandos(script):
                    conexao.execute(comando)
                if numero == 1:
                    conexao.executemany(
                        "INSERT INTO permissoes (operacao, perfil) VALUES (?, ?)",
                        [(o.name, p.name) for o, p in MatrizPermissoes.inicial().concedidas],
                    )
                if numero == 3:
                    # Bancos criados antes: o Dono ganha a nova operação, como na matriz inicial (OPEN-54).
                    conexao.execute("INSERT OR IGNORE INTO permissoes (operacao, perfil) VALUES ('MANTER_EMPRESA', 'DONO')")
                if numero == 4:
                    conexao.executemany(
                        "INSERT OR IGNORE INTO permissoes (operacao, perfil) VALUES (?, ?)",
                        [(o.name, p.name) for o, p in MatrizPermissoes.inicial().concedidas if o in _OPERACOES_DA_SPEC_018],
                    )
                conexao.execute(f"PRAGMA user_version = {numero}")
                conexao.execute("COMMIT")
            except Exception:
                conexao.execute("ROLLBACK")
                raise
    finally:
        conexao.close()


def _comandos(script: str) -> List[str]:
    """Separa os comandos do script, respeitando os gatilhos, que têm ponto e vírgula dentro."""
    comandos, atual = [], []
    for linha in script.splitlines():
        if linha.strip().startswith("--") or not linha.strip():
            continue
        atual.append(linha)
        texto = "\n".join(atual)
        if sqlite3.complete_statement(texto):
            comandos.append(texto)
            atual = []
    return comandos


class UnidadeDeTrabalhoSQLite:
    """Transação real (RNF-09). Cada linha de execução tem a sua conexão; um bloco aberto dentro de outro
    participa da mesma transação, e só o mais externo confirma ou desfaz."""

    def __init__(self, caminho: str):
        self.caminho = caminho
        self._local = threading.local()
        self.titulos = RepositorioTitulosSQLite(self)
        self.clientes = RepositorioClientesSQLite(self)
        self.orcamentos = RepositorioOrcamentosSQLite(self)
        self.empresa = RepositorioEmpresaSQLite(self)
        self.fornecedores = RepositorioFornecedoresSQLite(self)
        self.contas_pagar = RepositorioContasPagarSQLite(self)
        self.auditoria = AuditoriaSQLite(self)
        self.usuarios = RepositorioUsuariosSQLite(self)
        self.sessoes = RepositorioSessoesSQLite(self)
        self.permissoes = RepositorioPermissoesSQLite(self)

    def conexao(self) -> sqlite3.Connection:
        conexao = getattr(self._local, "conexao", None)
        if conexao is None:
            raise RuntimeError("Acesso ao banco fora de uma unidade de trabalho.")
        return conexao

    def __enter__(self):
        profundidade = getattr(self._local, "profundidade", 0)
        if profundidade == 0:
            conexao = sqlite3.connect(self.caminho, timeout=10, isolation_level=None)
            try:
                conexao.execute("PRAGMA foreign_keys = ON")
                conexao.execute("BEGIN IMMEDIATE")
            except Exception:
                conexao.close()
                raise
            self._local.conexao = conexao
        self._local.profundidade = profundidade + 1
        return self

    def __exit__(self, tipo, valor, rastro):
        self._local.profundidade -= 1
        if self._local.profundidade == 0:
            conexao = self._local.conexao
            self._local.conexao = None
            try:
                conexao.execute("COMMIT" if tipo is None else "ROLLBACK")
            finally:
                conexao.close()


class _Repositorio:
    def __init__(self, uow: UnidadeDeTrabalhoSQLite):
        self._uow = uow

    def _executar(self, comando: str, parametros=()):
        return self._uow.conexao().execute(comando, parametros)


class RepositorioTitulosSQLite(_Repositorio):
    def obter(self, titulo_id: str) -> Optional[Titulo]:
        linha = self._executar("SELECT * FROM titulos WHERE id = ?", (titulo_id,)).fetchone()
        if linha is None:
            return None
        return self._montar(linha, self._pagamentos([titulo_id]).get(titulo_id, []))

    def salvar(self, titulo: Titulo) -> None:
        self._executar(
            """INSERT INTO titulos (id, cliente_id, valor, vencimento, origem, condicao_pagamento, estado)
               VALUES (?, ?, ?, ?, ?, ?, ?)
               ON CONFLICT (id) DO UPDATE SET estado = excluded.estado,
                   condicao_pagamento = excluded.condicao_pagamento""",
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
        for ordem, pagamento in enumerate(titulo.pagamentos):
            self._executar(
                """INSERT INTO pagamentos (id, titulo_id, ordem, valor, data, estornado, motivo_estorno, pedido_id)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                   ON CONFLICT (id) DO UPDATE SET estornado = excluded.estornado,
                       motivo_estorno = excluded.motivo_estorno""",
                (
                    pagamento.id,
                    titulo.id,
                    ordem,
                    str(pagamento.valor),
                    pagamento.data.isoformat(),
                    int(pagamento.estornado),
                    pagamento.motivo_estorno,
                    pagamento.pedido_id,
                ),
            )

    def listar(self) -> List[Titulo]:
        linhas = self._executar("SELECT * FROM titulos ORDER BY vencimento, id").fetchall()
        pagamentos = self._pagamentos(None)
        return [self._montar(linha, pagamentos.get(linha["id"], [])) for linha in linhas]

    def _pagamentos(self, ids):
        if ids is None:
            linhas = self._executar("SELECT * FROM pagamentos ORDER BY titulo_id, ordem").fetchall()
        else:
            linhas = self._executar(
                "SELECT * FROM pagamentos WHERE titulo_id = ? ORDER BY ordem", (ids[0],)
            ).fetchall()
        por_titulo = {}
        for linha in linhas:
            por_titulo.setdefault(linha["titulo_id"], []).append(
                Pagamento(
                    id=linha["id"],
                    valor=Decimal(linha["valor"]),
                    data=date.fromisoformat(linha["data"]),
                    estornado=bool(linha["estornado"]),
                    motivo_estorno=linha["motivo_estorno"],
                    pedido_id=linha["pedido_id"],
                )
            )
        return por_titulo

    @staticmethod
    def _montar(linha, pagamentos) -> Titulo:
        return Titulo(
            id=linha["id"],
            cliente_id=linha["cliente_id"],
            valor=Decimal(linha["valor"]),
            vencimento=date.fromisoformat(linha["vencimento"]),
            origem=linha["origem"],
            condicao_pagamento=linha["condicao_pagamento"],
            estado=EstadoTitulo[linha["estado"]],
            pagamentos=pagamentos,
        )

    def _executar(self, comando: str, parametros=()):
        cursor = super()._executar(comando, parametros)
        cursor.row_factory = sqlite3.Row
        return cursor


class RepositorioClientesSQLite(_Repositorio):
    def obter(self, cliente_id: str) -> Optional[Cliente]:
        return self._um("SELECT id, nome, documento, contato FROM clientes WHERE id = ?", cliente_id)

    def obter_por_documento(self, documento: str) -> Optional[Cliente]:
        return self._um("SELECT id, nome, documento, contato FROM clientes WHERE documento = ?", documento)

    def salvar(self, cliente: Cliente) -> None:
        self._executar(
            """INSERT INTO clientes (id, nome, documento, contato) VALUES (?, ?, ?, ?)
               ON CONFLICT (id) DO UPDATE SET nome = excluded.nome, documento = excluded.documento,
                   contato = excluded.contato""",
            (cliente.id, cliente.nome, cliente.documento, cliente.contato),
        )

    def listar(self) -> List[Cliente]:
        linhas = self._executar("SELECT id, nome, documento, contato FROM clientes").fetchall()
        return [Cliente(*linha) for linha in linhas]

    def existe(self, cliente_id: str) -> bool:
        return self._executar("SELECT 1 FROM clientes WHERE id = ?", (cliente_id,)).fetchone() is not None

    def _um(self, comando: str, chave: str) -> Optional[Cliente]:
        linha = self._executar(comando, (chave,)).fetchone()
        return Cliente(*linha) if linha else None


class RepositorioFornecedoresSQLite(_Repositorio):
    _COLUNAS = "id, nome, documento, contato"

    def obter(self, fornecedor_id: str) -> Optional[Fornecedor]:
        return self._um(f"SELECT {self._COLUNAS} FROM fornecedores WHERE id = ?", fornecedor_id)

    def obter_por_documento(self, documento: str) -> Optional[Fornecedor]:
        return self._um(f"SELECT {self._COLUNAS} FROM fornecedores WHERE documento = ?", documento)

    def salvar(self, fornecedor: Fornecedor) -> None:
        self._executar(
            """INSERT INTO fornecedores (id, nome, documento, contato) VALUES (?, ?, ?, ?)
               ON CONFLICT (id) DO UPDATE SET nome = excluded.nome, documento = excluded.documento,
                   contato = excluded.contato""",
            (fornecedor.id, fornecedor.nome, fornecedor.documento, fornecedor.contato),
        )

    def listar(self) -> List[Fornecedor]:
        return [Fornecedor(*linha) for linha in self._executar(f"SELECT {self._COLUNAS} FROM fornecedores").fetchall()]

    def existe(self, fornecedor_id: str) -> bool:
        return self._executar("SELECT 1 FROM fornecedores WHERE id = ?", (fornecedor_id,)).fetchone() is not None

    def _um(self, comando: str, chave: str) -> Optional[Fornecedor]:
        linha = self._executar(comando, (chave,)).fetchone()
        return Fornecedor(*linha) if linha else None


class RepositorioContasPagarSQLite(_Repositorio):
    """Como o repositório de títulos: a conta e os pagamentos, que só são incluídos ou marcados como estornados."""

    _COLUNAS = "id, fornecedor_id, descricao, valor, vencimento, condicao_pagamento, estado"

    def obter(self, conta_id: str) -> Optional[ContaPagar]:
        linha = self._executar(f"SELECT {self._COLUNAS} FROM contas_pagar WHERE id = ?", (conta_id,)).fetchone()
        return self._montar(linha, self._pagamentos(conta_id).get(conta_id, [])) if linha else None

    def salvar(self, conta: ContaPagar) -> None:
        self._executar(
            """INSERT INTO contas_pagar (id, fornecedor_id, descricao, valor, vencimento, condicao_pagamento, estado)
               VALUES (?, ?, ?, ?, ?, ?, ?)
               ON CONFLICT (id) DO UPDATE SET estado = excluded.estado""",
            (
                conta.id, conta.fornecedor_id, conta.descricao, str(conta.valor), conta.vencimento.isoformat(),
                conta.condicao_pagamento, conta.estado.name,
            ),
        )
        for ordem, pagamento in enumerate(conta.pagamentos):
            self._executar(
                """INSERT INTO pagamentos_conta (id, conta_id, ordem, valor, data, estornado, motivo_estorno, pedido_id)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                   ON CONFLICT (id) DO UPDATE SET estornado = excluded.estornado,
                       motivo_estorno = excluded.motivo_estorno""",
                (
                    pagamento.id, conta.id, ordem, str(pagamento.valor), pagamento.data.isoformat(),
                    int(pagamento.estornado), pagamento.motivo_estorno, pagamento.pedido_id,
                ),
            )

    def listar(self) -> List[ContaPagar]:
        linhas = self._executar(f"SELECT {self._COLUNAS} FROM contas_pagar ORDER BY vencimento, id").fetchall()
        pagamentos = self._pagamentos(None)
        return [self._montar(linha, pagamentos.get(linha[0], [])) for linha in linhas]

    def _pagamentos(self, conta_id: Optional[str]):
        colunas = "conta_id, id, valor, data, estornado, motivo_estorno, pedido_id"
        if conta_id is None:
            linhas = self._executar(f"SELECT {colunas} FROM pagamentos_conta ORDER BY conta_id, ordem").fetchall()
        else:
            linhas = self._executar(
                f"SELECT {colunas} FROM pagamentos_conta WHERE conta_id = ? ORDER BY ordem", (conta_id,)
            ).fetchall()
        por_conta = {}
        for conta, id_, valor, data, estornado, motivo, pedido in linhas:
            por_conta.setdefault(conta, []).append(
                Pagamento(id_, Decimal(valor), date.fromisoformat(data), bool(estornado), motivo, pedido)
            )
        return por_conta

    @staticmethod
    def _montar(linha, pagamentos) -> ContaPagar:
        id_, fornecedor_id, descricao, valor, vencimento, condicao, estado = linha
        return ContaPagar(
            id_, fornecedor_id, descricao, Decimal(valor), date.fromisoformat(vencimento), condicao,
            EstadoContaPagar[estado], pagamentos,
        )


class RepositorioEmpresaSQLite(_Repositorio):
    def obter(self) -> Optional[Empresa]:
        linha = self._executar(f"SELECT {', '.join(CAMPOS_DA_EMPRESA)} FROM empresa WHERE id = 1").fetchone()
        return Empresa(*linha) if linha else None

    def salvar(self, empresa: Empresa) -> None:
        valores = [getattr(empresa, c) for c in CAMPOS_DA_EMPRESA]
        self._executar(
            f"INSERT OR REPLACE INTO empresa (id, {', '.join(CAMPOS_DA_EMPRESA)}) VALUES (1, ?, ?, ?, ?, ?, ?)", valores
        )


class RepositorioOrcamentosSQLite(_Repositorio):
    def obter(self, orcamento_id: str) -> Optional[Orcamento]:
        linha = self._executar("SELECT * FROM orcamentos WHERE id = ?", (orcamento_id,)).fetchone()
        return self._montar(linha, *self._filhos(orcamento_id)) if linha else None

    def listar(self) -> List[Orcamento]:
        linhas = self._executar("SELECT * FROM orcamentos ORDER BY criado_em DESC, id").fetchall()
        itens, decisoes = self._filhos(None)
        return [self._montar(l, itens.get(l["id"], []), decisoes.get(l["id"], [])) for l in linhas]

    def salvar(self, orcamento: Orcamento) -> None:
        pendencia = orcamento.pendencia
        self._executar(
            """INSERT INTO orcamentos (id, cliente_id, elaborado_por, criado_em, estado, condicao_pagamento,
                   percentual_desconto, pendente_percentual, pendente_solicitado_por, pendente_alcada, motivo_cancelamento)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
               ON CONFLICT (id) DO UPDATE SET estado = excluded.estado,
                   condicao_pagamento = excluded.condicao_pagamento,
                   percentual_desconto = excluded.percentual_desconto,
                   pendente_percentual = excluded.pendente_percentual,
                   pendente_solicitado_por = excluded.pendente_solicitado_por,
                   pendente_alcada = excluded.pendente_alcada,
                   motivo_cancelamento = excluded.motivo_cancelamento""",
            (
                orcamento.id,
                orcamento.cliente_id,
                orcamento.elaborado_por,
                orcamento.criado_em.isoformat(),
                orcamento.estado.name,
                orcamento.condicao_pagamento,
                str(orcamento.percentual_desconto),
                str(pendencia.percentual_solicitado) if pendencia else None,
                pendencia.solicitado_por if pendencia else None,
                str(pendencia.alcada) if pendencia else None,
                orcamento.motivo_cancelamento,
            ),
        )
        self._executar("DELETE FROM itens_orcamento WHERE orcamento_id = ?", (orcamento.id,))
        for ordem, item in enumerate(orcamento.itens):
            self._executar(
                """INSERT INTO itens_orcamento (id, orcamento_id, ordem, descricao, quantidade, valor_unitario)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (item.id, orcamento.id, ordem, item.descricao, str(item.quantidade), str(item.valor_unitario)),
            )
        # As decisões só se acrescentam: a já gravada não muda.
        for ordem, d in enumerate(orcamento.decisoes):
            self._executar(
                """INSERT OR IGNORE INTO decisoes_desconto (orcamento_id, ordem, aprovado, percentual_solicitado,
                       percentual_aprovado, decidido_por, data) VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (
                    orcamento.id,
                    ordem,
                    int(d.aprovado),
                    str(d.percentual_solicitado),
                    None if d.percentual_aprovado is None else str(d.percentual_aprovado),
                    d.decidido_por,
                    d.data.isoformat(),
                ),
            )

    def _filhos(self, orcamento_id: Optional[str]):
        onde, parametros = ("WHERE orcamento_id = ?", (orcamento_id,)) if orcamento_id else ("", ())
        itens, decisoes = {}, {}
        for l in self._executar(f"SELECT * FROM itens_orcamento {onde} ORDER BY orcamento_id, ordem", parametros):
            itens.setdefault(l["orcamento_id"], []).append(
                ItemOrcamento(l["id"], l["descricao"], Decimal(l["quantidade"]), Decimal(l["valor_unitario"]))
            )
        for l in self._executar(f"SELECT * FROM decisoes_desconto {onde} ORDER BY orcamento_id, ordem", parametros):
            decisoes.setdefault(l["orcamento_id"], []).append(
                AprovacaoDesconto(
                    aprovado=bool(l["aprovado"]),
                    percentual_solicitado=Decimal(l["percentual_solicitado"]),
                    percentual_aprovado=None if l["percentual_aprovado"] is None else Decimal(l["percentual_aprovado"]),
                    decidido_por=l["decidido_por"],
                    data=date.fromisoformat(l["data"]),
                )
            )
        if orcamento_id:
            return itens.get(orcamento_id, []), decisoes.get(orcamento_id, [])
        return itens, decisoes

    @staticmethod
    def _montar(linha, itens, decisoes) -> Orcamento:
        pendencia = None
        if linha["pendente_percentual"] is not None:
            pendencia = PendenciaDesconto(
                Decimal(linha["pendente_percentual"]), linha["pendente_solicitado_por"], Decimal(linha["pendente_alcada"])
            )
        return Orcamento(
            id=linha["id"],
            cliente_id=linha["cliente_id"],
            elaborado_por=linha["elaborado_por"],
            criado_em=date.fromisoformat(linha["criado_em"]),
            estado=EstadoOrcamento[linha["estado"]],
            condicao_pagamento=linha["condicao_pagamento"],
            percentual_desconto=Decimal(linha["percentual_desconto"]),
            itens=list(itens),
            pendencia=pendencia,
            decisoes=list(decisoes),
            motivo_cancelamento=linha["motivo_cancelamento"],
        )

    def _executar(self, comando: str, parametros=()):
        cursor = super()._executar(comando, parametros)
        cursor.row_factory = sqlite3.Row
        return cursor


class AuditoriaSQLite(_Repositorio):
    """Somente inclusão e leitura (ADR-004); o banco recusa alteração e exclusão (CA-13)."""

    _COLUNAS = "usuario_id, data_hora, operacao, registro_afetado, valor_anterior, valor_novo, motivo, campo, automatica, rotina"

    def registrar(self, registro: RegistroAuditoria) -> None:
        self._executar(
            f"INSERT INTO auditoria ({self._COLUNAS}) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
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

    def listar(self) -> List[RegistroAuditoria]:
        linhas = self._executar(f"SELECT {self._COLUNAS} FROM auditoria ORDER BY sequencia").fetchall()
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
    _COLUNAS = "id, nome, perfil, email, ativo"

    def obter(self, usuario_id: str) -> Optional[Usuario]:
        return self._um(f"SELECT {self._COLUNAS} FROM usuarios WHERE id = ?", usuario_id)

    def obter_por_email(self, email: str) -> Optional[Usuario]:
        return self._um(f"SELECT {self._COLUNAS} FROM usuarios WHERE email = ?", email)

    def salvar(self, usuario: Usuario) -> None:
        self._executar(
            """INSERT INTO usuarios (id, nome, perfil, email, ativo) VALUES (?, ?, ?, ?, ?)
               ON CONFLICT (id) DO UPDATE SET nome = excluded.nome, perfil = excluded.perfil,
                   email = excluded.email, ativo = excluded.ativo""",
            (usuario.id, usuario.nome, usuario.perfil.name, usuario.email, int(usuario.ativo)),
        )

    def listar(self) -> List[Usuario]:
        return [self._montar(l) for l in self._executar(f"SELECT {self._COLUNAS} FROM usuarios").fetchall()]

    def guardar_hash(self, usuario_id: str, hash_da_senha: str) -> None:
        self._executar("UPDATE usuarios SET hash_da_senha = ? WHERE id = ?", (hash_da_senha, usuario_id))

    def hash_de(self, usuario_id: str) -> Optional[str]:
        linha = self._executar("SELECT hash_da_senha FROM usuarios WHERE id = ?", (usuario_id,)).fetchone()
        return linha[0] if linha else None

    def _um(self, comando: str, chave: str) -> Optional[Usuario]:
        linha = self._executar(comando, (chave,)).fetchone()
        return self._montar(linha) if linha else None

    @staticmethod
    def _montar(linha) -> Usuario:
        return Usuario(id=linha[0], nome=linha[1], perfil=Perfil[linha[2]], email=linha[3], ativo=bool(linha[4]))


class RepositorioSessoesSQLite(_Repositorio):
    def obter(self, chave: str) -> Optional[Sessao]:
        linha = self._executar(
            "SELECT chave, usuario_id, aberta_em, expira_em, protecao FROM sessoes WHERE chave = ?", (chave,)
        ).fetchone()
        if linha is None:
            return None
        return Sessao(
            chave=linha[0],
            usuario_id=linha[1],
            aberta_em=datetime.fromisoformat(linha[2]),
            expira_em=datetime.fromisoformat(linha[3]),
            protecao=linha[4],
        )

    def salvar(self, sessao: Sessao) -> None:
        self._executar(
            "INSERT OR REPLACE INTO sessoes (chave, usuario_id, aberta_em, expira_em, protecao) VALUES (?, ?, ?, ?, ?)",
            (sessao.chave, sessao.usuario_id, sessao.aberta_em.isoformat(), sessao.expira_em.isoformat(), sessao.protecao),
        )

    def remover(self, chave: str) -> None:
        self._executar("DELETE FROM sessoes WHERE chave = ?", (chave,))

    def remover_do_usuario(self, usuario_id: str) -> None:
        self._executar("DELETE FROM sessoes WHERE usuario_id = ?", (usuario_id,))


class RepositorioPermissoesSQLite(_Repositorio):
    def obter(self) -> MatrizPermissoes:
        linhas = self._executar("SELECT operacao, perfil FROM permissoes").fetchall()
        return MatrizPermissoes(frozenset((Operacao[o], Perfil[p]) for o, p in linhas))

    def salvar(self, matriz: MatrizPermissoes) -> None:
        self._executar("DELETE FROM permissoes")
        self._uow.conexao().executemany(
            "INSERT INTO permissoes (operacao, perfil) VALUES (?, ?)",
            [(o.name, p.name) for o, p in matriz.concedidas],
        )
