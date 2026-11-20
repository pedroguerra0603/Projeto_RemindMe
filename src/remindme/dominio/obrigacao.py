"""Obrigação fiscal, trabalhista ou contratual e sua evidência (Spec 010, UC-09). Regras RB-07, RB-13, RB-16, RB-29.

Cada ocorrência é uma `Obrigacao`; as ocorrências geradas a partir do mesmo cadastro têm a mesma `serie`. O histórico
(RF-50) é a lista de `EventoObrigacao`, acrescentada por cada operação que muda a obrigação.
"""

import calendar
import unicodedata
from dataclasses import dataclass, field, replace
from datetime import date, datetime, timedelta
from enum import Enum
from typing import Dict, List, Optional, Tuple

from remindme.dominio.erros import OperacaoRecusada, recusar_campos
from remindme.dominio.usuario import Perfil, Usuario
from remindme.dominio.valores import recusar

TAMANHO_DO_NOME = 120
TAMANHO_DA_DESCRICAO = 200
TAMANHO_MAXIMO_DA_EVIDENCIA = 5 * 1024 * 1024  # OPEN-63

# RB-07 e RB-16, com os valores padrão de OPEN-66, até a Spec 014 torná-los configuráveis (INV-9).
ANTECEDENCIA_DO_AVISO_DIAS = 7
TOLERANCIA_DO_ESCALONAMENTO_DIAS = 0

PERFIS_RESPONSAVEIS = (Perfil.DONO, Perfil.OPERADOR_FINANCEIRO)  # OPEN-64

# OPEN-63: a extensão escolhe o tipo, e o conteúdo tem de começar pela assinatura desse tipo.
_TIPOS_DE_ARQUIVO: Dict[str, Tuple[str, bytes]] = {
    ".pdf": ("application/pdf", b"%PDF-"),
    ".png": ("image/png", b"\x89PNG\r\n\x1a\n"),
    ".jpg": ("image/jpeg", b"\xff\xd8\xff"),
    ".jpeg": ("image/jpeg", b"\xff\xd8\xff"),
}


class TipoObrigacao(Enum):
    """OPEN-66: lista fixa, para a Spec 014 configurar a antecedência por tipo (RB-07)."""

    FISCAL = "Fiscal"
    TRABALHISTA = "Trabalhista"
    CONTRATUAL = "Contratual"
    OUTRA = "Outra"


class Periodicidade(Enum):
    """OPEN-65."""

    UNICA = "Única"
    MENSAL = "Mensal"
    TRIMESTRAL = "Trimestral"
    SEMESTRAL = "Semestral"
    ANUAL = "Anual"

    @property
    def meses(self) -> int:
        return {"Única": 0, "Mensal": 1, "Trimestral": 3, "Semestral": 6, "Anual": 12}[self.value]


class EstadoObrigacao(Enum):
    PENDENTE = "Pendente"
    AGUARDANDO_EVIDENCIA = "Aguardando Evidência"
    ATRASADA = "Atrasada"
    CUMPRIDA = "Cumprida"


class TipoEvento(Enum):
    """O que entra no histórico da obrigação (RF-50). O valor é o texto mostrado."""

    CADASTRADA = "cadastrada"
    GERADA = "gerada a partir de outra ocorrência"
    PRAZO_ALTERADO = "prazo alterado"
    RESPONSAVEL_ALTERADO = "responsável alterado"
    AVISO_ENVIADO = "aviso enviado"
    AVISO_FALHOU = "aviso não entregue"
    ATRASADA = "atrasada"
    ESCALADA = "escalada ao Dono"
    ESCALONAMENTO_FALHOU = "escalonamento não entregue"
    CUMPRIMENTO_REGISTRADO = "cumprimento registrado"
    EVIDENCIA_ANEXADA = "evidência anexada"
    CUMPRIDA = "cumprida"


class TipoAlerta(Enum):
    AVISO = "aviso"
    ESCALONAMENTO = "escalonamento"


_EVENTOS_DO_ALERTA = {
    TipoAlerta.AVISO: (TipoEvento.AVISO_ENVIADO, TipoEvento.AVISO_FALHOU),
    TipoAlerta.ESCALONAMENTO: (TipoEvento.ESCALADA, TipoEvento.ESCALONAMENTO_FALHOU),
}


@dataclass(frozen=True)
class ArquivoDeEvidencia:
    """O arquivo como chegou: nome informado por quem enviou e o conteúdo."""

    nome: str
    conteudo: bytes


@dataclass(frozen=True)
class Evidencia:
    """Comprova o cumprimento (RB-29). O conteúdo fica à parte, no repositório, como o hash da senha."""

    id: str
    descricao: str
    nome_arquivo: str
    tipo_arquivo: str
    tamanho: int
    anexada_em: datetime
    usuario_id: str

    @classmethod
    def conferir(
        cls, id: str, arquivo: ArquivoDeEvidencia, descricao: object, anexada_em: datetime, usuario_id: str
    ) -> "Evidencia":
        """OPEN-63: PDF, PNG ou JPG de 1 byte a 5 MB, conferido pelo conteúdo; descrição obrigatória."""
        campos: Dict[str, str] = {}
        conteudo = arquivo.conteudo if isinstance(arquivo.conteudo, bytes) else b""
        nome = nome_base(arquivo.nome)
        tipo = _TIPOS_DE_ARQUIVO.get(_extensao(nome))
        if not conteudo:
            campos["arquivo"] = "O arquivo está vazio."
        elif len(conteudo) > TAMANHO_MAXIMO_DA_EVIDENCIA:
            campos["arquivo"] = "O arquivo tem no máximo 5 MB."
        elif tipo is None or not conteudo.startswith(tipo[1]):
            campos["arquivo"] = "Anexe um PDF, PNG ou JPG (OPEN-63)."
        texto = _texto(descricao)
        if not texto:
            campos["descricao"] = "Descreva a evidência."
        elif len(texto) > TAMANHO_DA_DESCRICAO:
            campos["descricao"] = f"A descrição tem no máximo {TAMANHO_DA_DESCRICAO} caracteres."
        recusar_campos(campos)
        return cls(id, texto, nome, tipo[0], len(conteudo), anexada_em, usuario_id)


@dataclass(frozen=True)
class EventoObrigacao:
    quando: datetime
    tipo: TipoEvento
    usuario_id: Optional[str]
    detalhe: str = ""
    destinatario_id: Optional[str] = None
    prazo: Optional[date] = None


def responsavel_valido(usuario: Optional[Usuario]) -> bool:
    """OPEN-64: usuário ativo, Dono ou Operador Financeiro."""
    return usuario is not None and usuario.ativo and usuario.perfil in PERFIS_RESPONSAVEIS


@dataclass
class Obrigacao:
    id: str
    nome: str
    tipo: TipoObrigacao
    periodicidade: Periodicidade
    prazo: date
    prazo_referencia: date
    dia_base: int
    responsavel_id: str
    exige_evidencia: bool
    serie: str
    estado: EstadoObrigacao
    cumprimento_em: Optional[date] = None
    cumprimento_por: Optional[str] = None
    proxima_id: Optional[str] = None
    evidencias: List[Evidencia] = field(default_factory=list)
    historico: List[EventoObrigacao] = field(default_factory=list)

    @classmethod
    def cadastrar(
        cls,
        id: str,
        nome: object,
        tipo: object,
        periodicidade: object,
        prazo: object,
        responsavel: Optional[Usuario],
        exige_evidencia: bool,
        hoje: date,
        usuario_id: str,
        quando: datetime,
    ) -> "Obrigacao":
        """RF-40. Todos os campos inválidos de uma vez (UC-09, E3; RNF-14). Prazo passado nasce Atrasada (A7)."""
        campos: Dict[str, str] = {}
        texto = _texto(nome)
        if not texto:
            campos["nome"] = "Informe o nome da obrigação."
        elif len(texto) > TAMANHO_DO_NOME:
            campos["nome"] = f"O nome tem no máximo {TAMANHO_DO_NOME} caracteres."
        tipo_valido = _enum(TipoObrigacao, tipo)
        if tipo_valido is None:
            campos["tipo"] = "Escolha o tipo: Fiscal, Trabalhista, Contratual ou Outra."
        periodicidade_valida = _enum(Periodicidade, periodicidade)
        if periodicidade_valida is None:
            campos["periodicidade"] = "Escolha a periodicidade: Única, Mensal, Trimestral, Semestral ou Anual."
        if not isinstance(prazo, date):
            campos["prazo"] = "Informe o prazo."
        if not responsavel_valido(responsavel):
            campos["responsavel"] = "Escolha um usuário ativo, Dono ou Operador Financeiro (OPEN-64)."
        recusar_campos(campos)
        obrigacao = cls(
            id=id,
            nome=texto,
            tipo=tipo_valido,
            periodicidade=periodicidade_valida,
            prazo=prazo,
            prazo_referencia=prazo,
            dia_base=prazo.day,
            responsavel_id=responsavel.id,
            exige_evidencia=bool(exige_evidencia),
            serie=id,
            estado=EstadoObrigacao.PENDENTE,
        )
        obrigacao._registrar(quando, TipoEvento.CADASTRADA, usuario_id)
        obrigacao.marcar_atrasada(hoje, quando)
        return obrigacao

    @property
    def aguarda_evidencia(self) -> bool:
        """RB-13: o cumprimento foi registrado, mas falta a evidência exigida."""
        return self.cumprimento_em is not None and self.estado is not EstadoObrigacao.CUMPRIDA

    def alterar_prazo(self, prazo: object, hoje: date, usuario_id: str, quando: datetime) -> date:
        """RF-41, A3: só em Pendente ou Aguardando Evidência, e nunca para antes de hoje. O prazo de referência e o
        dia-base não mudam: a alteração vale só para esta ocorrência (OPEN-65)."""
        if self.estado not in (EstadoObrigacao.PENDENTE, EstadoObrigacao.AGUARDANDO_EVIDENCIA):
            self._recusar_no_estado("alteração de prazo")
        if not isinstance(prazo, date):
            recusar("prazo", "Informe o prazo.")
        if prazo < hoje:
            recusar("prazo", "O novo prazo não pode ser anterior a hoje.")
        anterior = self.prazo
        self.prazo = prazo
        self._registrar(quando, TipoEvento.PRAZO_ALTERADO, usuario_id, f"{_data(anterior)} → {_data(prazo)}")
        return anterior

    def alterar_responsavel(self, responsavel: Optional[Usuario], usuario_id: str, quando: datetime) -> str:
        """RF-41, A3: em qualquer estado diferente de Cumprida."""
        if self.estado is EstadoObrigacao.CUMPRIDA:
            self._recusar_no_estado("alteração de responsável")
        if not responsavel_valido(responsavel):
            recusar("responsavel", "Escolha um usuário ativo, Dono ou Operador Financeiro (OPEN-64).")
        anterior = self.responsavel_id
        self.responsavel_id = responsavel.id
        self._registrar(quando, TipoEvento.RESPONSAVEL_ALTERADO, usuario_id, f"{anterior} → {responsavel.id}")
        return anterior

    def registrar_cumprimento(
        self,
        data: object,
        hoje: date,
        usuario_id: str,
        quando: datetime,
        evidencia: Optional[Evidencia] = None,
    ) -> None:
        """RF-45 a RF-47. Sem a evidência exigida, Pendente passa a Aguardando Evidência (A2) e Atrasada continua
        Atrasada (A4) até o anexo. Qualquer usuário autorizado registra (OPEN-64)."""
        if self.estado is EstadoObrigacao.CUMPRIDA:
            self._recusar_no_estado("cumprimento")
        if self.cumprimento_em is not None:
            raise OperacaoRecusada("O cumprimento já foi registrado; falta anexar a evidência.")
        if not isinstance(data, date):
            recusar("data", "Informe a data do cumprimento.")
        if data > hoje:
            recusar("data", "A data do cumprimento não pode ser posterior a hoje.")
        self.cumprimento_em = data
        self.cumprimento_por = usuario_id
        self._registrar(quando, TipoEvento.CUMPRIMENTO_REGISTRADO, usuario_id, _data(data))
        if evidencia is not None:
            self.anexar_evidencia(evidencia, quando)
            return
        self._avaliar_cumprimento(quando, usuario_id)

    def anexar_evidencia(self, evidencia: Evidencia, quando: datetime) -> None:
        """RF-46, RB-29: com o cumprimento já registrado, o anexo leva a Cumprida."""
        if self.estado is EstadoObrigacao.CUMPRIDA:
            self._recusar_no_estado("evidência")
        self.evidencias.append(evidencia)
        self._registrar(quando, TipoEvento.EVIDENCIA_ANEXADA, evidencia.usuario_id, evidencia.nome_arquivo)
        self._avaliar_cumprimento(quando, evidencia.usuario_id)

    def marcar_atrasada(self, hoje: date, quando: datetime) -> bool:
        """RF-48: Pendente ou Aguardando Evidência com prazo anterior a hoje passa a Atrasada. Idempotente."""
        if self.estado in (EstadoObrigacao.PENDENTE, EstadoObrigacao.AGUARDANDO_EVIDENCIA) and self.prazo < hoje:
            self.estado = EstadoObrigacao.ATRASADA
            self._registrar(quando, TipoEvento.ATRASADA, None, _data(self.prazo))
            return True
        return False

    def gerar_proxima_ocorrencia(self, novo_id: str, hoje: date, quando: datetime) -> Optional["Obrigacao"]:
        """RF-42, OPEN-65: a próxima nasce do prazo de referência, avançado pela periodicidade no dia-base, e não
        da data do cumprimento nem do prazo alterado. INV-4: cada ocorrência gera no máximo uma próxima."""
        if self.estado is not EstadoObrigacao.CUMPRIDA:
            raise OperacaoRecusada("Só obrigação Cumprida gera a próxima ocorrência (RF-42).")
        if self.proxima_id is not None:
            raise OperacaoRecusada("A próxima ocorrência desta obrigação já foi gerada (RF-42).")
        if self.periodicidade is Periodicidade.UNICA:
            return None
        prazo = avancar_meses(self.prazo_referencia, self.periodicidade.meses, self.dia_base)
        proxima = replace(
            self,
            id=novo_id,
            prazo=prazo,
            prazo_referencia=prazo,
            estado=EstadoObrigacao.PENDENTE,
            cumprimento_em=None,
            cumprimento_por=None,
            proxima_id=None,
            evidencias=[],
            historico=[EventoObrigacao(quando, TipoEvento.GERADA, None, self.id)],
        )
        proxima.marcar_atrasada(hoje, quando)
        self.proxima_id = novo_id
        return proxima

    def destinatarios_do_aviso(self, hoje: date, responsavel: Optional[Usuario], donos_ativos: List[str]) -> List[str]:
        """RF-44, RB-07: Pendente com prazo entre hoje e hoje + 7 dias avisa o responsável, uma vez por prazo e por
        destinatário. Responsável inativo: avisa os Donos ativos (A6, OPEN-64)."""
        if self.estado is not EstadoObrigacao.PENDENTE:
            return []
        if not hoje <= self.prazo <= hoje + timedelta(days=ANTECEDENCIA_DO_AVISO_DIAS):
            return []
        candidatos = [responsavel.id] if responsavel_valido(responsavel) else donos_ativos
        return self._ainda_sem(TipoAlerta.AVISO, candidatos)

    def destinatarios_do_escalonamento(self, hoje: date, donos_ativos: List[str]) -> List[str]:
        """RF-49, RB-16: Atrasada há pelo menos a tolerância escala a cada Dono ativo, uma vez por prazo."""
        if self.estado is not EstadoObrigacao.ATRASADA:
            return []
        if hoje < self.prazo + timedelta(days=1 + TOLERANCIA_DO_ESCALONAMENTO_DIAS):
            return []
        return self._ainda_sem(TipoAlerta.ESCALONAMENTO, donos_ativos)

    def registrar_alerta(self, tipo: TipoAlerta, destinatario_id: str, entregue: bool, quando: datetime) -> None:
        enviado, falhou = _EVENTOS_DO_ALERTA[tipo]
        self.historico.append(
            EventoObrigacao(quando, enviado if entregue else falhou, None, "", destinatario_id, self.prazo)
        )

    def _ainda_sem(self, tipo: TipoAlerta, candidatos: List[str]) -> List[str]:
        enviado = _EVENTOS_DO_ALERTA[tipo][0]
        ja_recebidos = {e.destinatario_id for e in self.historico if e.tipo is enviado and e.prazo == self.prazo}
        unicos = list(dict.fromkeys(candidatos))
        return [u for u in unicos if u not in ja_recebidos]

    def _avaliar_cumprimento(self, quando: datetime, usuario_id: Optional[str]) -> None:
        if self.cumprimento_em is None:
            return
        if self.exige_evidencia and not self.evidencias:
            if self.estado is EstadoObrigacao.PENDENTE:
                self.estado = EstadoObrigacao.AGUARDANDO_EVIDENCIA
            return
        self.estado = EstadoObrigacao.CUMPRIDA
        self._registrar(quando, TipoEvento.CUMPRIDA, usuario_id)

    def _recusar_no_estado(self, acao: str) -> None:
        raise OperacaoRecusada(f"Obrigação {self.estado.value} não aceita {acao}.")

    def _registrar(self, quando: datetime, tipo: TipoEvento, usuario_id: Optional[str], detalhe: str = "") -> None:
        self.historico.append(EventoObrigacao(quando, tipo, usuario_id, detalhe))


def avancar_meses(data: date, meses: int, dia_base: int) -> date:
    """OPEN-65: o mesmo dia-base, ou o último dia do mês quando ele não existe (31/01 → 28/02 → 31/03)."""
    total = data.year * 12 + (data.month - 1) + meses
    ano, mes = divmod(total, 12)
    mes += 1
    return date(ano, mes, min(dia_base, calendar.monthrange(ano, mes)[1]))


def nome_base(nome: object) -> str:
    """Foco de revisão 1: só o nome do arquivo, sem caminho, aspas, caracteres de controle nem de formatação
    (como U+202E, que inverte o texto mostrado). Nome longo é cortado no radical, preservando a extensão."""
    texto = nome if isinstance(nome, str) else ""
    texto = texto.replace("\\", "/").rsplit("/", 1)[-1]
    texto = "".join(c for c in texto if c != '"' and unicodedata.category(c) not in ("Cc", "Cf")).strip()
    extensao = _extensao(texto)
    if len(texto) > TAMANHO_DO_NOME:
        radical = texto[: len(texto) - len(extensao)]
        texto = radical[: TAMANHO_DO_NOME - len(extensao)] + extensao
    return texto


def _extensao(nome: str) -> str:
    return nome[nome.rfind("."):].lower() if "." in nome else ""


def _enum(classe, escolha):
    """Aceita o membro ou o seu texto, como chega do formulário."""
    if isinstance(escolha, classe):
        return escolha
    return next((membro for membro in classe if membro.value == escolha), None)


def _texto(texto: object) -> str:
    return " ".join(texto.split()) if isinstance(texto, str) else ""


def _data(data: date) -> str:
    return data.strftime("%d/%m/%Y")
